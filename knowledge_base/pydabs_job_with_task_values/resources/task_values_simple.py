from databricks.bundles.jobs import Job, Task, NotebookTask, TaskDependency

producer = Task(
    task_key="producer",
    notebook_task=NotebookTask(notebook_path="src/xcom/producer.py"),
)

consumer = Task(
    task_key="consumer",
    depends_on=[TaskDependency(task_key="producer")],
    notebook_task=NotebookTask(notebook_path="src/xcom/consumer.py"),
)

job = Job(
    name="xcom_to_task_values_example",
    tasks=[producer, consumer],
)