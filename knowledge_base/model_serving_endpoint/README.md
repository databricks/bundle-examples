# Model serving endpoint with AI Gateway

This example deploys a custom model to a Databricks Model Serving endpoint.
It uses a Unity Catalog registered model, a serverless training job, and AI Gateway.

## What this example shows

- A Unity Catalog `registered_models` resource.
- A serverless job that trains a small scikit-learn model.
- The job logs the model with MLflow and registers a new version in Unity Catalog.
- The job sets the alias `champion` on the new version.
- A `model_serving_endpoints` resource that serves one version of the model.
- AI Gateway rate limits, an inference table, and usage tracking.
- Scale to zero and a `Small` workload in `dev`.
- No scale to zero and a `Medium` workload in `prod`.
- Endpoint `permissions` that give `CAN_QUERY` to a consumers group.

```
src/train_model.py  (serverless job train_model)
        ↓  log_model + set alias "champion"
<catalog>.<schema>.<model_name>  version N
        ↓  entity_version: ${var.model_version}
model_endpoint  (AI Gateway: rate limits, inference table, usage tracking)
        ↓
databricks serving-endpoints query
```

### Project structure

```
.
├── databricks.yml                              # Bundle name, variables, and the dev and prod targets
├── resources/
│   ├── model.registered_model.yml              # Unity Catalog registered model
│   ├── model.model_serving_endpoint.yml        # Serving endpoint with AI Gateway and permissions
│   ├── train_model.experiment.yml              # MLflow experiment for the training runs
│   └── train_model.job.yml                     # Serverless job that trains and registers the model
└── src/
    └── train_model.py                          # Trains the model, registers a version, sets the alias
```

### Why the endpoint uses a version number

A served entity takes `entity_name` and `entity_version`.
The `entity_version` field takes a version number.
It does not take an alias such as `champion`.
Thus, the variable `model_version` holds the version that the endpoint serves.
Set `model_version` to the version that has the `champion` alias.
The bundle does not move the alias and the endpoint version together.
You keep them aligned when you deploy.

## Prerequisites

- A Databricks workspace with Unity Catalog enabled.
- Model Serving available in the workspace region.
- Serverless compute for jobs enabled in the workspace.
- Databricks CLI version 1.20.0 or above. The `bundle validate` check for this example used that version.
- An existing Unity Catalog catalog and schema. The defaults are `main` and `default`.
- These privileges for the user who deploys the bundle:
  - `USE CATALOG` on the catalog.
  - `USE SCHEMA`, `CREATE MODEL`, and `CREATE TABLE` on the schema.
  - Permission to create serving endpoints in the workspace.
- A workspace group for the endpoint consumers. The default is `users`.

The bundle does not create the catalog or the schema.
The bundle does not delete them when you destroy it.

## Configure

Set the variables in `databricks.yml`, or use `--var` on the command line.

| Variable | Default | Purpose |
| --- | --- | --- |
| `catalog` | `main` | Catalog for the model and the inference table. |
| `schema` | `default` | Schema for the model and the inference table. |
| `model_name` | `iris_classifier` | Name of the registered model, without catalog and schema. |
| `model_version` | `1` | Model version that the endpoint serves. |
| `endpoint_name` | `iris-classifier` | Name of the serving endpoint. |
| `consumers_group` | `users` | Group that gets `CAN_QUERY` on the endpoint. |
| `workload_size` | `Small` (`prod`: `Medium`) | Provisioned concurrency range of the served model. |
| `scale_to_zero` | `true` (`prod`: `false`) | Scale the served model to zero when it gets no traffic. |
| `rate_limit_calls` | `100` (`prod`: `1000`) | Maximum calls per minute for the endpoint. |
| `rate_limit_user_calls` | `20` (`prod`: `100`) | Maximum calls per minute for each user. |

The `dev` target uses `mode: development`.
In `dev`, the CLI adds the prefix `dev_<your_user_name>_` to the model name and the endpoint name.
Thus, each developer gets a different model and endpoint.

The bundle has no `workspace.host`.
The CLI uses the host of your profile.
Use `-p <profile>` to select a profile.

## First deploy

The endpoint needs a model version before Databricks can create it.
A new registered model has no versions.
Thus, the first deploy has two steps.

1. Authenticate the CLI:

   ```sh
   databricks auth login --host <workspace-url>
   ```

2. Deploy only the registered model, the experiment, and the training job:

   ```sh
   databricks bundle deploy -t dev --select registered_models.model,experiments.train_model_experiment,jobs.train_model
   ```

3. Run the training job:

   ```sh
   databricks bundle run -t dev train_model
   ```

4. Read the version number in the job output.
   The first run creates version `1`.
   The output shows a line such as `Deploy this version with: --var model_version=1`.

5. Optional: make sure that the `champion` alias points to that version:

   ```sh
   databricks model-versions get-by-alias main.default.dev_<your_user_name>_iris_classifier champion
   ```

6. Deploy the full bundle with that version:

   ```sh
   databricks bundle deploy -t dev --var model_version=1
   ```

7. Wait until the endpoint is ready.
   The first deploy of an endpoint can take 10 minutes or more.

   ```sh
   databricks serving-endpoints get dev_<your_user_name>_iris-classifier
   ```

   The endpoint is ready when `state.ready` is `READY` and `state.config_update` is `NOT_UPDATING`.

For `prod`, do the same steps with `-t prod`.
In `prod`, the names have no prefix.

If step 6 fails, correct the cause and run the same command again.
The deploy is safe to run again.
The CLI compares the bundle with the workspace and changes only the differences.

## Query the endpoint

Use `databricks serving-endpoints query` with the endpoint name.
The model takes the four iris measurements as input.

```sh
databricks serving-endpoints query dev_<your_user_name>_iris-classifier --json '{
  "dataframe_records": [
    {"sepal length (cm)": 5.1, "sepal width (cm)": 3.5, "petal length (cm)": 1.4, "petal width (cm)": 0.2},
    {"sepal length (cm)": 6.7, "sepal width (cm)": 3.0, "petal length (cm)": 5.2, "petal width (cm)": 2.3}
  ]
}'
```

The response has one prediction for each input record.
Each prediction is a class number: `0`, `1`, or `2`.

```json
{
  "predictions": [0, 2]
}
```

The exact values depend on the trained model.
The response can also contain other fields, such as `served-model-name`.

The caller needs `CAN_QUERY` on the endpoint.
Members of `consumers_group` have `CAN_QUERY`.

## AI Gateway settings

The `ai_gateway` block in `resources/model.model_serving_endpoint.yml` sets these keys.

| Key | Purpose | `dev` | `prod` |
| --- | --- | --- | --- |
| `rate_limits` with `key: endpoint` | Limits the calls per minute for the full endpoint. | `100` | `1000` |
| `rate_limits` with `key: user` | Limits the calls per minute for each user. | `20` | `100` |
| `rate_limits.renewal_period` | Sets the period of the limit. The API supports only `minute`. | `minute` | `minute` |
| `inference_table_config.enabled` | Logs requests and responses to a Unity Catalog table. | `true` | `true` |
| `inference_table_config.catalog_name` and `schema_name` | Set the location of the inference table. | `catalog`, `schema` | `catalog`, `schema` |
| `inference_table_config.table_name_prefix` | Sets the prefix of the table name. The value is the registered model name. | `dev_<your_user_name>_iris_classifier` | `iris_classifier` |
| `usage_tracking_config.enabled` | Writes usage data to system tables. | `true` | `true` |

The inference table name is `<catalog>.<schema>.<table_name_prefix>_payload`.

The example does not set `guardrails` or `fallback_config`.
Those keys apply to external models and foundation model endpoints.

## Update the model

1. Run the training job again:

   ```sh
   databricks bundle run -t dev train_model
   ```

2. Read the new version number in the job output.
   The job also moves the `champion` alias to the new version.

3. Deploy the bundle with the new version:

   ```sh
   databricks bundle deploy -t dev --var model_version=2
   ```

To keep the version in the bundle, change the `model_version` default in `databricks.yml`.
Commit that change.

### Zero-downtime notes

- A config update does not stop the endpoint.
- The endpoint serves the old version until the new version is ready.
- Then the endpoint sends all traffic to the new version.
- During the update, `state.config_update` is `IN_PROGRESS`.
- If the new version fails to start, the endpoint continues to serve the old version.
- Do not start a second deploy while an update is `IN_PROGRESS`.

### Roll back to a prior version

1. Deploy the bundle with the prior version:

   ```sh
   databricks bundle deploy -t dev --var model_version=1
   ```

2. Move the `champion` alias back to the prior version:

   ```sh
   databricks registered-models set-alias main.default.dev_<your_user_name>_iris_classifier champion 1
   ```

Do not delete the prior model version before the rollback is complete.

## Edge cases and limits

- **Cold start with scale to zero.**
  When scale to zero is on, the endpoint stops compute after a period with no traffic.
  The next request starts the compute again.
  That request can take minutes, and it can time out.
  Use scale to zero only for `dev` and tests.
  The `prod` target sets `scale_to_zero: false`.
- **Endpoint name.**
  The name must be unique in the workspace.
  The name can contain only letters, numbers, dashes, and underscores.
  Databricks limits the length of the name.
  The `dev` prefix makes the name longer, so keep `endpoint_name` short.
  Two bundles with the same `endpoint_name` and target conflict.
- **Inference table requirements.**
  The catalog and the schema must exist before the deploy.
  The user who deploys needs `CREATE TABLE` on the schema.
  Databricks creates the table when it enables the inference table.
  Rows arrive in the table after a delay. They are not available in real time.
  To change `catalog_name`, `schema_name`, or `table_name_prefix`, first deploy with `enabled: false`.
  Then deploy the new values with `enabled: true`.
- **Cloud and region availability.**
  Model Serving is available on AWS, Azure, and Google Cloud.
  Some regions do not support Model Serving, AI Gateway, or inference tables.
  Some regions do not support GPU workloads.
  Before you deploy, examine the Model Serving region list for your cloud.
- **GPU vs CPU.**
  This example uses the default `workload_type`, which is `CPU`.
  A scikit-learn model does not need a GPU.
  For a deep learning model, set `workload_type` on the served entity, for example `GPU_SMALL`.
  GPU workloads cost more and take longer to start.
- **Serverless vs classic compute.**
  The training job uses serverless compute with `environment_version: "4"`.
  This example does not include a classic cluster configuration.
  To use a classic cluster, replace `environment_key` with a `job_cluster_key` or `new_cluster`.
  Then install `mlflow` and `scikit-learn` as task libraries.
- **No schedules.**
  The training job has no schedule or trigger.
  It runs only when you start it.
- **No secrets.**
  The bundle has no tokens, hosts, or IDs.
  The CLI gets credentials from your profile.

## Clean up

1. Destroy the bundle:

   ```sh
   databricks bundle destroy -t dev
   ```

   The CLI deletes the endpoint, the job, the experiment, and the registered model.
   The CLI deletes the endpoint before the registered model, because the endpoint refers to the model.
   Unity Catalog deletes all model versions together with the registered model.

2. Drop the inference table, because the bundle does not own it:

   ```sql
   DROP TABLE IF EXISTS main.default.dev_<your_user_name>_iris_classifier_payload;
   ```

The bundle does not delete the catalog, the schema, or the usage data in system tables.

In `prod`, the registered model can have versions that other systems use.
Before you destroy `prod`, make sure that no other endpoint or job uses the model.
To keep the model, add `lifecycle: { prevent_destroy: true }` to the registered model.
