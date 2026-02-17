from databricks.bundles.jobs import (
    FileArrivalTriggerConfiguration,
    Job,
    Task,
    TriggerSettings,
    NotebookTask,
)

process_files = Task(
    task_key="process_files",
    notebook_task=NotebookTask(notebook_path="src/files/process_files.py"),
)

job = Job(
    name="file_arrival_example",
    trigger=TriggerSettings(
        file_arrival=FileArrivalTriggerConfiguration(
            url="/Volumes/main/raw/incoming/",  # UC volume or external location
            min_time_between_triggers_seconds=60,
            wait_after_last_change_seconds=90,
        )
    ),
    tasks=[process_files],
)
