#!/bin/bash
# The launch script the AI Runtime task runs on each node. The platform injects
# the distributed-run coordinates (NODE_RANK, WORLD_SIZE, MASTER_ADDR,
# MASTER_PORT) into the environment; a real workload would pass them to torchrun.
set -uo pipefail

echo "AI Runtime training — rank ${NODE_RANK:-0} of ${WORLD_SIZE:-1}"
echo "MASTER_ADDR=${MASTER_ADDR:-<unset>} MASTER_PORT=${MASTER_PORT:-<unset>}"

# The code_source archive is extracted to /databricks/code_source/<dir> and
# symlinked at $HOME/<dir>. Run the training entrypoint from there.
python3 "/databricks/code_source/air_runtime_training/train.py"
