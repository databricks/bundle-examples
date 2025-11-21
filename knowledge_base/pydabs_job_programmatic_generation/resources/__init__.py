import os
import glob

from databricks.bundles.core import (
    Bundle,
    Resources,
    load_resources_from_current_package_module,
)


def load_resources(bundle: Bundle) -> Resources:
    """
    'load_resources' function is referenced in databricks.yml and is responsible for loading
    bundle resources defined in Python code. This function is called by Databricks CLI during
    bundle deployment. After deployment, this function is not used.
    """

    # the default implementation loads all Python files in 'resources' directory
    # return load_resources_from_current_package_module()

    """
    load_resources() is called during bundle deployment
    Here a job is created for every notebook in the src folder 
    """
    resources = Resources()
    for file in glob.glob("src/notebook*.py", recursive=True):
        resources.add_job(
            resource_name=os.path.basename(file).removesuffix(".py"),
            job={
                "name": file,
                "tasks": [
                    {
                        "task_key": "notebook_task",
                        "notebook_task": {"notebook_path": file},
                    },
                ],
            },
        )

    return resources
