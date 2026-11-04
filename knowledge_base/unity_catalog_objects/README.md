# Unity Catalog objects

This Declarative Automation Bundles example creates a managed Unity Catalog catalog, schema, and volume with grants.
A serverless job writes a marker file into the volume.
See the [catalog resource documentation](https://docs.databricks.com/dev-tools/bundles/resources.html#catalogs).

## Prerequisites

* Databricks CLI v1.20.0 or above
* A workspace with Unity Catalog and serverless jobs
* Permission to create catalogs in the metastore
* A cloud storage root URL for the catalog when the metastore has no default root

## Usage

1. Set the catalog storage root: `export BUNDLE_VAR_catalog_storage_root=abfss://container@storageaccount.dfs.core.windows.net/`
2. Validate the development target: `databricks bundle validate -t dev --profile <profile>`
3. Deploy the development target: `databricks bundle deploy -t dev --profile <profile>`
4. Run the write job: `databricks bundle run -t dev write_marker --profile <profile>`
5. Check catalog grants: `databricks grants get catalog <catalog_name> --profile <profile>`
6. In `resources/data.schema.yml`, set `lifecycle.prevent_destroy` to `false`.
7. Remove the development deployment: `databricks bundle destroy -t dev --auto-approve --profile <profile>`
8. Deploy the production target: `databricks bundle deploy -t prod --profile <profile>`
9. Remove the production deployment after the same `prevent_destroy` steps: `databricks bundle destroy -t prod --auto-approve --profile <profile>`

| Resource | Purpose |
| --- | --- |
| `catalogs.uc_demo` | Managed catalog with grants |
| `schemas.data` | Schema with `lifecycle.prevent_destroy` |
| `volumes.landing` | Managed volume for the marker file |
| `jobs.write_marker` | Serverless job that proves volume access |
