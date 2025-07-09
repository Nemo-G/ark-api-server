#!/bin/bash

# Function to log messages with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_message "Starting decoder setup..."

# Change to project directory
project_dir=/app/xllm
cd $project_dir

# Set up Python and library paths
export PYTHONPATH=$project_dir:$PYTHONPATH
export LD_LIBRARY_PATH=$project_dir:$LD_LIBRARY_PATH

# GPU configuration
NUM_GPU=`nvidia-smi -L | wc -l`
export XLLM_MODEL_MP_SIZE=$NUM_GPU
export XLLM_PARALLEL_LOCAL_WORLD_SIZE=$NUM_GPU

log_message "Detected $NUM_GPU GPUs"

# Model configuration
export XLLM_MODEL_NAME=deepseek-r1
export XLLM_MODEL_VERSION=250120

# Model directories
DEEPSEEK_MODEL_DIR=/data/models/DeepSeek-R1-ENC-xLLM
DEEPSEEK_DRAFT_MODEL_DIR=/data/models/DeepSeek-R1-DRAFT-ENC-xLLM
export XPERF_TUNER_CONFIG_LOAD_PATH=$DEEPSEEK_MODEL_DIR/saved_model/gemm_config
export XLLM_DRAFT_MODEL_MODEL_DIR=$DEEPSEEK_DRAFT_MODEL_DIR

# Network configuration
LOCAL_ADDR=$(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
log_message "Local address: $LOCAL_ADDR"

# Splitwise configuration
export SPLITWISE_PREFILL_ROUTING_CONFIG__ROUTING_STRATEGY="p2c"
export SPLITWISE_PREFILL_ROUTING_CONFIG__PICK_N=3
export SPLITWISE_DRIVER_PORT=62001
export SPLITWISE_KV_CACHE_RECEIVER_PORT=62002
export SPLITWISE_PREFILL_LENGTH_THRESHOLD=0
export SPLITWISE_KV_TRANSFER_BACKEND=veturborpc
export SPLITWISE_PREFILL_ROUTING_CONFIG__ROUTING_TABLE_UPDATER_CONFIG__TYPE="env_based"
export SPLITWISE_PREFILL_ROUTING_CONFIG__ROUTING_TABLE_UPDATER_CONFIG__ADDRS_VAR_NAME="PREFILL_ADDRS"

# Prefill configuration - use environment variable if set, otherwise use default
prefill_ip=${PREFILL_NODE_IP:-"10.0.0.174"}
export PREFILL_ADDRS="${prefill_ip}:62001"
export SPLITWISE_DECODE_ADDR=${LOCAL_ADDR}
export SPLITWISE_KV_CACHE_RECEIVER_ADDR=${LOCAL_ADDR}
export VETURBORPC_LOCAL_ADDR=${LOCAL_ADDR}

log_message "Prefill addresses: $PREFILL_ADDRS"

# Processor configuration
export XLLM_PROCESSOR_REASONING_END_TOKEN="</think>"
export XLLM_PROCESSOR_REASONING_PREFILL_TEMPLATE=$'<think>\n'
export XLLM_PROCESSOR_TOOL_PARSER=deepseek_r1

# Environment file path
XLLM_ENV_PATH=/app/xllm/decode_enc.env

log_message "Starting decoder service..."

# Start the decoder service
./private_xllm.bin \
        --model-dir $DEEPSEEK_MODEL_DIR \
        --env-path $XLLM_ENV_PATH \
        --driver-type splitwise_decode \
        --num-server-procs 4 \
        --port 62000

DECODER_PID=$!
log_message "Decoder service started with PID: $DECODER_PID"



