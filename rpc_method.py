import json
from typing import Any, Dict, List, Union
from abc import ABC, abstractmethod
from typing_extensions import TypeAlias, TypeGuard

from proto import ark_pb2
from proto.ark_pb2 import InferenceRequest, InferenceResponse

from abc import ABC, abstractmethod
from google.protobuf import message



UnboxedValue: TypeAlias = Union[
    None,
    int,
    float,
    bytes,
    str,
    bool,
    List["UnboxedValue"],
    Dict[str, "UnboxedValue"],
    Dict[int, "UnboxedValue"],
]

class Method(ABC):
    """
    Class for pack and unpack proto messages
    """

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @classmethod
    @abstractmethod
    def pack_request_to_proto(cls, **kwargs: Any) -> message.Message:
        ...

    @classmethod
    @abstractmethod
    def unpack_request_from_proto(cls, proto_request: message.Message) -> Any:
        ...

    @classmethod
    @abstractmethod
    def pack_response_to_proto(cls, **kwargs: Any) -> message.Message:
        ...

    @classmethod
    @abstractmethod
    def unpack_response_from_proto(cls, proto_response: message.Message) -> Any:
        ...

def _is_struct_(value: Union[Dict[str, UnboxedValue], Dict[int, UnboxedValue]]) -> TypeGuard[Dict[str, UnboxedValue]]:
    return type(next(iter(value))) == str


def _is_int64_dict(
    value: Union[Dict[str, UnboxedValue], Dict[int, UnboxedValue]],
) -> TypeGuard[Dict[int, UnboxedValue]]:
    return type(next(iter(value))) == int


def _is_int64_list(value: List[UnboxedValue]) -> TypeGuard[List[int]]:
    return type(value[0]) == int


def _is_float_list(value: List[UnboxedValue]) -> TypeGuard[List[float]]:
    return type(value[0]) == float


def _is_bytes_list(value: List[UnboxedValue]) -> TypeGuard[List[bytes]]:
    return type(value[0]) == bytes


def _is_string_list(value: List[UnboxedValue]) -> TypeGuard[List[str]]:
    return type(value[0]) == str


def decode_value(value: ark_pb2.Value) -> UnboxedValue:
    kind = value.WhichOneof("kind")
    if kind is None:
        return None
    if kind == "int64_":
        return value.int64_
    if kind == "float_":
        return value.float_
    if kind == "bytes_":
        return value.bytes_
    if kind == "string_":
        return value.string_
    if kind == "bool_":
        return value.bool_
    if kind == "int64_list":
        return [v for v in value.int64_list.values]
    if kind == "float_list":
        return [v for v in value.float_list.values]
    if kind == "bytes_list":
        return [v for v in value.bytes_list.values]
    if kind == "string_list":
        return [v for v in value.string_list.values]
    if kind == "value_list":
        return [decode_value(v) for v in value.value_list.values]
    if kind == "struct_":
        return {k: decode_value(v) for k, v in value.struct_.fields.items()}
    if kind == "int64_dict":
        return {k: decode_value(v) for k, v in value.int64_dict.fields.items()}
    else:
        raise TypeError(f"Invalid kind: {kind}")


def encode_value(value: UnboxedValue) -> ark_pb2.Value:
    if value is None:
        return ark_pb2.Value()
    elif isinstance(value, int):
        return ark_pb2.Value(int64_=value)
    elif isinstance(value, float):
        return ark_pb2.Value(float_=value)
    elif isinstance(value, bytes):
        return ark_pb2.Value(bytes_=value)
    elif isinstance(value, str):
        return ark_pb2.Value(string_=value)
    elif isinstance(value, bool):
        return ark_pb2.Value(bool_=value)
    elif isinstance(value, dict):
        if not value:
            return ark_pb2.Value(struct_=ark_pb2.Struct(fields={}))
        if _is_struct_(value):
            return ark_pb2.Value(struct_=ark_pb2.Struct(fields={k: encode_value(v) for k, v in value.items()}))
        elif _is_int64_dict(value):
            return ark_pb2.Value(int64_dict=ark_pb2.Int64Dict(fields={k: encode_value(v) for k, v in value.items()}))
    if isinstance(value, list):
        if not value:
            return ark_pb2.Value(value_list=ark_pb2.ValueList(values=[]))
        if _is_int64_list(value):
            return ark_pb2.Value(int64_list=ark_pb2.Int64List(values=value))
        elif _is_float_list(value):
            return ark_pb2.Value(float_list=ark_pb2.FloatList(values=value))
        elif _is_bytes_list(value):
            return ark_pb2.Value(bytes_list=ark_pb2.BytesList(values=value))
        elif _is_string_list(value):
            return ark_pb2.Value(string_list=ark_pb2.StringList(values=value))
        else:
            return ark_pb2.Value(value_list=ark_pb2.ValueList(values=[encode_value(v) for v in value]))
    else:
        raise TypeError(f"Invalid type: {type(value)}")


class StreamingCallMethod:
    @property
    def name(self):
        return "StreamingCall"

    @classmethod
    def pack_request_to_proto(cls, **kwargs: Any) -> InferenceRequest:
        req_id = kwargs.pop("req_id")
        model_name = kwargs.pop("model_name")
        inputs = kwargs.pop("inputs")
        method = kwargs.pop("method", "")
        if kwargs:
            raise ValueError(f"Unexpected kwargs: {kwargs}")

        if "messages" in inputs:  # for compatibility
            messages_dot_role, messages_dot_content, messages_dot_name = list(), list(), list()
            for msg in inputs["messages"]:
                messages_dot_role.append(msg["role"].encode())
                messages_dot_content.append(msg["content"].encode())
                if "name" in msg:
                    messages_dot_name.append(msg["name"].encode())

            inputs["messages.role"] = messages_dot_role
            inputs["messages.content"] = messages_dot_content
            if len(messages_dot_name) > 0:
                assert len(messages_dot_name) == len(messages_dot_content)
                inputs["messages.name"] = messages_dot_name

        inf_req = InferenceRequest(
            req_id=req_id,
            model_name=model_name,
            method=method,
            inputs={k: encode_value(v) for k, v in inputs.items()},
        )

        return inf_req

    @classmethod
    def unpack_request_from_proto(cls, proto_request: InferenceRequest) -> Any:  # type: ignore
        inputs = proto_request.inputs
        req = {k: decode_value(v) for k, v in inputs.items()}
        if proto_request.model_name:
            req["model_name"] = proto_request.model_name

        if "messages.role" in inputs and "messages" not in inputs:  # for compatibility
            messages = []
            messages_dot_role = inputs["messages.role"].bytes_list.values
            messages_dot_content = inputs["messages.content"].bytes_list.values
            for role, content in zip(messages_dot_role, messages_dot_content):
                messages.append({"role": role.decode(), "content": content.decode()})
            if "messages.name" in inputs:
                messages_dot_name = inputs["messages.name"].bytes_list.values
                assert len(messages_dot_name) == len(messages_dot_content)
                for i, name in enumerate(messages_dot_name):
                    messages[i]["name"] = name.decode()
            if "messages.image" in inputs:
                messages_dot_image = inputs["messages.image"].bytes_list.values
                assert len(messages_dot_image) == len(messages_dot_content)
                for i, image in enumerate(messages_dot_image):
                    messages[i]["image"] = image  # type: ignore
            req["messages"] = messages  # type: ignore

        req["_req_id"] = proto_request.req_id
        # req_id equals to inhouse log_id
        # double assignment for easy reference
        req["_log_id"] = proto_request.req_id
        return proto_request.req_id, proto_request.model_name, proto_request.method, req

    @classmethod
    def pack_response_to_proto(cls, **kwargs: Any) -> InferenceResponse:
        req_id = kwargs.pop("req_id")
        model_name = kwargs.pop("model_name")
        outputs = kwargs.pop("outputs")
        if kwargs:
            raise ValueError(f"Unexpected kwargs: {kwargs}")

        if "choice" in outputs:  # for compatibility
            choice = outputs["choice"]
            if "message" in choice:
                outputs["choice.message.role"] = choice["message"]["role"].encode()
                outputs["choice.message.content"] = choice["message"]["content"].encode()
            if "index" in choice:
                outputs["choice.index"] = choice["index"]
            if "finish_reason" in choice:
                if choice["finish_reason"]:
                    outputs["choice.finish_reason"] = choice["finish_reason"].encode()
                else:
                    # pop None
                    choice.pop("finish_reason")

        if "usage" in outputs:  # for compatibility
            usage = outputs["usage"]
            if "prompt_tokens" in usage:
                outputs["usage.prompt_tokens"] = usage["prompt_tokens"]
            if "completion_tokens" in usage:
                outputs["usage.completion_tokens"] = usage["completion_tokens"]
            if "total_tokens" in usage:
                outputs["usage.total_tokens"] = usage["total_tokens"]

        if "cache" in outputs:
            cache = outputs["cache"]
            if (hit_tokens := cache.get("prompt_cache_hit_tokens")) is not None:
                outputs["cache.prompt_cache_hit_tokens"] = hit_tokens
            if (miss_tokens := cache.get("prompt_cache_miss_tokens")) is not None:
                outputs["cache.prompt_cache_miss_tokens"] = miss_tokens
            if (append_tokens := cache.get("prompt_cache_append_tokens")) is not None:
                outputs["cache.prompt_cache_append_tokens"] = append_tokens
            if (initial_tokens := cache.get("prompt_cache_initial_tokens")) is not None:
                outputs["cache.prompt_cache_initial_tokens"] = initial_tokens

        inf_resp = InferenceResponse(
            req_id=req_id,
            model_name=model_name,
            outputs={k: encode_value(v) for k, v in outputs.items()},
        )
        return inf_resp

    @classmethod
    def unpack_response_from_proto(cls, proto_response: InferenceResponse) -> Any:  # type: ignore
        resp = {k: decode_value(v) for k, v in proto_response.outputs.items()}

        return proto_response.req_id, proto_response.model_name, resp


class CallMethod(Method):
    @property
    def name(self):
        return "Call"

    @classmethod
    def pack_request_to_proto(cls, **kwargs: Any) -> InferenceRequest:
        req_id = kwargs.pop("req_id")
        model_name = kwargs.pop("model_name")
        inputs = kwargs.pop("inputs")
        method = kwargs.pop("method", "")
        if kwargs:
            raise ValueError(f"Unexpected kwargs: {kwargs}")

        inf_req = InferenceRequest(
            req_id=req_id,
            model_name=model_name,
            method=method,
            inputs={k: encode_value(v) for k, v in inputs.items()},
        )

        return inf_req

    @classmethod
    def unpack_request_from_proto(cls, proto_request: InferenceRequest) -> Any:  # type: ignore
        inputs = proto_request.inputs
        req = {k: decode_value(v) for k, v in inputs.items()}
        if proto_request.model_name:
            req["model_name"] = proto_request.model_name

        req["_req_id"] = proto_request.req_id
        req["_log_id"] = proto_request.req_id
        return proto_request.req_id, proto_request.model_name, proto_request.method, req

    @classmethod
    def pack_response_to_proto(cls, **kwargs: Any) -> InferenceResponse:
        req_id = kwargs.pop("req_id")
        model_name = kwargs.pop("model_name")
        outputs = kwargs.pop("outputs")
        if kwargs:
            raise ValueError(f"Unexpected kwargs: {kwargs}")

        if "usage" in outputs:  # for compatibility
            usage = outputs["usage"]
            if "prompt_tokens" in usage:
                outputs["usage.prompt_tokens"] = usage["prompt_tokens"]
            if "total_tokens" in usage:
                outputs["usage.total_tokens"] = usage["total_tokens"]

        inf_resp = InferenceResponse(
            req_id=req_id,
            model_name=model_name,
            outputs={k: encode_value(v) for k, v in outputs.items()},
        )
        return inf_resp

    @classmethod
    def unpack_response_from_proto(cls, proto_response: InferenceResponse) -> Any:  # type: ignore
        resp = {k: decode_value(v) for k, v in proto_response.outputs.items()}
        return proto_response.req_id, proto_response.model_name, resp
