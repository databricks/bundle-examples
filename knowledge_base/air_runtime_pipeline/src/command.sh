#!/bin/bash
# The launch script the AI Runtime task runs on each node. The platform injects
# the distributed-run coordinates (NODE_RANK, WORLD_SIZE, MASTER_ADDR,
# MASTER_PORT) into the environment; a real workload would pass them to torchrun.
set -uo pipefail

echo "AI Runtime training — rank ${NODE_RANK:-0} of ${WORLD_SIZE:-1}"
echo "MASTER_ADDR=${MASTER_ADDR:-<unset>} MASTER_PORT=${MASTER_PORT:-<unset>}"

# The launcher populates the environment with platform values (distributed-run
# coordinates, MLflow wiring, and the paths below). Note: ai_runtime_task fields
# do NOT accept user parameters/task values, and none surface here — a training
# task takes its inputs via code_source and these launcher-provided paths.
echo "CODE_SOURCE_PATH=${CODE_SOURCE_PATH:-<unset>}"
echo "REQUIREMENTS_YAML_PATH=${REQUIREMENTS_YAML_PATH:-<unset>}"

# ai_runtime_task fields can't carry parameters, but the launcher exports a few
# useful paths into the environment (dump them above to see the full set):
#   CODE_SOURCE_PATH     - where the code_source archive was extracted
#   REQUIREMENTS_YAML_PATH - the synced src/requirements.yaml under ${workspace.file_path}
# The preprocess task wrote the dataset to ${workspace.file_path}/shared, a
# sibling of that src/ directory, so derive it from REQUIREMENTS_YAML_PATH.
src_dir="$(dirname "${REQUIREMENTS_YAML_PATH}")"
dataset_path="$(cd "${src_dir}/.." && pwd)/shared/dataset.csv"

python3 "${CODE_SOURCE_PATH}/train.py" "${dataset_path}"
