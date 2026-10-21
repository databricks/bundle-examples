# Model serving endpoint

This Declarative Automation Bundles example shows how to serve a Unity Catalog model on a Model Serving endpoint.
A serverless job trains a small scikit-learn model, registers a version, and sets the alias `champion`.
The endpoint uses AI Gateway rate limits, an inference table, usage tracking, and `CAN_QUERY` permissions.

For more information, refer to the [Model Serving documentation](https://docs.databricks.com/aws/en/machine-learning/model-serving/).

## Prerequisites

* Databricks CLI v1.20.0 or above
* A workspace with Unity Catalog, Model Serving, and serverless jobs enabled
* An existing catalog and schema (default: `main.default`)
* `USE CATALOG`, plus `USE SCHEMA`, `CREATE MODEL`, and `CREATE TABLE` on the schema

## Usage

The endpoint needs a model version, but a new model has no versions.
Thus, the first deploy has two deploy phases: steps 1 and 4.

1. Deploy only the model, the experiment, and the training job:

   ```sh
   databricks bundle deploy --select registered_models.model,experiments.train_model_experiment,jobs.train_model
   ```

2. Run the training job:

   ```sh
   databricks bundle run train_model
   ```

3. Read the version number in the job output, for example `--var model_version=1`.
   The job sets the `champion` alias on this version.

4. Deploy the full bundle. Set `model_version` to the `champion` version:

   ```sh
   databricks bundle deploy --var model_version=1
   ```

5. Query the endpoint. In `dev`, the endpoint name has the prefix `dev_<your_user_name>_`:

   ```sh
   databricks serving-endpoints query dev_<your_user_name>_iris-classifier --json '{
     "dataframe_records": [
       {"sepal length (cm)": 5.1, "sepal width (cm)": 3.5, "petal length (cm)": 1.4, "petal width (cm)": 0.2}
     ]
   }'
   ```

   The response has one class number for each record, for example `{"predictions": [0]}`.

6. Remove the resources. `bundle destroy` keeps the registered model while it has versions, so delete the versions and the model:

   ```sh
   databricks bundle destroy
   databricks model-versions delete <catalog>.<schema>.<model_name> <version>
   databricks registered-models delete <catalog>.<schema>.<model_name>
   ```

   In `dev`, `<model_name>` has the prefix `dev_<your_user_name>_`. Also drop the `<model_name>_payload` inference table.

To serve a new model version, do steps 2 to 4 again with the new version number.
To roll back, deploy again with the prior version number.
Use `-t prod` for the `prod` target.
