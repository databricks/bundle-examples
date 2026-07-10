import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DbtTaskOptions:
    """Options shared by every generated task. All tasks are serverless notebook tasks."""

    environment_key: str = "Default"
    """Key of the serverless environment the task runs on. Must match an environment defined on the job."""

    notebook_path: str | None = None
    """Workspace path to the dbt runner notebook that each task executes."""

    project_directory: str | None = None
    """Path to the dbt project directory, resolved relative to the runner notebook (or absolute)."""

    profiles_directory: str | None = None
    """Optional path to the dbt profiles directory (passed to dbt as `--profiles-dir`)."""


@dataclass(frozen=True)
class DbtTask:
    """A single generated Databricks notebook task that runs one batch of dbt commands."""

    task_key: str
    commands: list[str]
    options: DbtTaskOptions
    depends_on: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Renders the task as a serverless `notebook_task` dict for the Databricks job spec."""
        base_parameters: dict[str, str] = {"dbt_commands": json.dumps(self.commands)}
        if self.options.project_directory:
            base_parameters["project_directory"] = self.options.project_directory
        if self.options.profiles_directory:
            base_parameters["profiles_directory"] = self.options.profiles_directory

        return {
            "task_key": self.task_key,
            "depends_on": [{"task_key": dep} for dep in (self.depends_on or [])],
            "environment_key": self.options.environment_key,
            "notebook_task": {
                "notebook_path": self.options.notebook_path,
                "base_parameters": base_parameters,
            },
        }
