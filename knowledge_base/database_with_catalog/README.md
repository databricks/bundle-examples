# OLTP database instance with a catalog

This example demonstrates how to define an OLTP database instance and a database catalog in a Databricks Asset Bundle.

It includes and deploys an example database instance and a catalog. When the instance is making changes to the database, the changes are reflected in Unity Catalog.

For more information about Databricks database instances, see the [documentation](https://docs.databricks.com/aws/en/oltp/).

## Prerequisites

* Databricks CLI v0.265.0 or above
* `psql` client version 14 or above (only needed to run the demo data generation)

## Usage

Modify `databricks.yml`:
* Update the `host` field under `workspace` to the Databricks workspace to deploy to

Run `databricks bundle deploy` to deploy the bundle.

Run the following queries to populate your database with sample data:

- `databricks psql my-instance -- -d my_database -c "CREATE TABLE IF NOT EXISTS hello_world (id SERIAL PRIMARY KEY, message TEXT, number INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"`
- `databricks psql my-instance -- -d my_database -c "INSERT INTO hello_world (message, number) SELECT 'Hello World #' || generate_series, generate_series FROM generate_series(1, 100);"`
- `databricks psql my-instance -- -d my_database -c "SELECT * FROM hello_world;"`

Open your catalog in Databricks Workspace to explore generated data in Unity Catalog: `databricks bundle open my_catalog`
Navigate to `public` schema, then to `hello_world` table, then to "Sample data"
