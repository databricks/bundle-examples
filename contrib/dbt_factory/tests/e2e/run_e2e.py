"""
End-to-end test for the dbt-factory example.

It generates a fresh project from the ``dbt-factory`` template with the factory's default options,
points it at YOUR workspace, drops in the fixture dbt project next to this file, then **deploys the
factory-generated job, runs it, and verifies it succeeded** — before tearing everything down. This
is the check that a change to the factory won't break real dbt execution.

Run it with ``make test-e2e`` from the example root. Required environment:

    DATABRICKS_CONFIG_PROFILE   CLI profile for your workspace (auth + host).
    DBX_E2E_HTTP_PATH           SQL warehouse HTTP path, e.g. /sql/1.0/warehouses/<id>.
    DBX_E2E_CATALOG             Catalog to create the throwaway schema + tables in (write access).

Optional:
    DBX_E2E_SCHEMA_PREFIX       Schema-name prefix (default: dbt_factory_e2e). A unique
                                <prefix>_<timestamp> schema is created and dropped per run.

Nothing is left behind: the run destroys its bundle and drops its schema, pass or fail.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent
REPO_ROOT = FIXTURE_DIR.parents[3]
TEMPLATE_DIR = REPO_ROOT / "contrib" / "templates" / "dbt-factory"

PROJECT_NAME = "dbt_factory_e2e"

# Tables the fixture materializes, with the minimum row count that proves they actually ran.
EXPECTED_TABLES = {
    "customers": 5,
    "orders": 8,
    "customer_orders": 5,
    "customers_with_country": 5,
    "tpch_orders_summary": 1,
    "orders_snapshot": 8,
}


class Config:
    def __init__(self) -> None:
        self.profile = _require("DATABRICKS_CONFIG_PROFILE")
        self.http_path = _require("DBX_E2E_HTTP_PATH")
        self.catalog = _require("DBX_E2E_CATALOG")
        self.warehouse_id = self.http_path.rstrip("/").split("/")[-1]
        self.prefix = os.environ.get("DBX_E2E_SCHEMA_PREFIX", "dbt_factory_e2e")


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"ERROR: environment variable {name} is required (see the module docstring).")
    return value


def _run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    print(f"    $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(cmd)}")
    return result


def _sql(cfg: Config, statement: str, schema: str | None = None) -> list[list]:
    """Runs a SQL statement on the warehouse via the Statement Execution API; returns result rows."""
    body = {
        "warehouse_id": cfg.warehouse_id,
        "statement": statement,
        "catalog": cfg.catalog,
        "wait_timeout": "50s",
        "on_wait_timeout": "CANCEL",
    }
    if schema:
        body["schema"] = schema
    result = subprocess.run(
        ["databricks", "api", "post", "/api/2.0/sql/statements", "--json", json.dumps(body)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"SQL API call failed: {result.stderr.strip()}")
    payload = json.loads(result.stdout)
    state = payload.get("status", {}).get("state")
    if state != "SUCCEEDED":
        raise RuntimeError(f"SQL did not succeed ({state}): {statement}\n{json.dumps(payload.get('status', {}))}")
    return payload.get("result", {}).get("data_array", []) or []


def _init_project(cfg: Config, out_dir: Path, schema: str) -> Path:
    # Set only the values that point the project at this workspace. Everything else (test bundling,
    # environment key, extra dbt options) is left at the template's defaults — the factory's
    # out-of-the-box behavior, which is exactly what we want the e2e to exercise.
    config_file = out_dir / "init-config.json"
    config_file.write_text(
        json.dumps(
            {
                "project_name": PROJECT_NAME,
                "default_catalog": cfg.catalog,
                "dev_schema": schema,
                "http_path": cfg.http_path,
            }
        )
    )
    # Run `bundle init` from the neutral temp dir, NOT from inside the example bundle — otherwise the
    # CLI resolves auth against the example's placeholder host and refuses.
    _run(
        [
            "databricks",
            "bundle",
            "init",
            str(TEMPLATE_DIR),
            "--config-file",
            str(config_file),
            "--output-dir",
            str(out_dir),
        ],
        cwd=out_dir,
    )
    return out_dir / PROJECT_NAME


def _fill_fixture(project: Path) -> None:
    """Replace the starter models with the richer fixture dbt project next to this script."""
    src = project / "src"
    shutil.rmtree(src / "models" / "example", ignore_errors=True)
    for sub in ("models", "seeds", "snapshots", "tests"):
        for f in sorted((FIXTURE_DIR / sub).iterdir()):
            if f.is_file():
                shutil.copy2(f, src / sub / f.name)


def _assert_parse_cache_synced(project: Path) -> None:
    """Guard the parse-cache optimization: the git-ignored `target/partial_parse.msgpack` must reach
    the workspace (via `sync.include`) or every task silently full-parses instead of injecting it.
    A missing file here is the regression that the old `git add -f` opt-in caused. Tooling hiccups
    (summary/list) only warn; a file that is definitively absent fails the run."""
    summary = subprocess.run(
        ["databricks", "bundle", "summary", "--target", "dev", "-o", "json"],
        cwd=project,
        capture_output=True,
        text=True,
    )
    if summary.returncode != 0:
        print(f"      WARNING: bundle summary failed, skipping parse-cache check: {summary.stderr.strip()}")
        return
    try:
        file_path = json.loads(summary.stdout)["workspace"]["file_path"]
    except (json.JSONDecodeError, KeyError) as exc:
        print(f"      WARNING: could not read workspace.file_path, skipping parse-cache check: {exc}")
        return
    listing = subprocess.run(
        ["databricks", "workspace", "list", f"{file_path}/target", "-o", "json"],
        cwd=project,  # resolve auth against the rendered project's host, not the example bundle's
        capture_output=True,
        text=True,
    )
    if listing.returncode != 0:
        print(f"      WARNING: could not list {file_path}/target, skipping parse-cache check: {listing.stderr.strip()}")
        return
    names = {
        o.get("path", "").rsplit("/", 1)[-1] for o in (json.loads(listing.stdout) if listing.stdout.strip() else [])
    }
    if "partial_parse.msgpack" not in names:
        raise RuntimeError(f"partial_parse.msgpack not synced to {file_path}/target (found: {sorted(names)})")
    print(f"      parse cache synced: {file_path}/target/partial_parse.msgpack")


def _verify_output(cfg: Config, schema: str) -> list[str]:
    """Query each expected table's row count; return a list of failure messages (empty == all good)."""
    failures = []
    for table, minimum in EXPECTED_TABLES.items():
        rows = _sql(cfg, f"SELECT count(*) FROM {cfg.catalog}.{schema}.{table}", schema=schema)
        count = int(rows[0][0]) if rows and rows[0] else 0
        status = "ok" if count >= minimum else "TOO FEW"
        print(f"      {table:26} rows={count:<6} (expected >= {minimum})  {status}")
        if count < minimum:
            failures.append(f"{table}: {count} rows (< {minimum})")
    return failures


def run(cfg: Config) -> bool:
    schema = f"{cfg.prefix}_{time.strftime('%Y%m%d_%H%M%S')}"
    job = f"{PROJECT_NAME}_job"
    work = Path(tempfile.mkdtemp(prefix="dbtfactory_e2e_"))
    project = None
    print(f"\n===== dbt-factory e2e — schema {cfg.catalog}.{schema} =====")
    try:
        print("  [1/6] create throwaway schema")
        _sql(cfg, f"CREATE SCHEMA IF NOT EXISTS {cfg.catalog}.{schema}")
        print("  [2/6] init project from template + drop in fixture")
        project = _init_project(cfg, work, schema)
        _fill_fixture(project)
        print("  [3/6] install deps + generate dbt manifest")
        _run(["uv", "sync", "--dev"], cwd=project)
        _run(["uv", "run", "dbt", "parse", "--profiles-dir", "dbt_profiles"], cwd=project)
        print("  [4/6] deploy the factory-generated job")
        _run(["databricks", "bundle", "deploy", "--target", "dev"], cwd=project)
        _assert_parse_cache_synced(project)
        print("  [5/6] run the job (blocks; non-zero exit if any task fails)")
        run_result = _run(["databricks", "bundle", "run", job, "--target", "dev"], cwd=project, check=False)
        job_ok = run_result.returncode == 0
        print(f"      job result: {'SUCCESS' if job_ok else 'FAILED'}")
        print("  [6/6] verify output tables were materialized")
        failures = _verify_output(cfg, schema) if job_ok else ["job did not succeed; skipped table checks"]
        for f in failures:
            print(f"      FAIL: {f}")
        return job_ok and not failures
    except Exception as exc:  # noqa: BLE001 - surface any failure
        print(f"  ERROR: {exc}")
        return False
    finally:
        print("  cleanup: destroy bundle + drop schema")
        if project and project.exists():
            _run(["databricks", "bundle", "destroy", "--target", "dev", "--auto-approve"], cwd=project, check=False)
        try:
            _sql(cfg, f"DROP SCHEMA IF EXISTS {cfg.catalog}.{schema} CASCADE")
        except Exception as exc:  # noqa: BLE001
            print(f"    WARNING: could not drop schema {schema}: {exc}")
        shutil.rmtree(work, ignore_errors=True)


def main() -> None:
    passed = run(Config())
    print(f"\n===== e2e {'PASS' if passed else 'FAIL'} =====")
    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
