import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from databricks_dbt_factory.Utils import DYNAMIC_VALUE_REFERENCE


_MAX_NOTEBOOK_BASE_PARAMETERS_BYTES = 1_000_000


class TaskType(Enum):
    """Supported task types for generated Databricks tasks."""

    DBT = "dbt"
    NOTEBOOK = "notebook"


@dataclass(frozen=True)
class DbtTaskOptions:
    environment_key: str = "Default"  # serverless env
    """The key of an environment. It has to be unique within a job."""

    catalog: str | None = None
    """Optional name of the catalog to use. The value is the top level in the 3-level namespace of
    Unity Catalog (catalog / schema / relation). The catalog value can only be specified if a
    warehouse_id is specified. Requires dbt-databricks >= 1.1.1."""

    profiles_directory: str | None = None
    """Optional (relative) path to the profiles directory. Can only be specified if no warehouse_id is
    specified. If no warehouse_id is specified and this folder is unset, the root directory is used."""

    project_directory: str | None = None
    """Path to the project directory. Optional for Git sourced tasks, in which case if no value is
    provided, the root of the Git repository is used."""

    schema: str | None = None
    """Optional schema to write to. This parameter is only used when a warehouse_id is also provided.
    If not provided, the `default` schema is used."""

    source: str | None = None
    """Optional location type of the project directory. When set to `WORKSPACE`, the project will be
    retrieved from the local Databricks workspace. When set to `GIT`, the project will be retrieved
    from a Git repository defined in `git_source`. If the value is empty, the task will use `GIT` if
    `git_source` is defined and `WORKSPACE` otherwise.
    
    * `WORKSPACE`: Project is located in Databricks workspace. * `GIT`: Project is located in cloud
    Git provider."""

    warehouse_id: str | None = None
    """ID of the SQL warehouse to connect to. If provided, we automatically generate and provide the
    profile and connection details to dbt. It can be overridden on a per-command basis by using the
    `--profiles-dir` command line argument."""

    dbt_deps_enabled: bool = False
    """Optional flag to enable dbt deps to be run before each task. Defaults to False."""

    dbt_tasks_deps: list[str] = field(default_factory=list)
    """Optional comma separated list of tasks that requires dbt debs. Only in effect if dbt_deps_enabled is enabled."""

    task_type: TaskType = TaskType.NOTEBOOK
    """Task type to generate: `TaskType.NOTEBOOK` for a notebook_task wrapper (default),
    `TaskType.DBT` for a native dbt_task. Strings are accepted and coerced — any value outside the
    enum raises `ValueError`. Notebook mode enables base environment support and environment
    variables on serverless."""

    notebook_path: str | None = None
    """Path to the dbt runner notebook. Required when task_type is `TaskType.NOTEBOOK`."""

    job_cluster_key: str | None = None
    """Job cluster key for running tasks on job compute instead of serverless."""

    def __post_init__(self):
        if not isinstance(self.task_type, TaskType):
            object.__setattr__(self, "task_type", TaskType(self.task_type))
        if self.task_type is TaskType.NOTEBOOK:
            if not self.notebook_path:
                raise ValueError("notebook_path is required when task_type=NOTEBOOK.")
            unsupported = []
            for name, value in (
                ("warehouse_id", self.warehouse_id),
                ("schema", self.schema),
                ("catalog", self.catalog),
            ):
                if value:
                    unsupported.append(name)
            if unsupported:
                raise ValueError(
                    f"{', '.join(unsupported)} cannot be set with task_type=NOTEBOOK; "
                    "notebook tasks connect via profiles.yml."
                )


@dataclass(frozen=True)
class DbtTask:
    """Represents a dbt task in the Databricks job definition."""

    task_key: str
    commands: list[str]
    options: DbtTaskOptions
    depends_on: list[str] | None = None

    def to_dict(self) -> dict:
        """Converts the Task to a dictionary suitable for the job definition."""
        if self.options.task_type is TaskType.NOTEBOOK:
            return self._to_notebook_dict()
        return self._to_dbt_dict()

    def _base_spec(self) -> dict[str, Any]:
        spec: dict[str, Any] = {
            "task_key": self.task_key,
            "depends_on": [{"task_key": dep} for dep in (self.depends_on or [])],
        }
        if self.options.job_cluster_key:
            spec["job_cluster_key"] = self.options.job_cluster_key
        else:
            spec["environment_key"] = self.options.environment_key
        return spec

    def _to_dbt_dict(self) -> dict[str, Any]:
        spec = self._base_spec()
        dbt_task: dict[str, Any] = {"commands": self.commands}

        if self.options.source:
            dbt_task["source"] = self.options.source
        if self.options.project_directory:
            dbt_task["project_directory"] = self.options.project_directory
        if self.options.schema:
            dbt_task["schema"] = self.options.schema
        if self.options.warehouse_id:
            dbt_task["warehouse_id"] = self.options.warehouse_id
        if self.options.catalog:
            dbt_task["catalog"] = self.options.catalog
        if self.options.profiles_directory:
            dbt_task["profiles_directory"] = self.options.profiles_directory

        spec["dbt_task"] = dbt_task
        return spec

    def _to_notebook_dict(self) -> dict[str, Any]:
        serialized_commands = json.dumps(self.commands)
        if DYNAMIC_VALUE_REFERENCE.search(serialized_commands):
            raise ValueError(
                f"Notebook task {self.task_key!r} serialized dbt_commands forms a Databricks dynamic value "
                f"reference; rename the selected resources or change the dbt command options."
            )
        base_parameters: dict[str, str] = {
            "dbt_commands": serialized_commands,
        }
        if self.options.project_directory:
            base_parameters["project_directory"] = self.options.project_directory
        if self.options.profiles_directory:
            base_parameters["profiles_directory"] = self.options.profiles_directory

        serialized_size = len(json.dumps(base_parameters, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        if serialized_size > _MAX_NOTEBOOK_BASE_PARAMETERS_BYTES:
            raise ValueError(
                f"Notebook task {self.task_key!r} serializes base_parameters to {serialized_size:,} bytes; "
                f"Databricks allows at most {_MAX_NOTEBOOK_BASE_PARAMETERS_BYTES:,} bytes. Shorten its dbt "
                f"commands or path options, reduce the tests in this bundle, or generate native dbt tasks "
                f"with --task-type dbt."
            )

        notebook_task: dict[str, Any] = {
            "notebook_path": self.options.notebook_path,
            "base_parameters": base_parameters,
        }
        if self.options.source:
            notebook_task["source"] = self.options.source

        spec = self._base_spec()
        spec["notebook_task"] = notebook_task
        return spec
