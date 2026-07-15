# AI Runtime training (full config)

This Declarative Automation Bundles example is a fuller Serverless GPU (AI
Runtime) training job than [`air_runtime_training`](../air_runtime_training). It
shows how every configurable input maps onto a native bundle: task compute,
retries and timeout, permissions, MLflow, code_source, and the sidecar files that
carry environment variables, secrets, dependencies, and hyperparameters.

## Prerequisites

* Databricks CLI v1.7.0 or above.
* A workspace with Serverless GPU (AI Runtime) enabled.
* A secret scope/key for the secret-backed env var. Update
  `src/secret_env_vars.json` to reference one that exists in your workspace, or
  remove that entry.

## Usage

Run `databricks bundle deploy` to build and upload the code and create the job.

Run `databricks bundle run train` to start the training run.

## What maps where

| Input | Where it lives |
| --- | --- |
| Experiment / MLflow run name | `ai_runtime_task.experiment` / `mlflow_run` |
| GPU type and count | `ai_runtime_task.deployments[].compute` |
| Launch command | `src/command.sh` → `deployments[].command_path` |
| Training code | `artifacts.code_source` tarball → `code_source_path` |
| Dependencies + base env version | `src/requirements.yaml` |
| Hyperparameters | `src/hyperparameters.yaml` (read via `$HYPERPARAMETERS_PATH`) |
| Environment variables | `src/env_vars.json` |
| Secret-backed env variables | `src/secret_env_vars.json` |
| Retries / timeout | `tasks[].max_retries`, `retry_on_timeout`, `timeout_seconds` |
| Permissions | `resources.jobs.train.permissions` |

The environment variables, secrets, dependencies, and hyperparameters are
delivered as sidecar files co-located with `command.sh`; the AI Runtime launcher
reads them by their fixed filenames.

## Immutable deployments (optional)

Uncomment the `experimental.immutable_folder` block in `databricks.yml` to deploy
files and artifacts as a single content-addressed snapshot (requires the direct
deployment engine, `DATABRICKS_BUNDLE_ENGINE=direct`).
