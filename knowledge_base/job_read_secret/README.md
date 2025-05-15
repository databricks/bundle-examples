# Databricks job that reads a secret from a secret scope

This example demonstrates how to define a secret scope and a job with a task that reads from it in a Databricks Asset Bundle.

It includes and deploys an example secret scope, a job managed by DABs and a task that reads a secret from the secret scope to a Databricks workspace.

For more information about Databricks Secrets, please refer to the [documentation](https://docs.databricks.com/aws/en/security/secrets).

## Prerequisites

* Databricks CLI v0.252.0 or above

## Usage

Modify `databricks.yml`:
* Update the `host` field under `workspace` to the Databricks workspace to deploy to.
* Change the name of the secret scope under the `secret_scopes` field.

Run `databricks bundle deploy` to deploy the bundle.

Run a script to write a secret to the secret scope:

```
SECRET_SCOPE_NAME=$(databricks bundle summary -o json | jq -r '.resources.secret_scopes.my_secret_scope.name')

databricks secrets put-secret ${SECRET_SCOPE_NAME} example-key --string-value example-value --profile ${DATABRICKS_PROFILE}
```

Run the job:
```
databricks bundle run example_python_job
```