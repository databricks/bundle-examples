import json

from databricks_dbt_factory.DbtTask import DbtTask, DbtTaskOptions


def test_renders_serverless_notebook_task():
    options = DbtTaskOptions(
        environment_key="Default",
        notebook_path="./notebooks/dbt_runner.py",
        project_directory="/project",
        profiles_directory="/profiles",
    )
    task = DbtTask(
        task_key="my_model",
        commands=["dbt run --select my_model --target dev"],
        options=options,
        depends_on=["upstream_model"],
    )

    result = task.to_dict()

    assert result["task_key"] == "my_model"
    assert result["environment_key"] == "Default"  # serverless
    assert "job_cluster_key" not in result
    assert result["depends_on"] == [{"task_key": "upstream_model"}]

    notebook_task = result["notebook_task"]
    assert notebook_task["notebook_path"] == "./notebooks/dbt_runner.py"
    assert notebook_task["base_parameters"]["project_directory"] == "/project"
    assert notebook_task["base_parameters"]["profiles_directory"] == "/profiles"
    assert json.loads(notebook_task["base_parameters"]["dbt_commands"]) == [
        "dbt run --select my_model --target dev"
    ]


def test_defaults_and_optional_directories_are_omitted():
    options = DbtTaskOptions(notebook_path="./runner.py")
    task = DbtTask(task_key="m", commands=["dbt run --select m"], options=options)

    result = task.to_dict()

    assert result["environment_key"] == "Default"  # default serverless environment
    assert result["depends_on"] == []
    base_parameters = result["notebook_task"]["base_parameters"]
    assert "project_directory" not in base_parameters
    assert "profiles_directory" not in base_parameters
    assert json.loads(base_parameters["dbt_commands"]) == ["dbt run --select m"]
