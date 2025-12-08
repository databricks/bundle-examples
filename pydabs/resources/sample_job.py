from databricks.bundles.jobs import Job

"""
A sample job for pydabs.
"""

sample_job = Job.from_dict(
    {
        "name": "sample_job",
        "trigger": {
            # Run this job every day, exactly one day from the last run; see https://docs.databricks.com/api/workspace/jobs/create#trigger
            "periodic": {
                "interval": 1,
                "unit": "DAYS",
            },
        },
        # "email_notifications": {
        #     "on_failure": [
        #         "user@company.com",
        #     ],
        # },
        "parameters": [
            {
                "name": "catalog",
                "default": "${var.catalog}",
            },
            {
                "name": "schema",
                "default": "${var.schema}",
            },
        ],
        "tasks": [
            {
                "task_key": "notebook_task",
                "notebook_task": {
                    "notebook_path": "src/sample_notebook.ipynb",
                },
            },
            {
                "task_key": "python_wheel_task",
                "depends_on": [
                    {"task_key": "notebook_task"},
                ],
                "python_wheel_task": {
                    "package_name": "pydabs",
                    "entry_point": "main",
                    "parameters": [
                        "--catalog",
                        "${var.catalog}",
                        "--schema",
                        "${var.schema}",
                    ],
                },
                "environment_key": "default",
            },
            {
                "task_key": "refresh_pipeline",
                "depends_on": [
                    {"task_key": "notebook_task"},
                ],
                "pipeline_task": {
                    "pipeline_id": "${resources.pipelines.pydabs_etl.id}",
                },
            },
        ],
        "environments": [
            {
                "environment_key": "default",
                "spec": {
                    "environment_version": "4",
                    "dependencies": [
                        # By default we just include the .whl file generated for the pydabs package.
                        # See https://docs.databricks.com/dev-tools/bundles/library-dependencies.html
                        # for more information on how to add other libraries.
                        "dist/*.whl",
                    ],
                },
            },
        ],
    }
)
