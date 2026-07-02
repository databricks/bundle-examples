import pytest
from databricks_dbt_factory.SpecsHandler import SpecsHandler
from databricks_dbt_factory.DbtFactory import DbtFactory
from databricks_dbt_factory.DbtTask import DbtTaskOptions
from databricks_dbt_factory.TaskFactory import (
    ModelTaskFactory,
    SnapshotTaskFactory,
    SeedTaskFactory,
    TestTaskFactory,
    DbtDependencyResolver,
)


@pytest.fixture
def file_handler() -> SpecsHandler:
    return SpecsHandler()


@pytest.fixture
def dbt_factory(file_handler: SpecsHandler):
    return create_dbt_factory(file_handler)


@pytest.fixture
def dbt_factory_with_deps(file_handler: SpecsHandler):
    return create_dbt_factory(file_handler, dbt_deps_enabled=True)


@pytest.fixture
def dbt_factory_with_deps_selected(file_handler: SpecsHandler):
    return create_dbt_factory(
        file_handler,
        dbt_deps_enabled=True,
        dbt_tasks_deps=["diamonds_prices", "second_dbt_model"],
    )


@pytest.fixture
def notebook_factory(file_handler: SpecsHandler):
    return create_dbt_factory(
        file_handler, task_type="notebook", notebook_path="./notebooks/dbt_runner.py"
    )


@pytest.fixture
def dbt_factory_bundled(file_handler: SpecsHandler):
    return create_dbt_factory(file_handler, bundle_tests=True)


def create_dbt_factory(
    handler: SpecsHandler,
    dbt_deps_enabled: bool = False,
    dbt_tasks_deps: list[str] | None = None,
    task_type: str = "dbt",
    notebook_path: str | None = None,
    bundle_tests: bool = False,
) -> DbtFactory:
    resolver = DbtDependencyResolver()
    task_options = DbtTaskOptions(
        source="GIT",
        environment_key="Default",
        dbt_deps_enabled=dbt_deps_enabled,
        dbt_tasks_deps=dbt_tasks_deps,
        task_type=task_type,
        notebook_path=notebook_path,
    )
    dbt_options = "--target dev"

    task_factories = {
        "model": ModelTaskFactory(resolver, task_options, dbt_options),
        "snapshot": SnapshotTaskFactory(resolver, task_options, dbt_options),
        "seed": SeedTaskFactory(resolver, task_options, dbt_options),
        "test": TestTaskFactory(resolver, task_options, dbt_options),
    }

    return DbtFactory(handler, task_factories, bundle_tests=bundle_tests)
