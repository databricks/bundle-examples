import argparse
import os
import shutil
from importlib import resources
from pathlib import Path

from databricks_dbt_factory.DbtFactory import DbtFactory
from databricks_dbt_factory.SpecsHandler import SpecsHandler
from databricks_dbt_factory.DbtTask import DbtTaskOptions
from databricks_dbt_factory.TaskFactory import (
    ModelTaskFactory,
    SnapshotTaskFactory,
    SeedTaskFactory,
    TestTaskFactory,
    DbtDependencyResolver,
)

_RUNNER_NOTEBOOK_FILENAME = "run_dbt_command.py"


def main():
    args = parse_args()

    file_handler = SpecsHandler()
    resolver = DbtDependencyResolver()

    dbt_options = build_dbt_options(args)
    dbt_tasks_deps = (
        [item.strip() for item in args.dbt_tasks_deps.split(",") if item.strip()] if args.dbt_tasks_deps else []
    )

    notebook_path = args.notebook_path
    effective_project_directory = args.project_directory
    if args.task_type == "notebook" and notebook_path is None:
        notebook_path, notebook_at_project_root = _copy_runner_notebook(
            args.target_job_spec_path, args.project_directory
        )
        # If the runner landed at the project root, CWD at task runtime already equals the
        # project root. Pass `.` explicitly so the generated spec is self-documenting (and
        # immune to any future change in dbt's default); the user's original `../` would
        # resolve one level too high and is no longer correct.
        if notebook_at_project_root:
            effective_project_directory = "."

    task_options = DbtTaskOptions(
        environment_key=args.environment_key if args.environment_key is not None else "Default",
        warehouse_id=args.warehouse_id,
        catalog=args.catalog,
        schema=args.schema,
        profiles_directory=args.profiles_directory,
        project_directory=effective_project_directory,
        source=args.source,
        dbt_deps_enabled=args.enable_dbt_deps,
        dbt_tasks_deps=dbt_tasks_deps,
        task_type=args.task_type,
        notebook_path=notebook_path,
        job_cluster_key=args.job_cluster_key,
    )
    task_factories = {
        "model": ModelTaskFactory(resolver, task_options, dbt_options),
        "snapshot": SnapshotTaskFactory(resolver, task_options, dbt_options),
        "seed": SeedTaskFactory(resolver, task_options, dbt_options),
    }
    if args.run_tests:
        task_factories["test"] = TestTaskFactory(resolver, task_options, dbt_options)

    factory = DbtFactory(file_handler, task_factories, bundle_tests=args.bundle_tests)
    factory.create_tasks_and_update_job_spec(
        args.dbt_manifest_path, args.input_job_spec_path, args.target_job_spec_path, args.new_job_name, args.dry_run
    )


def _copy_runner_notebook(target_job_spec_path: str, project_directory: str | None) -> tuple[str, bool]:
    """
    Copies the packaged dbt runner notebook into the bundle so `databricks bundle deploy`
    uploads it automatically.

    When `project_directory` is a relative path (the common case, e.g. `../` when the spec
    lives in a subdirectory), the notebook is placed at the computed project root. This way
    the notebook sits next to `dbt_project.yml` / `profiles.yml`, and at task runtime CWD =
    project root — dbt finds everything without any path gymnastics in the runner.

    When `project_directory` is absolute (typical for `--source WORKSPACE` with a pinned
    workspace path we can't write to from local CLI) or missing, falls back to copying the
    notebook next to the generated job spec.

    Returns `(notebook_path, notebook_at_project_root)`:
    - `notebook_path`: relative path from the spec's directory to the copied notebook,
      which DAB resolves at deploy time.
    - `notebook_at_project_root`: True when the runner landed at the computed project root
      (so the caller knows CWD = project root at runtime and can drop `--project-dir`).

    Overwrites any existing file at the destination.
    """
    source = resources.files("databricks_dbt_factory") / "notebook" / _RUNNER_NOTEBOOK_FILENAME
    spec_dir = Path(target_job_spec_path).resolve().parent

    if project_directory and not Path(project_directory).is_absolute():
        notebook_at_project_root = True
        dest_dir = (spec_dir / project_directory).resolve()
    else:
        notebook_at_project_root = False
        dest_dir = spec_dir

    dest = dest_dir / _RUNNER_NOTEBOOK_FILENAME
    dest_dir.mkdir(parents=True, exist_ok=True)
    with resources.as_file(source) as src_path:
        shutil.copyfile(src_path, dest)

    relative = Path(os.path.relpath(dest, start=spec_dir)).as_posix()
    notebook_path = relative if relative.startswith("..") else f"./{relative}"
    return notebook_path, notebook_at_project_root


def build_dbt_options(args):
    """Builds the dbt command options based on the provided arguments."""
    dbt_options = ""

    if args.target:
        dbt_options += f"--target {args.target}"

    if args.extra_dbt_command_options:
        dbt_options += f" {args.extra_dbt_command_options}"

    return dbt_options


def parse_args():
    parser = argparse.ArgumentParser(description="Generate Databricks job definition from dbt manifest.")
    parser.add_argument(
        "--new-job-name",
        type=str,
        help="Optional job name. If provided the existing job name in job spec is updated",
        required=False,
        default=None,
    )
    parser.add_argument("--dbt-manifest-path", type=str, help="Path to the manifest file", required=True)
    parser.add_argument("--input-job-spec-path", type=str, help="Path to the input job spec file", required=True)
    parser.add_argument(
        "--target-job-spec-path",
        type=str,
        help="Path to the target job spec file.",
        required=True,
    )
    parser.add_argument("--target", type=str, help="Optional dbt target to use.", required=False)
    parser.add_argument(
        "--source",
        type=str,
        help="Optional project source. If not provided WORKSPACE will be used.",
        required=False,
        default=None,
    )
    parser.add_argument(
        "--warehouse_id", type=str, help="Optional SQL Warehouse to run dbt models on", required=False, default=None
    )
    parser.add_argument("--schema", type=str, help="Optional schema to write to.", required=False, default=None)
    parser.add_argument("--catalog", type=str, help="Optional catalog to write to.", required=False, default=None)
    parser.add_argument(
        "--profiles-directory",
        type=str,
        help="Optional (relative) path to the profiles directory.",
        required=False,
        default=None,
    )
    parser.add_argument(
        "--project-directory",
        type=str,
        help="Optional (relative) path to the project directory.",
        required=False,
        default=None,
    )
    parser.add_argument(
        "--environment-key",
        type=str,
        help="Optional (relative) key of an environment. Defaults to 'Default' when unset.",
        required=False,
        default=None,
    )
    parser.add_argument(
        "--extra-dbt-command-options",
        type=str,
        help="Optional additional dbt command options",
        required=False,
        default="",
    )
    parser.add_argument(
        "--no-run-tests",
        action="store_false",
        dest="run_tests",
        help="Skip generating dbt test tasks. Tests are included by default.",
    )
    parser.add_argument(
        "--bundle-tests",
        action="store_true",
        help=(
            "Bundle single-model tests for a given resource into one "
            "`dbt test --select <pkg>.<resource> --indirect-selection cautious` task (default: "
            "one task per test node). Cross-model tests (e.g. `relationships`) are detected "
            "from the manifest and emitted as their own tasks gated on every referenced "
            "resource, so no tests are silently dropped. Trade-off: fewer tasks and a smaller "
            "DAG, but per-test failures show up as a single red `<resource>_tests` task — drill "
            "into the logs to see which assertion failed."
        ),
    )
    parser.add_argument(
        "--enable-dbt-deps",
        action="store_true",
        help="Run `dbt deps` before each task.",
    )
    parser.add_argument(
        "--dbt-tasks-deps",
        type=str,
        help="Optional list of tasks that require dbt deps. Only in effect if `--enable-dbt-deps` is enabled.",
        required=False,
        default=None,
    )
    parser.add_argument(
        "--task-type",
        type=str,
        help="Task type to generate: 'dbt' for native dbt_task (default), 'notebook' for notebook_task wrapper.",
        required=False,
        default="dbt",
        choices=["dbt", "notebook"],
    )
    parser.add_argument(
        "--notebook-path",
        type=str,
        help=(
            "Path to the dbt runner notebook (used when --task-type is 'notebook'). If omitted, "
            "the factory copies the packaged runner notebook next to the generated job spec and "
            "references it relatively, so `databricks bundle deploy` uploads it automatically. "
            "Pass an explicit path to pin the notebook elsewhere and manage it yourself."
        ),
        required=False,
        default=None,
    )
    parser.add_argument(
        "--job-cluster-key",
        type=str,
        help="Job cluster key for running tasks on job compute instead of serverless. Mutually exclusive with --environment-key.",
        required=False,
        default=None,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated tasks without updating the job spec file.",
    )
    args = parser.parse_args()

    if args.job_cluster_key and args.environment_key is not None:
        parser.error("--job-cluster-key and --environment-key are mutually exclusive")

    if args.task_type == "notebook":
        conflicting = []
        for flag, value in (
            ("--warehouse_id", args.warehouse_id),
            ("--schema", args.schema),
            ("--catalog", args.catalog),
        ):
            if value:
                conflicting.append(flag)
        if conflicting:
            parser.error(
                f"{', '.join(conflicting)} cannot be used with --task-type notebook; "
                "notebook tasks connect via profiles.yml."
            )

    return args


if __name__ == "__main__":
    main()
