# Databricks notebook source
# MAGIC %md
# MAGIC # Create or Update Model Serving Endpoint
# MAGIC
# MAGIC Create or Update the deployed serving endpoints with a new model version.
# MAGIC
# MAGIC * Make sure you've created online tables for all the required feature tables.
# MAGIC * Run this job on the workspace where you want to serve the model. 

# COMMAND ----------

# MAGIC %pip install databricks-sdk>=0.38.0
# MAGIC %restart_python

# COMMAND ----------

dbutils.widgets.text("endpoint_name", defaultValue="")
dbutils.widgets.text("model_name", defaultValue="")
dbutils.widgets.text("model_version", defaultValue="")

# COMMAND ----------

ARGS = dbutils.widgets.getAll()

endpoint_name = ARGS["endpoint_name"]
model_name = ARGS["model_name"]
model_version = ARGS["model_version"]

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ServedEntityInput, EndpointCoreConfigInput
from databricks.sdk.errors import ResourceDoesNotExist

workspace = WorkspaceClient()

# COMMAND ----------

try:
    endpoint = workspace.serving_endpoints.get(name=endpoint_name)
except ResourceDoesNotExist as e:
    endpoint = None

if endpoint is None:
    workspace.serving_endpoints.create(
        name=endpoint_name,
        config=EndpointCoreConfigInput(
            served_entities=[
                ServedEntityInput(
                    entity_name=model_name,
                    entity_version=model_version,
                    scale_to_zero_enabled=True,
                    workload_size="Small",
                )
            ]
        ),
    )
    print(f"Created endpoint {endpoint_name}")
elif endpoint.pending_config is not None:
    print(f"A pending update for endpoint {endpoint_name} is being processed.")
elif (
    endpoint.config.served_entities[0].entity_name != model_name
    or endpoint.config.served_entities[0].entity_version != model_version
):
    # Update endpoint
    workspace.serving_endpoints.update_config(
        name=endpoint_name,
        served_entities=[
            ServedEntityInput(
                entity_name=model_name,
                entity_version=model_version,
                scale_to_zero_enabled=True,
                workload_size="Small",
            )
        ],
    )
    print(f"Updated endpoint {endpoint_name}")
else:
    print("Endpoint already up-to-date")