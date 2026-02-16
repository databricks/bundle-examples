from databricks.bundles.jobs import (
    Job,
    Task,
    NotebookTask,
    ConditionTask,
    ConditionTaskOp,
    TaskDependency,
)

# 1) Producer task: runs a notebook and emits a task value
check_quality = Task(
    task_key="check_quality",
    notebook_task=NotebookTask(notebook_path="src/branch/check_quality.py"),
)

# 2) Branch task: evaluates an expression using an upstream task value
branch = Task(
    task_key="branch",
    condition_task=ConditionTask(
        left="{{tasks.check_quality.values.bad_records}}",
        op=ConditionTaskOp.GREATER_THAN,
        right="100",
    ),
    depends_on=[TaskDependency(task_key="check_quality")],
)

# 3) Downstream tasks: gated on the condition outcome
fix_path = Task(
    task_key="fix_path",
    notebook_task=NotebookTask(notebook_path="src/branch/fix_path.py"),
    depends_on=[TaskDependency(task_key="branch", outcome="true")],
)

skip_path = Task(
    task_key="skip_path",
    notebook_task=NotebookTask(notebook_path="src/branch/skip_path.py"),
    depends_on=[TaskDependency(task_key="branch", outcome="false")],
)

job = Job(
    name="conditional_execution_example",
    tasks=[check_quality, branch, fix_path, skip_path],
)
