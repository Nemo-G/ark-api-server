#!/bin/bash

# Set working directory
project_dir=/app/xllm
cd $project_dir

# Set Python and library paths
export PYTHONPATH=$project_dir:$PYTHONPATH
export LD_LIBRARY_PATH=$project_dir:$LD_LIBRARY_PATH

# GPU configuration
NUM_GPU=`nvidia-smi -L | wc -l`
export XLLM_MODEL_MP_SIZE=$NUM_GPU
export XLLM_PARALLEL_LOCAL_WORLD_SIZE=$NUM_GPU
export XLLM_PARALLEL_TP_SIZE=$NUM_GPU

# Network configuration
LOCAL_ADDR=$(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
export VETURBORPC_LOCAL_ADDR=${LOCAL_ADDR}

# Model configuration
export XLLM_MODEL_NAME=deepseek-r1
export XLLM_MODEL_VERSION=250120

# Model directories
DEEPSEEK_MODEL_DIR=/data/models/DeepSeek-R1-ENC-xLLM
DEEPSEEK_DRAFT_MODEL_DIR=/data/models/DeepSeek-R1-DRAFT-ENC-xLLM
export XPERF_TUNER_CONFIG_LOAD_PATH=$DEEPSEEK_MODEL_DIR/saved_model/gemm_config
export XLLM_DRAFT_MODEL_MODEL_DIR=$DEEPSEEK_DRAFT_MODEL_DIR

# Environment file path
XLLM_ENV_PATH=/app/xllm/prefill_enc.env

# Start the prefiller service
./private_xllm.bin \
        --model-dir $DEEPSEEK_MODEL_DIR \
        --env-path $XLLM_ENV_PATH \
        --driver-type splitwise_prefill \
        --num-server-procs 4 \
        --port 62000 