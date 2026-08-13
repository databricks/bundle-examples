# End-to-end test

`make test-e2e` (from the example root) is the check that a change to the factory won't break real dbt
execution. It generates a fresh project from the [`dbt-factory` template](../../../templates/dbt-factory)
with the factory's default options, points it at **your** Databricks workspace, drops in the fixture
dbt project in this directory, then **deploys the factory-generated job, runs it, verifies the
output, and tears everything down**. Every run destroys its bundle and drops its schema, pass or
fail, so nothing is left behind.

Unlike `make test` (fast, offline unit tests), this one deploys and runs on a real workspace — so
it's not a CI gate; run it locally before merging a change to the factory.

## Prerequisites

- A Databricks CLI profile for your workspace: `databricks auth login --host <your-workspace-url>`.
- A SQL warehouse, and a catalog you can create schemas/tables in.

## Run it

```
DATABRICKS_CONFIG_PROFILE=<profile> \
DBT_FACTORY_HTTP_PATH=/sql/1.0/warehouses/<warehouse-id> \
DBT_FACTORY_CATALOG=<writable-catalog> \
make test-e2e
```

Optional: `DBT_FACTORY_SCHEMA_PREFIX` (default `dbt_factory_e2e`; a unique `<prefix>_<timestamp>` schema
is created and dropped each run).

`make test-e2e` does not read `DBT_FACTORY_SCHEMA` — it injects the per-run `<prefix>_<timestamp>`
schema into the generated project via `dev_schema`. `DBT_FACTORY_SCHEMA` only applies when you run
`dbt` in this directory directly (see [Parsing the fixture offline](#parsing-the-fixture-offline)).

## The fixture

The dbt project here covers every resource type the factory handles — models, a seed, a snapshot, a
`samples.tpch` source, schema tests (including a `severity: warn` test and a cross-model
`relationships` test), and a singular test — so a green run exercises the tricky gating/bundling
paths, not just the happy path. It reads only the ubiquitous `samples` catalog plus its own seed, so
it runs in any workspace.

## Parsing the fixture offline

The `dbt_project.yml` and `profiles.yml` in this directory let you run dbt against the fixture on
its own — handy for a quick `dbt parse`/`dbt compile` while editing the models, without generating a
project. `make test-e2e` does not use them (it renders the template and runs dbt inside the generated
project). The profile reads its connection from env vars, all with offline-safe defaults:

```
DBT_FACTORY_HTTP_PATH   SQL warehouse HTTP path (default: a placeholder; fine for `dbt parse`).
DBT_FACTORY_CATALOG     Catalog to read/write (default: main).
DBT_FACTORY_SCHEMA      Schema to read/write (default: default).
```

```
cd tests/e2e
uv run dbt parse   # reads project files only; no workspace needed
```
