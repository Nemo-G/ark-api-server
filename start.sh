#!/bin/bash

export http_forward_grpc_host=${HTTP_FORWARD_GRPC_HOST:-0.0.0.0}
export http_forward_grpc_port=${HTTP_FORWARD_GRPC_PORT:-62000}
uvicorn openai_api_server:app \
--host 0.0.0.0 \
--port 80 \
--workers 8
