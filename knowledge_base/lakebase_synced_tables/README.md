# Lakebase synced tables

This Declarative Automation Bundles example syncs a Unity Catalog Delta table to Lakebase Postgres. Each target creates its own project, branch, endpoint, and synced table.

See the [Lakebase Autoscaling documentation](https://docs.databricks.com/aws/en/oltp/) for more information.

## Prerequisites

- Databricks CLI v1.20.0 or above.
- A workspace with Lakebase Autoscaling and serverless pipelines.
- A source Delta table with change data feed enabled and an `id` primary key column.
- A standard catalog and schema for pipeline storage.
- A new project ID. The bundle creates and purges its project during deployment and cleanup.

## Usage

1. Set a unique project ID and your Unity Catalog object names.

   ```sh
   export BUNDLE_VAR_project_id=my-synced-tables
   export BUNDLE_VAR_source_table=main.example.source_table
   export BUNDLE_VAR_destination_table=main.example.synced_source_table
   export BUNDLE_VAR_pipeline_storage_catalog=main
   export BUNDLE_VAR_pipeline_storage_schema=example
   ```

2. Validate the bundle.

   ```sh
   databricks bundle validate
   ```

3. Deploy the development project and synced table.

   ```sh
   databricks bundle deploy
   ```

4. Deploy the production project and synced table.

   ```sh
   databricks bundle deploy -t prod
   ```

5. Verify the development and production sync status.

   ```sh
   databricks postgres get-synced-table "synced_tables/${BUNDLE_VAR_destination_table}_dev"
   databricks postgres get-synced-table "synced_tables/${BUNDLE_VAR_destination_table}_prod"
   databricks psql --project "${BUNDLE_VAR_project_id}-dev" --branch production --endpoint primary -- -d databricks_postgres -c "SELECT count(*) FROM example.synced_source_table_dev;"
   ```

6. Remove the resources for each deployed target.

   ```sh
   databricks bundle destroy --auto-approve
   databricks bundle destroy -t prod --auto-approve
   ```
