# Lakebase database project with a catalog

This Declarative Automation Bundles example demonstrates how to define a Lakebase Autoscaling database project and a Unity Catalog catalog backed by it.

It includes and deploys an example project and a catalog. When data changes in the project's Postgres database, it is reflected in Unity Catalog.

For more information about Lakebase, see the [documentation](https://docs.databricks.com/aws/en/oltp/).
For more information about managing Lakebase with bundles, see the [documentation](https://docs.databricks.com/aws/en/oltp/projects/manage-with-bundles).

## Prerequisites

* Databricks CLI v1.0.0 or above
* `psql` client version 14 or above (only needed to run the demo data generation)

## Usage

Modify `databricks.yml`:
* Update the `host` field under `workspace` to the Databricks workspace to deploy to

Run `databricks bundle deploy` to deploy the bundle.

Please note that after this bundle is deployed, the Lakebase project is created and incurs cost while running. Lakebase Autoscaling scales its compute down to zero when idle.

Run the following queries to populate your database with sample data:

```bash
# Create a demo table:
databricks psql --project my-project -- -d my_database -c "CREATE TABLE IF NOT EXISTS hello_world (id SERIAL PRIMARY KEY, message TEXT, number INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"

# Insert 100 rows of demo data:
databricks psql --project my-project -- -d my_database -c "INSERT INTO hello_world (message, number) SELECT 'Hello World #' || generate_series, generate_series FROM generate_series(1, 100);"

# Show generated rows:
databricks psql --project my-project -- -d my_database -c "SELECT * FROM hello_world;"
```

Open your catalog in Databricks: `databricks bundle open my_catalog`
Navigate to the `public` schema, then to the `hello_world` table, then to "Sample data" and explore your generated data.

## Clean up
To remove the project and catalog run `databricks bundle destroy`