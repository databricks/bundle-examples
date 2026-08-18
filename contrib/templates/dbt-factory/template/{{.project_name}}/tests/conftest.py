import pytest

from databricks_dbt_factory.dbt_factory import DbtFactory
from databricks_dbt_factory.dbt_task import DbtTaskOptions
from databricks_dbt_factory.task_factory import (
    ModelTaskFactory,
    SnapshotTaskFactory,
    SeedTaskFactory,
    TestTaskFactory,
    DbtDependencyResolver,
)


def create_dbt_factory(bundle_tests: bool = False) -> DbtFactory:
    resolver = DbtDependencyResolver()
    task_options = DbtTaskOptions(
        environment_key="Default",
        notebook_path="./notebooks/dbt_runner.py",
    )
    dbt_options = "--target dev"

    task_factories = {
        "model": ModelTaskFactory(resolver, task_options, dbt_options),
        "snapshot": SnapshotTaskFactory(resolver, task_options, dbt_options),
        "seed": SeedTaskFactory(resolver, task_options, dbt_options),
        "test": TestTaskFactory(resolver, task_options, dbt_options),
    }

    return DbtFactory(task_factories, bundle_tests=bundle_tests)


@pytest.fixture
def dbt_factory() -> DbtFactory:
    return create_dbt_factory()


@pytest.fixture
def dbt_factory_bundled() -> DbtFactory:
    return create_dbt_factory(bundle_tests=True)
