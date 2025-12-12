from databricks.bundles.jobs import (
    FileArrivalTriggerConfiguration,
    Job,
    NotebookTask,
    Task,
    TriggerSettings,
)

pydabs_job_file_arrival = Job(
    name="pydabs_job_file_arrival",
    tasks=[
        Task(
            task_key="process_new_files",
            notebook_task=NotebookTask(
                notebook_path="src/process_files.ipynb",
                base_parameters={
                    "file_arrival_location": "{{job.trigger.file_arrival.location}}"
                },
            ),
        )
    ],
    trigger=TriggerSettings(
        file_arrival=FileArrivalTriggerConfiguration(
            url="/Volumes/your_catalog/your_schema/your_volume/",
            min_time_between_triggers_seconds=60,
            wait_after_last_change_seconds=90,
        ),
    ),
)
