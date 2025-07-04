#!/bin/bash

export http_forward_grpc_host=0.0.0.0
export http_forward_grpc_port=62000
uvicorn openai_api_server:app \
--host 0.0.0.0 \
--port 80 \
--workers 8
