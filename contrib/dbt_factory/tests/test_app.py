import os
from tempfile import NamedTemporaryFile
from pathlib import Path
import pytest
import yaml

from databricks_dbt_factory.main import main, parse_args

BASE_PATH = str(Path(__file__).resolve().parent)


def test_main_given_default_args(monkeypatch):
    """Test the main function for job spec generation."""
    dbt_manifest_path = BASE_PATH + "/test_data/manifest.json"
    input_job_spec_path = BASE_PATH + "/test_data/job_definition_template.yaml"
    expected_job_definition_path = BASE_PATH + "/test_data/job_definition_default.yaml"

    with NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        target_job_spec_path = temp_file.name

    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "--dbt-manifest-path",
            dbt_manifest_path,
            "--input-job-spec-path",
            input_job_spec_path,
            "--target-job-spec-path",
            target_job_spec_path,
        ],
    )

    try:
        main()

        with open(expected_job_definition_path, "r", encoding="utf-8") as file:
            expected_job_definition = yaml.safe_load(file)

        with open(target_job_spec_path, "r", encoding="utf-8") as file:
            job_definition = yaml.safe_load(file)

        assert job_definition == expected_job_definition
    finally:
        if os.path.exists(target_job_spec_path):
            os.remove(target_job_spec_path)


def test_main_notebook_mode_auto_copies_runner_notebook_next_to_spec(monkeypatch, tmp_path):
    """Without --project-directory, the factory copies the runner notebook next to the
    generated job spec and emits `notebook_path: ./run_dbt_command.py`."""
    target_job_spec_path = tmp_path / "job_definition.yaml"

    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "--dbt-manifest-path",
            BASE_PATH + "/test_data/manifest.json",
            "--input-job-spec-path",
            BASE_PATH + "/test_data/job_definition_template.yaml",
            "--target-job-spec-path",
            str(target_job_spec_path),
            "--task-type",
            "notebook",
        ],
    )

    main()

    copied_notebook = tmp_path / "run_dbt_command.py"
    assert copied_notebook.exists(), "runner notebook should have been copied next to the job spec"
    assert "dbtRunner" in copied_notebook.read_text(), "copied file should be the packaged runner"

    with open(target_job_spec_path, "r", encoding="utf-8") as file:
        job_definition = yaml.safe_load(file)

    tasks = job_definition["resources"]["jobs"]["dbt_sql_job"]["tasks"]
    for task in tasks:
        assert task["notebook_task"]["notebook_path"] == "./run_dbt_command.py"


def test_main_notebook_mode_auto_copies_runner_notebook_to_project_root(monkeypatch, tmp_path):
    """With a relative --project-directory (e.g. `../`), the factory copies the runner to
    the computed project root and emits a matching relative notebook_path from the spec."""
    spec_dir = tmp_path / "resources"
    spec_dir.mkdir()
    target_job_spec_path = spec_dir / "job_definition.yaml"

    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "--dbt-manifest-path",
            BASE_PATH + "/test_data/manifest.json",
            "--input-job-spec-path",
            BASE_PATH + "/test_data/job_definition_template.yaml",
            "--target-job-spec-path",
            str(target_job_spec_path),
            "--task-type",
            "notebook",
            "--project-directory",
            "../",
        ],
    )

    main()

    copied_notebook = tmp_path / "run_dbt_command.py"
    assert copied_notebook.exists(), "runner should have been copied to the project root (one level up from the spec)"
    assert not (spec_dir / "run_dbt_command.py").exists(), "runner should NOT be copied next to the spec in this case"

    with open(target_job_spec_path, "r", encoding="utf-8") as file:
        job_definition = yaml.safe_load(file)

    tasks = job_definition["resources"]["jobs"]["dbt_sql_job"]["tasks"]
    for task in tasks:
        assert task["notebook_task"]["notebook_path"] == "../run_dbt_command.py"
        # With the runner at project root, CWD at runtime = project root. We explicitly
        # pin project_directory to "." so the spec is self-documenting (the user's original
        # "../" would resolve one level too high and has been rewritten).
        assert task["notebook_task"]["base_parameters"]["project_directory"] == "."


def test_main_notebook_mode(monkeypatch):
    """Test the main function for notebook task type generation."""
    dbt_manifest_path = BASE_PATH + "/test_data/manifest.json"
    input_job_spec_path = BASE_PATH + "/test_data/job_definition_template.yaml"
    expected_job_definition_path = BASE_PATH + "/test_data/job_definition_notebook_default.yaml"

    with NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        target_job_spec_path = temp_file.name

    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "--dbt-manifest-path",
            dbt_manifest_path,
            "--input-job-spec-path",
            input_job_spec_path,
            "--target-job-spec-path",
            target_job_spec_path,
            "--task-type",
            "notebook",
            "--notebook-path",
            "./notebooks/dbt_runner.py",
        ],
    )

    try:
        main()

        with open(expected_job_definition_path, "r", encoding="utf-8") as file:
            expected_job_definition = yaml.safe_load(file)

        with open(target_job_spec_path, "r", encoding="utf-8") as file:
            job_definition = yaml.safe_load(file)

        assert job_definition == expected_job_definition
    finally:
        if os.path.exists(target_job_spec_path):
            os.remove(target_job_spec_path)


def test_main_all_args(monkeypatch):
    """Test the main function for job spec generation."""
    dbt_manifest_path = BASE_PATH + "/test_data/manifest.json"
    input_job_spec_path = BASE_PATH + "/test_data/job_definition_template.yaml"
    expected_job_definition_path = BASE_PATH + "/test_data/job_definition_deps_selected.yaml"

    with NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        target_job_spec_path = temp_file.name

    new_job_name = "test_job"
    warehouse_id = "1234567890abcdef"
    schema = "dqx_test"
    catalog = "main"
    profiles_dir = "profiles_dir"
    project_dir = "/project_dir"
    extra_dbt_command_options = '"--upgrade"'

    # Mock command-line arguments
    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "--new-job-name",
            new_job_name,
            "--dbt-manifest-path",
            dbt_manifest_path,
            "--input-job-spec-path",
            input_job_spec_path,
            "--target-job-spec-path",
            target_job_spec_path,
            "--target",
            "dev",
            "--environment-key",
            "Default",
            "--source",
            "GIT",
            "--enable-dbt-deps",
            "--dbt-tasks-deps",
            "diamonds_prices,second_dbt_model",
            "--warehouse_id",
            warehouse_id,
            "--schema",
            schema,
            "--catalog",
            catalog,
            "--profiles-directory",
            profiles_dir,
            "--project-directory",
            project_dir,
            "--extra-dbt-command-options",
            extra_dbt_command_options,
        ],
    )

    try:
        main()

        with open(expected_job_definition_path, "r", encoding="utf-8") as file:
            expected_job_definition = yaml.safe_load(file)

        with open(target_job_spec_path, "r", encoding="utf-8") as file:
            job_definition = yaml.safe_load(file)

        expected_job_definition = update_spec(
            expected_job_definition,
            new_job_name,
            warehouse_id,
            schema,
            catalog,
            profiles_dir,
            project_dir,
            extra_dbt_command_options,
        )

        assert job_definition == expected_job_definition
    finally:
        if os.path.exists(target_job_spec_path):
            os.remove(target_job_spec_path)


REQUIRED_ARGS = [
    "--dbt-manifest-path",
    "manifest.json",
    "--input-job-spec-path",
    "in.yaml",
    "--target-job-spec-path",
    "out.yaml",
]


def test_explicit_environment_key_with_job_cluster_key_is_rejected(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["main.py", *REQUIRED_ARGS, "--job-cluster-key", "foo", "--environment-key", "Default"],
    )
    with pytest.raises(SystemExit):
        parse_args()


def test_job_cluster_key_alone_parses(monkeypatch):
    monkeypatch.setattr("sys.argv", ["main.py", *REQUIRED_ARGS, "--job-cluster-key", "foo"])
    args = parse_args()
    assert args.job_cluster_key == "foo"
    assert args.environment_key is None


def test_environment_key_alone_parses(monkeypatch):
    monkeypatch.setattr("sys.argv", ["main.py", *REQUIRED_ARGS, "--environment-key", "Default"])
    args = parse_args()
    assert args.environment_key == "Default"
    assert args.job_cluster_key is None


def test_boolean_flags_default(monkeypatch):
    monkeypatch.setattr("sys.argv", ["main.py", *REQUIRED_ARGS])
    args = parse_args()
    assert args.run_tests is True  # tests enabled by default
    assert args.bundle_tests is False
    assert args.enable_dbt_deps is False
    assert args.dry_run is False


def test_boolean_flags_toggled(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            *REQUIRED_ARGS,
            "--no-run-tests",
            "--bundle-tests",
            "--enable-dbt-deps",
            "--dry-run",
        ],
    )
    args = parse_args()
    assert args.run_tests is False
    assert args.bundle_tests is True
    assert args.enable_dbt_deps is True
    assert args.dry_run is True


def test_notebook_task_type_with_warehouse_id_is_rejected(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            *REQUIRED_ARGS,
            "--task-type",
            "notebook",
            "--notebook-path",
            "/n",
            "--warehouse_id",
            "wh123",
        ],
    )
    with pytest.raises(SystemExit):
        parse_args()


def remove_target_from_spec(expected_job_definition):
    """Remove 'target' key from dbt_task in the expected job definition."""
    spec = dict(expected_job_definition)

    for task in expected_job_definition["resources"]["jobs"]["dbt_sql_job"]["tasks"]:
        if "dbt_task" in task:
            task["dbt_task"].pop("source", None)

    return spec


def update_spec(
    expected_spec: dict,
    new_job_name: str,
    warehouse_id: str,
    schema: str,
    catalog: str,
    profiles_dir: str,
    project_dir: str,
    extra_dbt_command_options: str,
) -> dict:
    """Update the job specification with new parameters."""
    spec = dict(expected_spec)

    # Update job name
    spec["resources"]["jobs"][new_job_name] = spec["resources"]["jobs"].pop("dbt_sql_job")
    spec["resources"]["jobs"][new_job_name]["name"] = new_job_name

    # Add warehouse_id under dbt_task
    for task in spec["resources"]["jobs"][new_job_name]["tasks"]:
        if "dbt_task" in task:
            task["dbt_task"]["schema"] = schema
            task["dbt_task"]["catalog"] = catalog
            task["dbt_task"]["warehouse_id"] = warehouse_id
            task["dbt_task"]["project_directory"] = project_dir
            task["dbt_task"]["profiles_directory"] = profiles_dir

        # Update commands with extra dbt command options
        updated_commands = []
        for command in task["dbt_task"]["commands"]:
            if "--target dev" in command:
                command = command.replace("--target dev", f"--target dev {extra_dbt_command_options}")
            updated_commands.append(command)
        task["dbt_task"]["commands"] = updated_commands

    return spec
