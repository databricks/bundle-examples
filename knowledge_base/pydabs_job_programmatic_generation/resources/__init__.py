import os
import glob

from databricks.bundles.core import (
    Bundle,
    Resources,
)
from databricks.bundles.schemas import Schema


def load_resources(bundle: Bundle) -> Resources:
    """
    'load_resources' function is referenced in databricks.yml and is responsible for loading
    bundle resources defined in Python code. This function is called by Databricks CLI during
    bundle deployment. After deployment, this function is not used.

    the default implementation loads all Python files in 'resources' directory
    return load_resources_from_current_package_module()

    Here a job is created for every notebook in the src folder
    Plus a schema for the dev environment, to have one schema per user deploying the Job
    """
    resources = Resources()

    target_schema_name = "target_prod_schema"  # this is the schema name for prod - should be deployed with Terraform

    if bundle.target == "dev":
        # create 1 schema per user in other environments
        # note databricks.yml: the target dev is mode "development"
        schema = Schema(
            catalog_name="main",
            name="prog_gen_target",
            comment="Schema for output data",
        )
        resources.add_schema(resource_name="project_schema", schema=schema)
        target_schema_name = "${resources.schemas.project_schema.name}"

    for file in glob.glob("src/*.sql", recursive=True):
        resources.add_job(
            resource_name=os.path.basename(file).removesuffix(".sql"),
            job={
                "name": file,
                "tasks": [
                    {
                        "task_key": "create_table",
                        "sql_task": {
                            "parameters": {"target_schema": target_schema_name},
                            "file": {
                                "path": file,
                            },
                            "warehouse_id": "${resources.sql_warehouses.twoxs_warehouse.id}",
                        },
                    }
                ],
            },
        )

    return resources
