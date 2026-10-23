# Python pipeline with AUTO CDC (SCD Type 1 and Type 2)

This Declarative Automation Bundles example defines a serverless Python pipeline that uses `create_auto_cdc_flow`.
The pipeline applies a small change feed to an SCD Type 1 table and an SCD Type 2 table.
A job writes the change feed and then refreshes the pipeline.

For more information, see the [AUTO CDC documentation](https://docs.databricks.com/aws/en/ldp/cdc).

## Prerequisites

* Databricks CLI v1.20.0 or above
* A workspace with Unity Catalog and serverless compute.
* An existing catalog and schema for the tables and the `changes` volume.

## Usage

1. Set the catalog and the schema:

   ```sh
   export BUNDLE_VAR_catalog=<catalog>
   export BUNDLE_VAR_schema=<schema>
   ```

2. Deploy the bundle to dev: `databricks bundle deploy -t dev --profile <profile>`
3. Run the job: `databricks bundle run -t dev customers_cdc_job --profile <profile>`
4. Query the current rows: `SELECT * FROM <catalog>.<schema>.customers_scd1 ORDER BY id`
5. Query the history rows: `SELECT * FROM <catalog>.<schema>.customers_scd2 ORDER BY id, __START_AT`

   The late `Boston` update (seq 4) does not replace `Portland` (seq 5) in SCD Type 1.
   SCD Type 2 keeps it as a closed history row:

   ```
   id  name   city      __START_AT  __END_AT
   1   Alice  Seattle   1           4
   1   Alice  Boston    4           5
   1   Alice  Portland  5           null
   2   Bob    Austin    2           6
   3   Carol  Denver    3           7
   3   Carol  Miami     7           null
   ```

6. Recompute all tables: `databricks bundle run -t dev customers_cdc_job --params full_refresh=true --profile <profile>`
7. Deploy the bundle to prod: `databricks bundle deploy -t prod --profile <profile>`
8. Remove the dev resources: `databricks bundle destroy -t dev --profile <profile>`
9. Remove the prod resources: `databricks bundle destroy -t prod --profile <profile>`
10. Drop the tables: `DROP TABLE IF EXISTS <catalog>.<schema>.customers_scd1` and `DROP TABLE IF EXISTS <catalog>.<schema>.customers_scd2`

| Target | Pipeline mode |
| --- | --- |
| `dev` | Triggered (`continuous: false`) |
| `prod` | Continuous (`continuous: true`) |
