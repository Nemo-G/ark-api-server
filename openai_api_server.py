import base64
import collections
import json
import random
import time
import uuid
from typing import AsyncGenerator

import grpc
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse

try:
    from pydantic import BaseSettings
except ImportError:
    from pydantic_settings import BaseSettings

from rpc_method import decode_value, encode_value

from proto import ark_pb2, ark_pb2_grpc
from openai_protocol import ChatCompletionRequest


class XLLMServerSettings(BaseSettings):
    grpc_host: str = "0.0.0.0"
    grpc_port: str = "50050"
    # eg. export http_forward_grpc_host_list=0.0.0.1,0.0.0.2,0.0.0.3
    grpc_host_list: str = ""
    sse_data_prefix: bool = False

    compat_llmserver_vlm_v1: bool = False

    class Config:
        env_prefix = "http_forward_"


def lookup_service(service_settings: XLLMServerSettings):
    if service_settings.grpc_host_list:
        hosts = service_settings.grpc_host_list.split(",")
        return f"{hosts[random.randint(0, len(hosts) - 1)]}:{service_settings.grpc_port}"
    return f"{service_settings.grpc_host}:{service_settings.grpc_port}"


settings = XLLMServerSettings()
app = FastAPI()


def make_ark_req(args: ChatCompletionRequest) -> ark_pb2.InferenceRequest:
    request = ark_pb2.InferenceRequest()

    if args.messages is not None:
        for msg in args.messages:
            content = msg["content"]
            if isinstance(content, str):
                request.inputs["messages.role"].bytes_list.values.extend([msg["role"].encode()])
                request.inputs["messages.content"].bytes_list.values.extend([content.encode()])
            elif isinstance(content, collections.abc.Iterable):
                if settings.compat_llmserver_vlm_v1:
                    struct = ark_pb2.Struct()
                    struct.fields["role"].string_ = msg["role"]
                    for entry in msg["content"]:
                        if entry["type"] == "text":
                            struct.fields["content"].string_ = entry["text"]
                        elif entry["type"] == "image_url":
                            b64_image = entry["image_url"]["url"].split(",")[-1]
                            struct.fields["image"].bytes_list.values.extend([base64.b64decode(b64_image)])
                        else:
                            raise ValueError(f"type {entry['type']} is not supported in content")
                    request.inputs["messages"].value_list.values.append(ark_pb2.Value(struct_=struct))
                else:
                    request.inputs["messages.role"].bytes_list.values.extend([msg["role"].encode()])
                    payloads = []
                    for entry in msg["content"]:
                        if entry["type"] == "text":
                            text = ark_pb2.Struct()
                            text.fields["type"].string_ = "text"
                            text.fields["text"].string_ = entry["text"]
                            payloads.append(text)
                        elif entry["type"] == "image_url":
                            image = ark_pb2.Struct()
                            image.fields["type"].string_ = "image_url"
                            image.fields["image_url"].struct_.fields["url"].string_ = entry["image_url"]["url"]
                            image.fields["image_url"].struct_.fields["detail"].string_ = entry["image_url"].get(
                                "detail", "high"
                            )
                            payloads.append(image)
                        else:
                            raise ValueError(f"type {entry['type']} is not supported in content")

                        struct = ark_pb2.Struct()
                        struct.fields["role"].string_ = msg["role"]
                        struct.fields["content"].value_list.values.extend(
                            [ark_pb2.Value(struct_=payload) for payload in payloads]
                        )
                        request.inputs["messages"].value_list.values.append(ark_pb2.Value(struct_=struct))
            else:
                raise Exception("Unknown message.content type")

    request.req_id = str(uuid.uuid4())
    request.model_name = args.model

    if args.stop is not None:
        request.inputs["stop"].MergeFrom(encode_value(args.stop))
    if args.max_tokens is not None:
        request.inputs["max_new_tokens"].int64_ = args.max_tokens
    if args.n is not None:
        request.inputs["n"].int64_ = args.n
    if args.temperature is not None:
        request.inputs["temperature"].float_ = args.temperature
    if args.top_p is not None:
        request.inputs["top_p"].float_ = args.top_p
    if args.presence_penalty is not None:
        request.inputs["presence_penalty"].float_ = args.presence_penalty
    if args.frequency_penalty is not None:
        request.inputs["frequency_penalty"].float_ = args.frequency_penalty
    if args.logprobs == True:
        request.inputs["logprobs"].int64_ = args.top_logprobs if args.top_logprobs is not None else 1
    if args.logit_bias is not None:
        for key, value in args.logit_bias.items():
            request.inputs["logit_bias"].int64_dict.fields[int(key)].int64_ = value
    if args.response_format is not None:
        request.inputs["response_format"].MergeFrom(encode_value(args.response_format.dict(by_alias=True)))
    if args.guided_grammar is not None:
        request.inputs["guided_grammar"].string_ = args.guided_grammar

    if args.tools is not None:
        request.inputs["tools"].MergeFrom(encode_value([tool.dict(by_alias=True) for tool in args.tools]))

    return request


@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest):
    requestData = make_ark_req(request)
    response_role = "assistant"
    chunk_id = "chatcmpl-" + str(time.time_ns())  # Unique identifier for the chat completion
    timestamp = int(time.time())  # Current Unix timestamp in seconds
    model_name = request.model
    system_fp = "fp"  # System fingerprint, should be generated or retrieved from a config
    usage_flag = False

    service = lookup_service(settings)
    url = "{}/generate".format(service)

    if request.stream and request.stream_options is not None and request.stream_options.include_usage == True:
        usage_flag = True

    # Streaming case
    if request.stream:
        try:
            object_type = "chat.completion.chunk"

            async def StreamResults() -> AsyncGenerator[bytes, None]:
                async with grpc.aio.insecure_channel(url) as channel:
                    ultraman_chat_stub = ark_pb2_grpc.InferenceStub(channel)
                    response_iterator = ultraman_chat_stub.StreamingCall(requestData)
                    try:
                        async for response in response_iterator:
                            # Extract the data from the response
                            choice = decode_value(response.outputs["choice"])
                            # generated_text = response.outputs["choice.message.content"].bytes_.decode()
                            if response.outputs.get("usage") is not None:
                                usage = response.outputs.get("usage")
                                output_len = usage.struct_.fields["completion_tokens"].int64_
                                prompt_len = usage.struct_.fields["prompt_tokens"].int64_
                                reasoning_tokens_len = (
                                    usage.struct_.fields["completion_tokens_details"]
                                    .struct_.fields["reasoning_tokens"]
                                    .int64_
                                )
                            converted_response = {
                                "id": chunk_id,
                                "choices": [
                                    {
                                        "index": response.outputs["choice.index"].int64_,
                                        "delta": {
                                            "role": response_role,
                                            "content": choice["message"]["content"],
                                            "reasoning_content": choice["message"].get("reasoning_content", ""),
                                            "tool_calls": choice["message"].get("tool_calls", []),
                                        },
                                        "finish_reason": response.outputs["choice.finish_reason"].bytes_.decode(),
                                    }
                                ],
                                "created": timestamp,
                                "model": model_name,
                                "system_fingerprint": system_fp,
                                "object": object_type,
                                "usage": (
                                    {
                                        "prompt_tokens": prompt_len,
                                        "completion_tokens": output_len,
                                        "total_tokens": output_len + prompt_len,
                                        "completion_tokens_details": {
                                            "reasoning_tokens": reasoning_tokens_len,
                                        },
                                    }
                                    if not usage_flag or response.outputs["choice.finish_reason"].bytes_.decode() != ""
                                    else None
                                ),  # This would be populated with usage info on the last chunk if applicable
                            }
                            if settings.sse_data_prefix:
                                yield dict(data=json.dumps(converted_response, ensure_ascii=False))
                            else:
                                yield b"data: " + json.dumps(converted_response, ensure_ascii=False).encode() + b"\n\n"
                        
                        # Send the final [DONE] message
                        if settings.sse_data_prefix:
                            yield dict(data="[DONE]")
                        else:
                            yield b"data: [DONE]\n\n"
                            
                    except grpc.aio.AioRpcError as e:
                        print(f"Error: {e}")
                        if settings.sse_data_prefix:
                            yield dict(data=json.dumps({"status": e.code().value, "error": str(e)}))
                        else:
                            yield b"data: " + json.dumps({"status": e.code().value, "error": str(e)}).encode() + b"\n\n"

            if settings.sse_data_prefix:
                return EventSourceResponse(StreamResults())
            else:
                return StreamingResponse(StreamResults(), media_type="text/event-stream")
        except Exception as e:
            print(f"Error: {e}")
            return JSONResponse(status_code=500, content={"error": {"code": 500, "message": str(e)}})
    # Non-streaming case
    else:
        try:
            object_type = "chat.completion"
            async with grpc.aio.insecure_channel(url) as channel:
                ultraman_chat_stub = ark_pb2_grpc.InferenceStub(channel)
                response_iterator = ultraman_chat_stub.StreamingCall(requestData)
                index_choices = {}
                async for response in response_iterator:
                    # Extract the data from the response
                    choice = decode_value(response.outputs["choice"])
                    index = response.outputs["choice.index"].int64_
                    if index not in index_choices:
                        index_choices[index] = {
                            "role": response_role,
                            "content": choice["message"]["content"],
                            "reasoning_content": choice["message"].get("reasoning_content", ""),
                            "tool_calls": choice["message"].get("tool_calls", []),
                        }
                    else:
                        index_choices[index]["content"] += choice["message"]["content"]
                        index_choices[index]["reasoning_content"] += choice["message"].get("reasoning_content", "")
                        index_choices[index]["tool_calls"].extend(choice["message"].get("tool_calls", []))
                    index_choices[index]["finish_reason"] = response.outputs["choice.finish_reason"].bytes_.decode()

                    if response.outputs.get("usage") is not None:
                        usage = response.outputs.get("usage")
                        output_len = usage.struct_.fields["completion_tokens"].int64_
                        prompt_len = usage.struct_.fields["prompt_tokens"].int64_
                        reasoning_tokens_len = (
                            usage.struct_.fields["completion_tokens_details"].struct_.fields["reasoning_tokens"].int64_
                        )
                        if index_choices[index].get("usage") is None:
                            index_choices[index]["usage"] = {
                                "prompt_tokens": prompt_len,
                            }

                        index_choices[index]["usage"]["completion_tokens"] = output_len
                        index_choices[index]["usage"]["total_tokens"] = output_len + prompt_len
                        index_choices[index]["usage"]["completion_tokens_details"] = {
                            "reasoning_tokens": reasoning_tokens_len,
                        }
                converted_response = {
                    "id": chunk_id,
                    "object": object_type,
                    "created": timestamp,
                    "model": model_name,
                    "system_fingerprint": system_fp,
                    "choices": [
                        {
                            "index": index,
                            "message": {
                                "role": response_role,
                                "content": choice["content"],
                                "reasoning_content": choice["reasoning_content"],
                                "tool_calls": choice["tool_calls"],
                            },
                            "finish_reason": choice["finish_reason"],
                        }
                        for index, choice in index_choices.items()
                    ],
                    "usage": {
                        "completion_len": sum(
                            [choice["usage"]["completion_tokens"] for choice in index_choices.values()]
                        ),
                        "prompt_len": index_choices[0]["usage"]["prompt_tokens"],
                        "total_len": index_choices[0]["usage"]["prompt_tokens"]
                        + sum([choice["usage"]["completion_tokens"] for choice in index_choices.values()]),
                        "completion_tokens_details": {
                            "reasoning_tokens": sum(
                                [
                                    choice["usage"]["completion_tokens_details"]["reasoning_tokens"]
                                    for choice in index_choices.values()
                                ]
                            )
                        },
                    },
                }
            return JSONResponse(converted_response)
        except Exception as e:
            print(f"Error: {e}")
            return JSONResponse(status_code=500, content={"error": {"code": 500, "message": str(e)}})
