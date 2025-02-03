# Databricks notebook source
# MAGIC %md
# MAGIC # Sync the share and add all required resources
# MAGIC
# MAGIC Add a model and all it's dependencies to the given Share.
# MAGIC
# MAGIC Prerequisit:
# MAGIC
# MAGIC * Create a share in [delta-sharing](https://docs.databricks.com/en/delta-sharing/create-share.html).
# MAGIC * Config the default parameters in resources/manage_share.job.yml 

# COMMAND ----------

# MAGIC %pip install databricks-sdk>=0.38.0
# MAGIC %restart_python

# COMMAND ----------

dbutils.widgets.text("model_name", defaultValue="")
dbutils.widgets.text("share_name", defaultValue="")
dbutils.widgets.text("max_number_of_versions_to_sync", defaultValue="10")

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ServedEntityInput
from databricks.sdk.service.sharing import (
    SharedDataObjectUpdate,
    SharedDataObjectUpdateAction,
    SharedDataObjectDataObjectType,
    SharedDataObject,
    SharedDataObjectHistoryDataSharingStatus,
)

workspace = WorkspaceClient()

# COMMAND ----------

model_name = dbutils.widgets.get("model_name")
share_name = dbutils.widgets.get("share_name")
max_number_of_versions_to_sync = int(
    dbutils.widgets.get("max_number_of_versions_to_sync")
)

print("~~~ parameters ~~~")
print(f"Model name: {model_name}")
print(f"Share name: {share_name}")
print(f"Max number of versions to sync: {max_number_of_versions_to_sync}")

# COMMAND ----------

def getLatestVersions(model_name: str, max_number_of_versions: int):
    versions = workspace.model_versions.list(
        full_name=model_name,
    )
    result = []
    for version in versions:
        result.append(
            workspace.model_versions.get(full_name=model_name, version=version.version)
        )
    return result


def getDependencies(model_versions):
    tables = set()
    functions = set()
    for version in model_versions:
        for dependency in version.model_version_dependencies.dependencies:
            if dependency.table is not None:
                tables.add(dependency.table.table_full_name)
            elif dependency.function is not None:
                functions.add(dependency.function.function_full_name)
    return tables, functions

# COMMAND ----------

versions = getLatestVersions(model_name, max_number_of_versions_to_sync)
tableDependencies, functionDependencies = getDependencies(versions)

# COMMAND ----------

from lib.rest_client import RestClient

notebook_context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
rc = RestClient(notebook_context)

# COMMAND ----------

shareInfo = rc.get_share_info(share_name)

# COMMAND ----------

sharedTables = sharedFunctions = sharedSchemas = sharedModels = set()
model_is_shared = False

if "objects" in shareInfo:
    sharedTables = set(
        [
            obj["name"]
            for obj in filter(
                lambda obj: obj["data_object_type"] == "TABLE", shareInfo["objects"]
            )
        ]
    )
    sharedFunctions = set(
        [
            obj["name"]
            for obj in filter(
                lambda obj: obj["data_object_type"] == "FUNCTION", shareInfo["objects"]
            )
        ]
    )
    sharedSchemas = set(
        [
            obj["name"]
            for obj in filter(
                lambda obj: obj["data_object_type"] == "SCHEMA", shareInfo["objects"]
            )
        ]
    )
    sharedModels = set(
        [
            obj["name"]
            for obj in filter(
                lambda obj: obj["data_object_type"] == "MODEL", shareInfo["objects"]
            )
        ]
    )
    model_is_shared = model_name in sharedModels

# COMMAND ----------

def getSchema(full_name):
    name_sections = full_name.split(".")
    return f"{name_sections[0]}.{name_sections[1]}"


def getObjectsToAdd(dependencies, sharedObjects, sharedSchemas):
    newDependencies = dependencies - sharedObjects
    return list(filter(lambda x: getSchema(x) not in sharedSchemas, newDependencies))

# COMMAND ----------

tablesToAdd = getObjectsToAdd(tableDependencies, sharedTables, sharedSchemas)
functionsToAdd = getObjectsToAdd(functionDependencies, sharedFunctions, sharedSchemas)

updates = []

for table in tablesToAdd:
    updates.append(
        SharedDataObjectUpdate(
            action=SharedDataObjectUpdateAction.ADD,
            data_object=SharedDataObject(
                name=table,
                data_object_type=SharedDataObjectDataObjectType.TABLE,
                history_data_sharing_status=SharedDataObjectHistoryDataSharingStatus.ENABLED,
            ),
        )
    )


for function in functionsToAdd:
    updates.append(
        SharedDataObjectUpdate(
            action=SharedDataObjectUpdateAction.ADD,
            data_object=SharedDataObject(
                name=function, data_object_type=SharedDataObjectDataObjectType.FUNCTION
            ),
        )
    )

if not model_is_shared:
    updates.append(
        SharedDataObjectUpdate(
            action=SharedDataObjectUpdateAction.ADD,
            data_object=SharedDataObject(
                name=model_name, data_object_type=SharedDataObjectDataObjectType.MODEL
            ),
        )
    )


def print_update_summary(updates):
    for update in updates:
        print(
            f"{update.action.value} {update.data_object.data_object_type} {update.data_object.name}"
        )


if updates:
    print_update_summary(updates)
    workspace.shares.update(name=share_name, updates=updates)
else:
    print("The share is already up-to-date.")

