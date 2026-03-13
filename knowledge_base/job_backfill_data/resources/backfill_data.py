from databricks.bundles.jobs import (
    Job,
    Task,
    SqlTask,
    SqlTaskFile,
    JobParameterDefinition,
)

run_daily_sql = Task(
    task_key="run_daily_sql",
    sql_task=SqlTask(
        warehouse_id="<your_warehouse_id>",
        file=SqlTaskFile(path="src/my_query.sql"),
        parameters={"run_date": "{{job.parameters.run_date}}"},
    ),
)

job = Job(
    name="sql_backfill_example",
    tasks=[run_daily_sql],
    parameters=[
        JobParameterDefinition(name="run_date", default="2024-01-01"),
    ],
)
