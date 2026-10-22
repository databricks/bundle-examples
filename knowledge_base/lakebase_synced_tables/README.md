# Lakebase synced tables

This Declarative Automation Bundles example syncs a Unity Catalog Delta table to Lakebase Postgres. It also creates a target-specific branch, endpoint, and disabled snapshot schedule.

The `postgres_*` resources use Lakebase Autoscaling. Legacy `database_instances` resources configure Lakebase Provisioned.

See the [Lakebase Autoscaling documentation](https://docs.databricks.com/aws/en/oltp/) for more information.

## Prerequisites

- Databricks CLI v1.20.0 or above.
- A workspace with Lakebase Autoscaling and serverless pipelines.
- A source Delta table with an `id` primary key column.
- A standard catalog and schema for pipeline storage.

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

3. Deploy the development branch, endpoint, schedule, and synced table.

   ```sh
   databricks bundle deploy
   ```

4. Deploy the production target when required.

   ```sh
   databricks bundle deploy -t prod
   ```

5. Remove the resources for each deployed target.

   ```sh
   databricks bundle destroy --auto-approve
   databricks bundle destroy -t prod --auto-approve
   ```
