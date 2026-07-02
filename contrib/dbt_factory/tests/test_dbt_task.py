import pytest

from databricks_dbt_factory.DbtTask import DbtTask, DbtTaskOptions, TaskType


def test_notebook_task_with_job_cluster_key():
    options = DbtTaskOptions(
        task_type="notebook",
        notebook_path="./notebooks/dbt_runner.py",
        source="WORKSPACE",
        project_directory="/project",
        profiles_directory="/profiles",
        job_cluster_key="dbt_cluster",
    )
    task = DbtTask(
        task_key="my_model",
        commands=["dbt run --select my_model --target dev"],
        options=options,
        depends_on=["upstream_model"],
    )

    result = task.to_dict()

    assert result["job_cluster_key"] == "dbt_cluster"
    assert "environment_key" not in result
    assert result["task_key"] == "my_model"
    assert result["depends_on"] == [{"task_key": "upstream_model"}]
    assert result["notebook_task"]["source"] == "WORKSPACE"
    assert result["notebook_task"]["base_parameters"]["project_directory"] == "/project"
    assert result["notebook_task"]["base_parameters"]["profiles_directory"] == "/profiles"


def test_notebook_task_without_job_cluster_key_uses_environment():
    options = DbtTaskOptions(
        task_type="notebook",
        notebook_path="./notebooks/dbt_runner.py",
    )
    task = DbtTask(task_key="my_model", commands=["dbt run --select my_model"], options=options)

    result = task.to_dict()

    assert result["environment_key"] == "Default"
    assert "job_cluster_key" not in result


def test_dbt_task_without_job_cluster_key_uses_environment():
    options = DbtTaskOptions(environment_key="Default")
    task = DbtTask(task_key="my_model", commands=["dbt run --select my_model"], options=options)

    result = task.to_dict()

    assert result["environment_key"] == "Default"
    assert "job_cluster_key" not in result


def test_task_type_string_is_coerced_to_enum():
    options = DbtTaskOptions(task_type="notebook", notebook_path="./runner.py")
    assert options.task_type is TaskType.NOTEBOOK


def test_task_type_invalid_value_raises():
    with pytest.raises(ValueError, match="not a valid TaskType"):
        DbtTaskOptions(task_type="Notebook")
    with pytest.raises(ValueError, match="not a valid TaskType"):
        DbtTaskOptions(task_type="dbt_task")


def test_notebook_task_rejects_warehouse_schema_catalog():
    for kwargs in (
        {"warehouse_id": "wh123"},
        {"schema": "silver"},
        {"catalog": "main"},
    ):
        with pytest.raises(ValueError, match="notebook tasks connect via profiles.yml"):
            DbtTaskOptions(task_type=TaskType.NOTEBOOK, notebook_path="/n", **kwargs)


def test_notebook_task_rejects_multiple_incompatible_fields_at_once():
    with pytest.raises(ValueError, match=r"warehouse_id, schema, catalog"):
        DbtTaskOptions(
            task_type=TaskType.NOTEBOOK,
            notebook_path="/n",
            warehouse_id="wh123",
            schema="silver",
            catalog="main",
        )


def test_dbt_task_still_accepts_warehouse_schema_catalog():
    options = DbtTaskOptions(
        task_type=TaskType.DBT,
        warehouse_id="wh123",
        schema="silver",
        catalog="main",
    )
    assert options.warehouse_id == "wh123"
