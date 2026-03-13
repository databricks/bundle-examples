# job_backfill_data

This example demonstrates a Databricks Asset Bundle (DABs) Job that runs a SQL task with a date parameter for backfilling data.

The Job consists of:

1. **run_daily_sql** — A SQL task that runs `src/my_query.sql` with a `run_date` job parameter. The query inserts data from a source table into a target table filtered by `event_date = run_date`, so you can backfill or reprocess specific dates.

* `src/`: SQL and notebook source code for this project.
  * `src/my_query.sql`: Daily insert query that uses the `:run_date` parameter to filter by event date.
* `resources/`: Resource configurations (jobs, pipelines, etc.)
  * `resources/backfill_data.py`: job definition with a parameterized SQL task.

## Job parameters

| Parameter   | Default     | Description                          |
|------------|-------------|--------------------------------------|
| `run_date` | `2024-01-01` | Date used to filter data (e.g. `event_date`). |

Before deploying, set `warehouse_id` in `resources/backfill_data.py` to your SQL warehouse ID, and adjust the catalog/schema/table names in `src/my_query.sql` to match your environment.

## Documentation

For more information about job backfills and parameters, see:
- [Create and run jobs](https://docs.databricks.com/en/jobs/index.html)
- [Backfill jobs](https://docs.databricks.com/aws/en/jobs/backfill-jobs)

## Getting started

Choose how you want to work on this project:

(a) Directly in your Databricks workspace, see
    https://docs.databricks.com/dev-tools/bundles/workspace.

(b) Locally with an IDE like Cursor or VS Code, see
    https://docs.databricks.com/vscode-ext.

(c) With command line tools, see https://docs.databricks.com/dev-tools/cli/databricks-cli.html

If you're developing with an IDE, dependencies for this project should be installed using uv:

*  Make sure you have the UV package manager installed.
   It's an alternative to tools like pip: https://docs.astral.sh/uv/getting-started/installation/.
*  Run `uv sync --dev` to install the project's dependencies.

## Using this project with the CLI

The Databricks workspace and IDE extensions provide a graphical interface for working
with this project. You can also use the CLI:

1. Authenticate to your Databricks workspace, if you have not done so already:
   ```
   $ databricks configure
   ```

2. To deploy a development copy of this project, run:
   ```
   $ databricks bundle deploy --target dev
   ```
   (Note: "dev" is the default target, so `--target` is optional.)

   This deploys everything defined for this project, including the job
   `[dev yourname] sql_backfill_example`. You can find it under **Workflows** (or **Jobs & Pipelines**) in your workspace.

3. To run the job with the default `run_date`:
   ```
   $ databricks bundle run sql_backfill_example
   ```

4. To run the job for a specific date (e.g. backfill):
   ```
   $ databricks bundle run sql_backfill_example --parameters run_date=2024-02-01
   ```
