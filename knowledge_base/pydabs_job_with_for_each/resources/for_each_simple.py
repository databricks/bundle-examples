from databricks.bundles.jobs import Job, Task, NotebookTask, ForEachTask, TaskDependency

extract = Task(
    task_key="extract",
    notebook_task=NotebookTask(notebook_path="src/notebook_extract.py"),
)
process_item_iteration = Task(
    task_key="process_item_iteration",
    notebook_task=NotebookTask(
        notebook_path="src/notebook_process_item.py",
        base_parameters={
            "index": "{{input}}",
        },        
    ),
)
process_item = Task(
    task_key='process_item',
    depends_on=[TaskDependency(task_key="extract")],
    for_each_task=ForEachTask(
        inputs='{{tasks.extract.values.indexes}}', 
        task=process_item_iteration,
        concurrency=10
    )
)

for_each_example = Job(
    name="for_each_example",
    tasks=[
        extract,
        process_item,
    ],
    parameters=[
            {
                "name": "lookup_file_name",
                "default": "/Volumes/main/for_each_example/hotchpotch/my_file.json",
            },
    ],
)
