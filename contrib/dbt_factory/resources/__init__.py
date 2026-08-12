"""
PyDABs integration for databricks-dbt-factory.

At ``databricks bundle deploy`` time the Databricks CLI calls :func:`load_resources`, which
reads the dbt manifest and expands it into a Databricks job with one task per dbt object
(model / seed / snapshot / test) using the vendored ``databricks_dbt_factory`` core. No
per-model YAML is generated or checked in — the job graph is built on the fly from the manifest.

This module is the only integration glue: it configures the vendored ``databricks_dbt_factory``
core (under ``src/databricks_dbt_factory``) for serverless notebook tasks and returns a
``Resources`` object for PyDABs.
"""

import os
from importlib.metadata import PackageNotFoundError, version

import yaml
from databricks.bundles.core import Bundle, Resources
from databricks.bundles.jobs import Job

from databricks_dbt_factory.DbtFactory import DbtFactory
from databricks_dbt_factory.DbtTask import DbtTaskOptions, TaskType
from databricks_dbt_factory.TaskFactory import (
    DbtDependencyResolver,
    ModelTaskFactory,
    SnapshotTaskFactory,
    SeedTaskFactory,
    TestTaskFactory,
)
from databricks_dbt_factory.Utils import read_dbt_manifest

# --- Configuration -------------------------------------------------------------------------

# Path to the dbt manifest, read at deploy time. Regenerate with `make manifest` (dbt parse).
# Override the location without editing this file via the DBT_MANIFEST_PATH env var.
MANIFEST_PATH = os.environ.get("DBT_MANIFEST_PATH", "target/manifest.json")

# Name of the generated Databricks job.
JOB_NAME = "dbt_factory_job"

# Key of the serverless environment (defined on the job below).
ENVIRONMENT_KEY = "Default"

# Bundle single-model tests per resource into one `dbt test` task (fewer task startups,
# faster end-to-end runtime for projects with many tests). See the databricks-dbt-factory
# README "DBT Tests handling" section for the trade-offs.
BUNDLE_TESTS = False

# Extra options appended to every generated dbt command (e.g. "--full-refresh"). Empty by default.
# Selection options (`--select`, `--exclude`, ...) and parse-context options (`--vars`, `--target`,
# `--profiles-dir`, `--project-dir`) are rejected: the factory owns selection and the runtime parse
# context must match the supplied manifest.
EXTRA_DBT_COMMAND_OPTIONS = ""

# Serverless base-environment file, generated at deploy time from the pinned
# dbt-databricks version and synced with the bundle. The generated job points its
# serverless environment at this file (see build_job) so Databricks pre-builds the
# environment once instead of installing dbt on every task. `${workspace.file_path}`
# is substituted by the CLI at deploy time to the bundle's synced files root.
SERVERLESS_ENV_FILE = "dbt_serverless_env.yaml"
SERVERLESS_ENV_PATH = "${workspace.file_path}/" + SERVERLESS_ENV_FILE

# The runner notebook shipped with the core, referenced in place (path relative to the bundle
# root). `PROJECT_DIRECTORY` is the path from the notebook's own directory back up to the dbt
# project root (== bundle root), where the runner changes directory to before running dbt. It is
# derived from the notebook path so the two stay consistent if the layout ever changes.
RUNNER_NOTEBOOK_PATH = "src/databricks_dbt_factory/notebook/run_dbt_command.py"
PROJECT_DIRECTORY = os.path.relpath(".", os.path.dirname(RUNNER_NOTEBOOK_PATH))
PROFILES_DIRECTORY = "dbt_profiles"


def _build_tasks(target: str) -> list[dict]:
    """Reads the dbt manifest and returns the list of Databricks task dicts (one per dbt node)."""
    resolver = DbtDependencyResolver()
    task_options = DbtTaskOptions(
        environment_key=ENVIRONMENT_KEY,
        notebook_path=RUNNER_NOTEBOOK_PATH,
        project_directory=PROJECT_DIRECTORY,
        profiles_directory=PROFILES_DIRECTORY,
        task_type=TaskType.NOTEBOOK,
    )
    dbt_options = f"--target {target} {EXTRA_DBT_COMMAND_OPTIONS}".strip()

    task_factories = {
        "model": ModelTaskFactory(resolver, task_options, dbt_options),
        "snapshot": SnapshotTaskFactory(resolver, task_options, dbt_options),
        "seed": SeedTaskFactory(resolver, task_options, dbt_options),
        "test": TestTaskFactory(resolver, task_options, dbt_options),
    }

    factory = DbtFactory(task_factories, bundle_tests=BUNDLE_TESTS)
    manifest = read_dbt_manifest(MANIFEST_PATH)
    return factory.create_tasks(manifest)


def _dbt_databricks_dependency() -> str:
    """Pin the runtime to the exact dbt-databricks installed in this bundle's venv — the same
    version used to generate the manifest (`make manifest`) and to develop locally. pyproject.toml
    is therefore the single source of truth for the dbt version, and the version that runs in
    Databricks is guaranteed to match the one you tested with (no separate range that can drift).
    Local or dev builds (e.g. `1.9.0+custom`) are rejected: pip cannot resolve them from PyPI
    when Databricks builds the serverless environment, which would fail every task at runtime.
    """
    try:
        installed = version("dbt-databricks")
    except PackageNotFoundError as exc:
        raise RuntimeError(
            "dbt-databricks is not installed in the bundle venv — run `make setup` before deploying."
        ) from exc

    from packaging.version import InvalidVersion, Version

    try:
        parsed = Version(installed)
    except InvalidVersion:
        parsed = None
    if parsed is None or parsed.local or parsed.is_devrelease:
        raise RuntimeError(
            f"The installed dbt-databricks version ({installed}) is not a plain PyPI release, so the "
            "serverless environment cannot install it. Set a released version in pyproject.toml and "
            "re-run `make setup` before deploying."
        )
    return f"dbt-databricks=={installed}"


def _serverless_environment_spec() -> dict:
    """Contents of the base-environment file: the environment version plus the pinned
    dbt-databricks dependency."""
    return {"environment_version": "4", "dependencies": [_dbt_databricks_dependency()]}


def _write_serverless_environment_file() -> None:
    """Write the base-environment file to the bundle root so `bundle deploy` syncs it to the
    workspace, where the generated job references it via base_environment. The write is skipped
    when the file already has the desired content, so commands like `bundle validate` stay free
    of side effects once the file exists."""
    content = yaml.safe_dump(_serverless_environment_spec(), sort_keys=False)
    try:
        with open(SERVERLESS_ENV_FILE, "r", encoding="utf-8") as f:
            if f.read() == content:
                return
    except OSError:
        pass
    try:
        with open(SERVERLESS_ENV_FILE, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as exc:
        raise RuntimeError(
            f"Cannot write {SERVERLESS_ENV_FILE}, which the generated job needs as its serverless "
            f"base environment: {exc}"
        ) from exc


def build_job(target: str) -> Job:
    """Builds the Databricks job that runs the dbt project on serverless via notebook tasks."""
    return Job.from_dict(
        {
            "name": JOB_NAME,
            "queue": {"enabled": True},
            "trigger": {
                # Run this job every day, exactly one day from the last run;
                # see https://docs.databricks.com/api/workspace/jobs/create#trigger
                "periodic": {"interval": 1, "unit": "DAYS"},
            },
            "tasks": _build_tasks(target),
            "environments": [
                {
                    "environment_key": ENVIRONMENT_KEY,
                    # Pre-built base env (synced with the bundle), not inline deps —
                    # the two are mutually exclusive; the file pins dbt-databricks.
                    "spec": {"base_environment": SERVERLESS_ENV_PATH},
                }
            ],
        }
    )


def load_resources(bundle: Bundle) -> Resources:
    """
    Called by the Databricks CLI during `bundle deploy` to load resources defined in Python.

    Reads the dbt manifest, writes the serverless base-environment file (synced with the bundle),
    and registers the generated job. After deployment this function is not used.
    """
    _write_serverless_environment_file()
    resources = Resources()
    resources.add_job(JOB_NAME, build_job(bundle.target))
    return resources
