from databricks.bundles.jobs import Job, Task, NotebookTask, TaskDependency

task_a = Task(
    task_key="task_a",
    notebook_task=NotebookTask(notebook_path="src/notebook_task_a.py"),
)
task_b = Task(
    task_key="task_b",
    depends_on=[TaskDependency(task_key="task_a")],
    notebook_task=NotebookTask(notebook_path="src/notebook_task_b.py"),
)

task_values_simple=Job(
    name="task_values_simple",
    tasks=[
        task_a,
        task_b,
    ],
)
