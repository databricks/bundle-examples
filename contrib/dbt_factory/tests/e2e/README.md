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
DBX_E2E_HTTP_PATH=/sql/1.0/warehouses/<warehouse-id> \
DBX_E2E_CATALOG=<writable-catalog> \
make test-e2e
```

Optional: `DBX_E2E_SCHEMA_PREFIX` (default `dbt_factory_e2e`; a unique `<prefix>_<timestamp>` schema
is created and dropped each run).

## The fixture

The dbt project here covers every resource type the factory handles — models, a seed, a snapshot, a
`samples.tpch` source, schema tests (including a `severity: warn` test and a cross-model
`relationships` test), and a singular test — so a green run exercises the tricky gating/bundling
paths, not just the happy path. It reads only the ubiquitous `samples` catalog plus its own seed, so
it runs in any workspace.
