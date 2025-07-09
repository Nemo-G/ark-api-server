# ARK HTTP Proxy

## Overview

This project provides an HTTP proxy for the ARK gRPC inference server, enabling OpenAI-compatible API access to large language models (LLMs) served via a custom backend. The system is designed for high-performance, GPU-accelerated inference and is orchestrated using Docker Compose.


### Quickstart: API Server Only

To quickly start just the API server (useful for development or debugging):

```sh
docker compose up api-server
```

This will build and run only the API server container. Make sure any required backend services (prefiller/decoder) are running and accessible as configured.

## Architecture

The system consists of three main services:

### 1. Prefiller
- **Role:** Handles the prefill (prompt encoding and caching) stage of LLM inference.
- **Image:** `iaas-gpu-cn-beijing.cr.volces.com/serving/xllm:private_xllm_th24_cu124_xperf_0609`
- **Entrypoint:** `prefiller-setup` script
- **Key Features:**
  - Loads DeepSeek-R1-ENC-xLLM and DeepSeek-R1-DRAFT-ENC-xLLM models
  - Configures GPU and environment
  - Runs `private_xllm.bin` in `splitwise_prefill` mode
  - Exposes port 62000 for gRPC
  - Healthcheck ensures the binary is running and port is open

### 2. Decoder
- **Role:** Handles the decode (token generation) stage of LLM inference, connecting to the prefiller for cached context.
- **Image:** `iaas-gpu-cn-beijing.cr.volces.com/serving/xllm:private_xllm_th24_cu124_xperf_0609`
- **Entrypoint:** `decoder-setup` script
- **Key Features:**
  - Loads the same models as prefiller
  - Configures GPU and environment
  - Runs `private_xllm.bin` in `splitwise_decode` mode
  - Connects to the prefiller via `PREFILL_NODE_IP`
  - Exposes port 62000 for gRPC
  - Healthcheck ensures the binary is running and HTTP is responsive
  - Starts the API server after decoder is healthy

### 3. API Server
- **Role:** Exposes an OpenAI-compatible HTTP API for chat completions and model listing, forwarding requests to the backend via gRPC.
- **Image:** Built from this repo (Python/FastAPI/Uvicorn)
- **Entrypoint:** `start.sh` (runs `uvicorn openai_api_server:app`)
- **Key Features:**
  - `/v1/models`: Lists available models
  - `/v1/chat/completions`: Handles chat completion requests (streaming and non-streaming)
  - Forwards requests to the decoder via gRPC using protobufs defined in `proto/ark.proto`
  - Compatible with OpenAI API clients

## Protocols and Data Flow

- **gRPC Protocol:** Defined in `proto/ark.proto`, with Python bindings in `proto/ark_pb2.py` and `proto/ark_pb2_grpc.py`.
- **HTTP Protocol:** OpenAI-compatible endpoints implemented in `openai_api_server.py`.
- **Request Flow:**
  1. Client sends HTTP request to API server
  2. API server converts request to gRPC and forwards to decoder
  3. Decoder may interact with prefiller for context caching
  4. Response is streamed or returned to client

## Setup and Running

### Prerequisites
- Docker and Docker Compose
- NVIDIA GPUs and drivers (for model serving)
- Python 3.10+ (for local development)

### Dependencies
Main Python dependencies (see `pyproject.toml`):
- fastapi
- uvicorn[standard]
- grpcio, grpcio-tools
- sse-starlette
- pydantic, pydantic-settings
- openai
- typing-extensions

### Running with Docker Compose

```sh
docker-compose up --build
```

This will start all three services. The API server will be available at `http://localhost:18080`.

### Environment Variables
- `HTTP_FORWARD_GRPC_HOST`: Host for gRPC backend (default: 0.0.0.0)
- `HTTP_FORWARD_GRPC_PORT`: Port for gRPC backend (default: 62000)
- `PREFILL_NODE_IP`: IP address of the prefiller node (used by decoder)

### Volumes and Model Files
- Mount your model directories and license files as shown in `docker-compose.yaml`.

## Usage

- **List Models:**
  ```sh
  curl http://localhost:18080/v1/models
  ```
- **Chat Completion:**
  ```sh
  curl http://localhost:18080/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -d '{"model": "deepseek-r1-0528", "messages": [{"role": "user", "content": "Hello!"}]}'
  ```

## Development

- Main API logic: `openai_api_server.py`
- Protocols: `proto/ark.proto`, `openai_protocol.py`
- RPC helpers: `rpc_method.py`
- Service setup: `prefiller-setup`, `decoder-setup`, `start.sh`

## Protobufs
- See `proto/ark.proto` for message and service definitions.
- Regenerate Python bindings with:
  ```sh
  python -m grpc_tools.protoc -I./proto --python_out=./proto --grpc_python_out=./proto ./proto/ark.proto
  ```

## License
- License file must be mounted as `/root/license.lic` in containers.
- See your organization's license terms for model and binary usage.

## References
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference/introduction)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [gRPC Python](https://grpc.io/docs/languages/python/) 