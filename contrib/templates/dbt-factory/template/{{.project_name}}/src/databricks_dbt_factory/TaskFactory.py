from abc import ABC, abstractmethod
from enum import Enum

from databricks_dbt_factory.DbtTask import DbtTask, DbtTaskOptions


class DbtNodeTypes(Enum):
    """dbt node types that become Databricks tasks."""

    MODEL = "model"
    TEST = "test"
    SEED = "seed"
    SNAPSHOT = "snapshot"


class DbtDependencyResolver:
    @staticmethod
    def resolve(
        node_info: dict, valid_deps_types: list[str], task_keys: dict[str, str]
    ) -> list[str]:
        """
        Resolves a dbt node's upstream dependencies to Databricks task keys, keeping only the
        dependency types relevant for the node being built.

        Args:
            node_info (dict): The dbt manifest entry for the node.
            valid_deps_types (list[str]): dbt node types that should become task dependencies.
            task_keys (dict[str, str]): Task key per dbt node, from `build_task_key_maps`.

        Returns:
            list[str]: Resolved upstream task keys.
        """
        deps = node_info.get("depends_on", {}).get("nodes", [])
        resolved_deps = []
        for node_full_name in deps:
            if any(
                node_full_name.startswith(dbt_type + ".")
                for dbt_type in valid_deps_types
            ):
                resolved_deps.append(task_keys[node_full_name])
        return resolved_deps


class TaskFactory(ABC):
    """Abstract base class for building a task (one dbt command batch) from a dbt node."""

    def __init__(
        self,
        resolver: DbtDependencyResolver,
        task_options: DbtTaskOptions,
        dbt_options: str = "",
    ):
        """
        Args:
            resolver (DbtDependencyResolver): Resolves upstream dependencies to task keys.
            task_options (DbtTaskOptions): Shared task options (serverless notebook task).
            dbt_options (str, optional): Extra options appended to every dbt command. Defaults to "".
        """
        self.resolver = resolver
        self.task_options = task_options
        self.dbt_options = dbt_options

    @abstractmethod
    def create_task(
        self,
        dbt_node_name: str,
        dbt_node_info: dict,
        task_key: str,
        task_keys: dict[str, str],
    ) -> DbtTask:
        """Builds a `DbtTask` for a single dbt node. `task_keys` maps every dbt node to its task key."""

    def _command(self, verb: str, select: str) -> str:
        """Assembles a `dbt <verb> --select <select> [extra options]` command string."""
        return f"dbt {verb} --select {select}" + (
            f" {self.dbt_options}" if self.dbt_options else ""
        )


class ModelTaskFactory(TaskFactory):
    """Factory for model tasks (`dbt run`)."""

    def create_task(
        self,
        dbt_node_name: str,
        dbt_node_info: dict,
        task_key: str,
        task_keys: dict[str, str],
    ) -> DbtTask:
        valid_dbt_deps_types = [
            DbtNodeTypes.MODEL.value,
            DbtNodeTypes.SEED.value,
            DbtNodeTypes.SNAPSHOT.value,
            DbtNodeTypes.TEST.value,
        ]
        depends_on = self.resolver.resolve(
            dbt_node_info, valid_dbt_deps_types, task_keys
        )
        return DbtTask(
            task_key,
            [self._command("run", dbt_node_name)],
            self.task_options,
            depends_on,
        )


class SnapshotTaskFactory(TaskFactory):
    """Factory for snapshot tasks (`dbt snapshot`)."""

    def create_task(
        self,
        dbt_node_name: str,
        dbt_node_info: dict,
        task_key: str,
        task_keys: dict[str, str],
    ) -> DbtTask:
        depends_on = self.resolver.resolve(
            dbt_node_info, [DbtNodeTypes.MODEL.value], task_keys
        )
        return DbtTask(
            task_key,
            [self._command("snapshot", dbt_node_name)],
            self.task_options,
            depends_on,
        )


class SeedTaskFactory(TaskFactory):
    """Factory for seed tasks (`dbt seed`). Seeds have no dependencies."""

    def create_task(
        self,
        dbt_node_name: str,
        dbt_node_info: dict,
        task_key: str,
        task_keys: dict[str, str],
    ) -> DbtTask:
        depends_on = self.resolver.resolve(dbt_node_info, [], task_keys)
        return DbtTask(
            task_key,
            [self._command("seed", dbt_node_name)],
            self.task_options,
            depends_on,
        )


class TestTaskFactory(TaskFactory):
    """Factory for test tasks (`dbt test`)."""

    def create_task(
        self,
        dbt_node_name: str,
        dbt_node_info: dict,
        task_key: str,
        task_keys: dict[str, str],
    ) -> DbtTask:
        valid_dbt_deps_types = [
            DbtNodeTypes.MODEL.value,
            DbtNodeTypes.SEED.value,
            DbtNodeTypes.SNAPSHOT.value,
        ]
        depends_on = self.resolver.resolve(
            dbt_node_info, valid_dbt_deps_types, task_keys
        )
        return DbtTask(
            task_key,
            [self._command("test", dbt_node_name)],
            self.task_options,
            depends_on,
        )

    def create_bundled_task(
        self, task_key: str, select: str, depends_on: list[str]
    ) -> DbtTask:
        """
        Creates a single task that runs the single-model tests for a resource via
        `dbt test --select <resource> --indirect-selection cautious`. The cautious selector
        includes only tests whose referenced resources are entirely within this bundle;
        cross-model tests (e.g. `relationships`) are excluded and handled as standalone tasks.

        Args:
            task_key (str): Key for the bundled task.
            select (str): Pre-computed dbt `--select` argument (qualified model name, or
                `source:<pkg>.<src>.<tbl>` for sources).
            depends_on (list[str]): Upstream task keys this bundled task should gate on.

        Returns:
            DbtTask: The bundled test task.
        """
        command = f"dbt test --select {select} --indirect-selection cautious" + (
            f" {self.dbt_options}" if self.dbt_options else ""
        )
        return DbtTask(task_key, [command], self.task_options, depends_on)
