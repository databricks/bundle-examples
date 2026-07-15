# AI Runtime pipeline

This Declarative Automation Bundles example wraps a Serverless GPU (AI Runtime)
training task in a multi-task job — the kind of workflow a single-task submit
cannot express:

```
preprocess (serverless) -> train (ai_runtime_task) -> evaluate (serverless)
```

It demonstrates `depends_on` wiring, cross-task data flow via task values, a
job-level parameter, and multi-target promotion (dev/prod).

## Prerequisites

* Databricks CLI v1.7.0 or above.
* A workspace with Serverless GPU (AI Runtime) enabled.

## Usage

Run `databricks bundle deploy` to build and upload the code and create the job.

Run `databricks bundle run pipeline` to run the whole pipeline.

Deploy the production variant (more epochs) with
`databricks bundle deploy --target prod`.

## What it demonstrates

* **Multi-task DAG** — `train` and `evaluate` declare `depends_on`, so they run in
  order and skip if an upstream fails.
* **Cross-task data flow** — `preprocess` writes a dataset file into a shared
  workspace directory (`{{job.parameters.shared_dir}}`, under `/Workspace`) and
  publishes its path with `dbutils.jobs.taskValues.set(...)`; `evaluate` reads the
  path with `dbutils.jobs.taskValues.get(...)` and opens the file. Job task
  compute is ephemeral, so intermediate data lives in the workspace file system,
  not on local disk.
  Note: `ai_runtime_task` fields don't accept `{{...}}` templating, so the `train`
  task can't consume task values directly — it takes its inputs via `code_source`
  and its command's environment.
* **Job parameter** — `epochs` is defined once and passed to `preprocess` as
  `{{job.parameters.epochs}}`.
* **Promotion** — the `prod` target overrides `epochs` and deploys in production
  mode; the same config serves both environments.
* **AI Runtime task** — `train` is an `ai_runtime_task` whose code ships as an
  artifact-built tarball (`code_source_path`) and whose launch script is synced
  (`command_path`), exactly as in [`air_runtime_training`](../air_runtime_training).

## Immutable deployments (optional)

Uncomment the `experimental.immutable_folder` block in `databricks.yml`. This
example works with it enabled — including the serverless `preprocess`/`evaluate`
tasks, which read their `python_file` from the snapshot as long as it is in the
sync set (it is). Keep `python_file` as a local `../src/...` path so it passes
deploy-time validation and is rewritten into the snapshot. Requires the direct
deployment engine (`DATABRICKS_BUNDLE_ENGINE=direct`).
