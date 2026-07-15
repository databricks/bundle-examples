# AI Runtime training

This Declarative Automation Bundles example demonstrates how to run a distributed
training job on Databricks Serverless GPU using an `ai_runtime_task`.

The bundle builds the training code into a tarball at deploy time (via the
`artifacts` section), uploads it, and references it as the task's `code_source`.
The AI Runtime launcher extracts the archive on each GPU node and runs the launch
script (`src/command.sh`).

## Prerequisites

* Databricks CLI v0.256.0 or above.
* A workspace with Serverless GPU (AI Runtime) enabled.

## Usage

Run `databricks bundle deploy` to build and upload the code and create the job.

Run `databricks bundle run train` to start the training run.

Example output:

```
$ databricks bundle run train
Run URL: https://...

2026-07-14 09:11:12 "[dev pieter_noordhuis] Example AI Runtime training" TERMINATED SUCCESS
```

## How it works

* `artifacts.code_source` runs `.bin/build_tarball.sh` to produce `dist/code.tgz` — a
  gzipped tar with a single top-level directory (`air_runtime_training/`). The
  bundle uploads it to `${workspace.artifact_path}/.internal/`.
* `ai_runtime_task.code_source_path` points at that uploaded tarball. On the node
  it is extracted to `/databricks/code_source/air_runtime_training/` (also
  symlinked at `$HOME/air_runtime_training/`).
* `deployments[].command_path` points at `src/command.sh`, synced to the
  workspace. `command.sh` is the launch script; `requirements.yaml` (its
  co-located sidecar) declares the base-environment version and pip dependencies.
* `compute.accelerator_type` / `accelerator_count` select the GPU SKU and total
  GPU count (`accelerator_count` is across all nodes and must be a multiple of the
  per-node count encoded in the type, e.g. `GPU_8xH100` → multiples of 8).

## Immutable deployments (optional)

Uncomment the `experimental.immutable_folder` block in `databricks.yml` to deploy
all files and artifacts as a single content-addressed, immutable snapshot. The
`${workspace.*}` paths in the task resolve into the snapshot automatically. This
requires the direct deployment engine (`DATABRICKS_BUNDLE_ENGINE=direct`).
