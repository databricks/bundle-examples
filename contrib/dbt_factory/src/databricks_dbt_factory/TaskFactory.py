from abc import ABC, abstractmethod
from enum import Enum

from databricks_dbt_factory.DbtTask import DbtTask, DbtTaskOptions
from databricks_dbt_factory.Utils import generate_task_key


class DbtNodeTypes(Enum):
    """Enum class to represent dbt node types."""

    MODEL = "model"
    TEST = "test"
    SEED = "seed"
    SNAPSHOT = "snapshot"


class DbtDependencyResolver:
    @staticmethod
    def resolve(node_info: dict, valid_deps_types: list[str]) -> list[str]:
        """
        Resolves dependencies for a given DBT node.

        Args:
            node_info (dict): Information about the DBT node.
            valid_deps_types (list[str]): List of valid DBT dependency types for the node.

        Returns:
            list[str]: List of resolved dependencies.
        """
        deps = node_info.get("depends_on", {}).get("nodes", [])
        resolved_deps = []
        for node_full_name in deps:
            if any(node_full_name.startswith(dbt_type + ".") for dbt_type in valid_deps_types):
                resolved_deps.append(generate_task_key(node_full_name))
        return resolved_deps


class TaskFactory(ABC):
    """Abstract base class for creating tasks."""

    def __init__(self, resolver: DbtDependencyResolver, task_options: DbtTaskOptions, dbt_options: str = ""):
        """
        Initializes the TaskFactory.

        Args:
            resolver (DbtDependencyResolver): An instance of DbtDependencyResolver to resolve dependencies.
            task_options (DbtTaskOptions): Options for the task.
            dbt_options (str, optional): Additional DBT options. Defaults to "".
        """
        self.resolver = resolver
        self.task_options = task_options
        self.dbt_options = dbt_options

    @abstractmethod
    def create_task(self, dbt_node_name: str, dbt_node_info: dict, task_key: str) -> DbtTask:
        """
        Abstract method to create a task.

        Args:
            dbt_node_name (str): Name of the DBT node.
            dbt_node_info (dict): Information about the DBT node.
            task_key (str): Key for the task.

        Returns:
            DbtTask: An instance of Task.
        """

    def get_dbt_deps_command(self, dbt_task_name: str) -> str | None:
        """Adds the dbt deps command if enabled and applicable.
        Only return the command if enabled, and available in the task deps or not specific tasks provided.

        Args:
            dbt_task_name (str): Name of the DBT task.
        """
        if self.task_options.dbt_deps_enabled and (
            not self.task_options.dbt_tasks_deps or dbt_task_name in self.task_options.dbt_tasks_deps
        ):
            return f"dbt deps {self.dbt_options}"
        return None


class ModelTaskFactory(TaskFactory):
    """Factory for creating model tasks."""

    def create_task(self, dbt_node_name: str, dbt_node_info: dict, task_key: str) -> DbtTask:
        """
        Creates a model task.

        Args:
            dbt_node_name (str): Name of the DBT node.
            dbt_node_info (dict): Information about the DBT node.
            task_key (str): Key for the task.

        Returns:
            DbtTask: An instance of Task.
        """
        valid_dbt_deps_types: list[str] = [
            DbtNodeTypes.MODEL.value,
            DbtNodeTypes.SEED.value,
            DbtNodeTypes.SNAPSHOT.value,
            DbtNodeTypes.TEST.value,
        ]
        depends_on = self.resolver.resolve(dbt_node_info, valid_dbt_deps_types)

        dbt_deps = self.get_dbt_deps_command(dbt_node_name)
        commands = [dbt_deps] if dbt_deps else []
        commands.append(f"dbt run --select {dbt_node_name}" + (f" {self.dbt_options}" if self.dbt_options else ""))

        return DbtTask(task_key, commands, self.task_options, depends_on)


class SnapshotTaskFactory(TaskFactory):
    """Factory for creating snapshot tasks."""

    def create_task(self, dbt_node_name: str, dbt_node_info: dict, task_key: str) -> DbtTask:
        """
        Creates a snapshot task.

        Args:
            dbt_node_name (str): Name of the DBT node.
            dbt_node_info (dict): Information about the DBT node.
            task_key (str): Key for the task.

        Returns:
            DbtTask: An instance of Task.
        """
        valid_dbt_deps_types: list[str] = [DbtNodeTypes.MODEL.value]
        depends_on = self.resolver.resolve(dbt_node_info, valid_dbt_deps_types)

        dbt_deps = self.get_dbt_deps_command(dbt_node_name)
        commands = [dbt_deps] if dbt_deps else []
        commands.append(f"dbt snapshot --select {dbt_node_name}" + (f" {self.dbt_options}" if self.dbt_options else ""))

        return DbtTask(task_key, commands, self.task_options, depends_on)


class SeedTaskFactory(TaskFactory):
    """Factory for creating seed tasks."""

    def create_task(self, dbt_node_name: str, dbt_node_info: dict, task_key: str) -> DbtTask:
        """
        Creates a seed task.

        Args:
            dbt_node_name (str): Name of the DBT node.
            dbt_node_info (dict): Information about the DBT node.
            task_key (str): Key for the task.

        Returns:
            DbtTask: An instance of Task.
        """
        valid_dbt_deps_types: list[str] = []  # Seeds don't have dependencies

        depends_on = self.resolver.resolve(dbt_node_info, valid_dbt_deps_types)

        dbt_deps = self.get_dbt_deps_command(dbt_node_name)
        commands = [dbt_deps] if dbt_deps else []
        commands.append(f"dbt seed --select {dbt_node_name}" + (f" {self.dbt_options}" if self.dbt_options else ""))

        return DbtTask(task_key, commands, self.task_options, depends_on)


class TestTaskFactory(TaskFactory):
    """Factory for creating test tasks."""

    def create_task(self, dbt_node_name: str, dbt_node_info: dict, task_key: str) -> DbtTask:
        """
        Creates a test task for a single dbt test node.

        Args:
            dbt_node_name (str): Name of the DBT node.
            dbt_node_info (dict): Information about the DBT node.
            task_key (str): Key for the task.

        Returns:
            DbtTask: An instance of Task.
        """
        valid_dbt_deps_types: list[str] = [
            DbtNodeTypes.MODEL.value,
            DbtNodeTypes.SEED.value,
            DbtNodeTypes.SNAPSHOT.value,
        ]

        depends_on = self.resolver.resolve(dbt_node_info, valid_dbt_deps_types)

        dbt_deps = self.get_dbt_deps_command(dbt_node_name)
        commands = [dbt_deps] if dbt_deps else []
        commands.append(f"dbt test --select {dbt_node_name}" + (f" {self.dbt_options}" if self.dbt_options else ""))

        return DbtTask(task_key, commands, self.task_options, depends_on)

    def create_bundled_task(self, task_key: str, select: str, deps_command_name: str, depends_on: list[str]) -> DbtTask:
        """
        Creates a single test task that runs the single-model tests for a given resource via
        `dbt test --select <resource> --indirect-selection cautious`. The cautious selector
        ensures only tests whose referenced resources are entirely within this bundle are
        included; cross-model tests (e.g. `relationships`) are excluded and handled separately.

        Args:
            task_key (str): Key for the bundled task.
            select (str): Pre-computed dbt `--select` argument (qualified model name, or
                `source:<pkg>.<src>.<tbl>` for sources).
            deps_command_name (str): Name used by `get_dbt_deps_command` to decide whether to prepend `dbt deps`.
            depends_on (list[str]): Upstream task keys this bundled task should gate on.

        Returns:
            DbtTask: An instance of Task.
        """
        dbt_deps = self.get_dbt_deps_command(deps_command_name)
        commands = [dbt_deps] if dbt_deps else []
        commands.append(
            f"dbt test --select {select} --indirect-selection cautious"
            + (f" {self.dbt_options}" if self.dbt_options else "")
        )

        return DbtTask(task_key, commands, self.task_options, depends_on)
