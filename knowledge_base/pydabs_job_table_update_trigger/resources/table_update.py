from databricks.bundles.jobs import (
    Job,
    NotebookTask,
    Task,
    TriggerSettings,
    TableUpdateTriggerConfiguration,
)

consume_table = Task(
    task_key="consume_table",
    notebook_task=NotebookTask(notebook_path="src/assets/consume_table.py"),
)

job = Job(
    name="table_update_example",
    trigger=TriggerSettings(
        table_update=TableUpdateTriggerConfiguration(
            table_names=["main.analytics.daily_events"],
            min_time_between_triggers_seconds=0,
            wait_after_last_change_seconds=3600,
        )
    ),
    tasks=[consume_table],
)
