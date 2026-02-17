from databricks.bundles.jobs import Job, Task, NotebookTask, ForEachTask, TaskDependency

generate_items = Task(
    task_key="generate_items",
    notebook_task=NotebookTask(notebook_path="src/foreach/generate_items.py"),
)

process_item = Task(
    task_key="process_item",
    for_each_task=ForEachTask(
        inputs="{{tasks.generate_items.values.items}}",
        task=Task(
            task_key="process_item_iteration",
            notebook_task=NotebookTask(
                notebook_path="src/foreach/process_item.py",
                base_parameters={"item": "{{input}}"},
            ),
        ),
        concurrency=10,
    ),
    depends_on=[TaskDependency(task_key="generate_items")],
)

job = Job(
    name="for_each_task_example",
    tasks=[generate_items, process_item],
)
