#!/bin/bash
# Launch script that exercises every configurable input this example wires up.
set -uo pipefail

echo "== distributed coordinates (injected by the platform) =="
echo "NODE_RANK=${NODE_RANK:-0} WORLD_SIZE=${WORLD_SIZE:-1} MASTER_ADDR=${MASTER_ADDR:-<unset>} MASTER_PORT=${MASTER_PORT:-<unset>}"

echo "== plain env vars (from env_vars.json) =="
echo "NCCL_DEBUG=${NCCL_DEBUG:-<unset>}"

echo "== secret-backed env var (from secret_env_vars.json; value masked) =="
if [ -n "${HF_TOKEN:-}" ]; then echo "HF_TOKEN is set (len=${#HF_TOKEN})"; else echo "HF_TOKEN is not set"; fi

echo "== hyperparameters (path exposed as \$HYPERPARAMETERS_PATH) =="
echo "HYPERPARAMETERS_PATH=${HYPERPARAMETERS_PATH:-<unset>}"

# Run the training entrypoint delivered via code_source.
python3 "/databricks/code_source/air_runtime_full_config/train.py"
