# Lakebase Autoscaling (Postgres) project with branching

This example demonstrates how to define a Lakebase Autoscaling project with a non-default branch in a Declarative Automation Bundle.

It includes and deploys:
- A Lakebase Autoscaling project with configurable min and max compute units (CUs)
- A non-default `development` branch for isolated dev/test workflows
- A read-only replica endpoint on the default production branch

Lakebase Autoscaling is Databricks' managed PostgreSQL service with autoscaling compute, Git-like branching, scale-to-zero, and instant point-in-time restore.

For more information about Lakebase Autoscaling, see the [documentation](https://docs.databricks.com/aws/en/oltp/projects/).

## Prerequisites

* Databricks CLI v0.287.0 or above
* `psql` client version 14 or above (Optional, only needed to run the demo queries)

## Usage

Modify `databricks.yml`:
* Update the `host` field under each target's `workspace` block (`dev` and `prod`) to point at the Databricks workspace you want to deploy to
* Adjust `autoscaling_limit_min_cu` and `autoscaling_limit_max_cu` to fit your workload (valid range: 0.5-32 CU, max minus min cannot exceed 16 CU)
* Adjust `suspend_timeout_duration` to control scale-to-zero behavior (minimum: 60 seconds)

The bundle defines two targets: `dev` (the default) and `prod`. Run `databricks bundle deploy` to deploy to `dev`, or `databricks bundle deploy --target prod` to deploy to `prod`.

Please note that after this bundle gets deployed, the project and its compute endpoints start running, which incurs cost. Endpoints with scale-to-zero enabled will suspend after the configured `suspend_timeout_duration`.

Run the following queries against the **production** branch to populate your database with sample data:

```bash
# Create a demo table:
databricks psql --project my-autoscaling-project -- -d databricks_postgres -c "CREATE TABLE IF NOT EXISTS hello_world (id SERIAL PRIMARY KEY, message TEXT, number INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"

# Insert 100 rows of demo data:
databricks psql --project my-autoscaling-project -- -d databricks_postgres -c "INSERT INTO hello_world (message, number) SELECT 'Hello World #' || generate_series, generate_series FROM generate_series(1, 100);"

# Show generated rows:
databricks psql --project my-autoscaling-project -- -d databricks_postgres -c "SELECT * FROM hello_world;"
```

Run the following queries against the **development** branch to verify the branched data:

**Important:** Prior to running the following command, the `development` branch MUST be 'reset' via the web UI. This will re-sync the child branch with its parent. More information regarding resetting a branch can be found [here](https://docs.databricks.com/aws/en/oltp/projects/manage-branches#reset-branch-from-parent).

```bash
# Query the development branch:
databricks psql --project my-autoscaling-project --branch development -- -d databricks_postgres -c "SELECT count(*) FROM hello_world;"
```

## Clean up
To remove the provisioned project, branches, and endpoints run `databricks bundle destroy`
