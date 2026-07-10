# Databricks notebook source

import json
import os
import shlex
import shutil
import tempfile

from dbt.cli.main import dbtRunner

# COMMAND ----------

dbutils.widgets.text("dbt_commands", "")
dbutils.widgets.text("project_directory", "")
dbutils.widgets.text("profiles_directory", "")

dbt_commands = dbutils.widgets.get("dbt_commands")
project_directory = dbutils.widgets.get("project_directory")
profiles_directory = dbutils.widgets.get("profiles_directory")

if not dbt_commands:
    raise ValueError("dbt_commands parameter is required")

# COMMAND ----------

ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
os.environ["DBT_ACCESS_TOKEN"] = ctx.apiToken().get()
# dbt's host must be a bare hostname; apiUrl() includes the https:// scheme.
os.environ["DBT_HOST"] = ctx.apiUrl().get().removeprefix("https://").removeprefix("http://")

if project_directory:
    notebook_dir = os.path.dirname("/Workspace" + ctx.notebookPath().get())
    target_dir = (
        project_directory
        if os.path.isabs(project_directory)
        else os.path.normpath(os.path.join(notebook_dir, project_directory))
    )
    os.chdir(target_dir)

local_dir = tempfile.mkdtemp(prefix="dbt_local_")
os.environ["DBT_TARGET_PATH"] = local_dir
os.environ["DBT_LOG_PATH"] = local_dir

manifest = None
prebuilt_manifest_path = os.path.join("target", "partial_parse.msgpack")
if os.path.exists(prebuilt_manifest_path):
    try:
        from dbt.contracts.graph.manifest import Manifest

        with open(prebuilt_manifest_path, "rb") as f:
            manifest = Manifest.from_msgpack(f.read())
        manifest.build_flat_graph()
        print(f"[dbt-factory] injecting pre-built manifest from {prebuilt_manifest_path} (skipping dbt parse)")
    except Exception as e:
        print(f"[dbt-factory] manifest injection unavailable, falling back to dbt parse: {e}")
        manifest = None

try:
    runner = dbtRunner(manifest=manifest)

    for command_str in json.loads(dbt_commands):
        command_str = command_str.strip()
        if not command_str:
            continue

        if command_str.startswith("dbt "):
            command_str = command_str[4:]

        args = shlex.split(command_str)

        if profiles_directory:
            args.extend(["--profiles-dir", profiles_directory])

        print(f"Running: dbt {' '.join(args)}")

        result = runner.invoke(args)

        if not result.success:
            detail = result.exception or result.result or "(no further details)"
            raise RuntimeError(f"dbt command failed: dbt {' '.join(args)}\n{detail}")
finally:
    os.environ.pop("DBT_ACCESS_TOKEN", None)
    os.environ.pop("DBT_HOST", None)
    os.environ.pop("DBT_TARGET_PATH", None)
    os.environ.pop("DBT_LOG_PATH", None)
    if local_dir:
        shutil.rmtree(local_dir, ignore_errors=True)
