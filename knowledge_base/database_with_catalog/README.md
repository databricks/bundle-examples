# OLTP database instance with a catalog

This example demonstrates how to define an OLTP database instance and a database catalog in a Databricks Asset Bundle.

It includes and deploys an example database instance and a catalog. When data changes in the database instance, they are reflected in Unity Catalog.

For more information about Databricks database instances, see the [documentation](https://docs.databricks.com/aws/en/oltp/).

## Prerequisites

* Databricks CLI v0.265.0 or above
* `psql` client version 14 or above (only needed to run the demo data generation)

## Usage

Modify `databricks.yml`:
* Update the `host` field under `workspace` to the Databricks workspace to deploy to

Run `databricks bundle deploy` to deploy the bundle.

Please note that after this bundle gets deployed, the database instance starts running, which incurs cost.

Run the following queries to populate your database with sample data:

```bash
# Create a demo table:
databricks psql my-instance -- -d my_database -c "CREATE TABLE IF NOT EXISTS hello_world (id SERIAL PRIMARY KEY, message TEXT, number INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"

# Insert 100 rows of demo data:
databricks psql my-instance -- -d my_database -c "INSERT INTO hello_world (message, number) SELECT 'Hello World #' || generate_series, generate_series FROM generate_series(1, 100);"

# Show generated rows:
databricks psql my-instance -- -d my_database -c "SELECT * FROM hello_world;"
```

Open your catalog in Databricks: `databricks bundle open my_catalog`
Navigate to the `public` schema, then to the `hello_world` table, then to "Sample data" and explore your generated data.

## Clean up
To remove the provisioned instance and catalog run `databricks bundle destroy`