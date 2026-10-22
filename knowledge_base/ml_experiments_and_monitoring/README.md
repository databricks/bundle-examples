# ML experiments and monitoring

This Declarative Automation Bundles example defines an MLflow experiment, a Unity Catalog registered model with grants, a serverless training job, and a quality monitor.
The training job sets the `champion` alias and writes an inference table that Lakehouse Monitoring watches.

For more information, please refer to the [documentation](https://docs.databricks.com/aws/en/dev-tools/bundles/resources).

## Prerequisites

* Databricks CLI v1.20.0 or above
* A Unity Catalog schema that you can use to create models and tables
* An account group for model consumers

## Usage

| Resource | Purpose |
| --- | --- |
| `experiments.training` | Stores the training runs. |
| `registered_models.iris` | Stores model versions and grants `EXECUTE` to the consumers group. |
| `jobs.train` | Trains the model, sets the `champion` alias, and writes the inference table. |
| `job_runs.train_on_deploy` | Runs the training job during deploy. |
| `quality_monitors.predictions` | Monitors the inference table and sends email on failure. |

1. Update the `host` field in `databricks.yml` to your workspace URL. Set the `catalog`, `schema`, and `consumers_group` variables.

2. Deploy the bundle. The deploy runs the training job once, then creates the monitor:

   ```
   databricks bundle deploy
   ```

3. Run the training job again to register a new model version:

   ```
   databricks bundle run train
   ```

4. Refresh the monitor. Use the inference table name from the job output:

   ```
   databricks quality-monitors run-refresh <catalog>.<schema>.<model_name>_predictions
   ```

5. Deploy to production. The `prod` target keeps the daily refresh schedule active:

   ```
   databricks bundle deploy --target prod
   ```

6. Delete each model version that the training job registered:

   ```
   databricks model-versions delete <catalog>.<schema>.<model_name> <version>
   ```

7. Remove the resources:

   ```
   databricks bundle destroy
   ```
