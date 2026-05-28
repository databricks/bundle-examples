# Unity Catalog Metric View (via dbt)

This example creates a [Unity Catalog Metric View](https://docs.databricks.com/aws/en/metric-views/) using the [`metric_view` materialization](https://github.com/databricks/dbt-databricks/pull/1285) added in **dbt-databricks 1.12.0**. The deploy runs a Databricks job whose `dbt_task` executes `dbt run`, which in turn issues `CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML` against your warehouse.

See [`../metric_view`](../metric_view) for a variant that does the same thing with a raw `sql_task` (no dbt).

## What it does

Defines `bookings_kpis`, a metric view over the public sample dataset `samples.wanderbricks.bookings`. Once `dbt run` has materialized it, query it like:

```sql
SELECT
  check_in_month,
  MEASURE(total_bookings)    AS bookings,
  MEASURE(total_revenue)     AS revenue,
  MEASURE(avg_booking_value) AS aov
FROM main.<your_schema>.bookings_kpis
WHERE check_in_date >= '2024-01-01'
GROUP BY check_in_month
ORDER BY check_in_month;
```

The metric view exposes these dimensions and measures (see [`src/models/bookings_kpis.sql`](src/models/bookings_kpis.sql)):

- Dimensions: `check_in_date`, `check_in_month`, `status`, `guests_count`
- Measures: `total_bookings`, `total_revenue`, `avg_booking_value`, `total_guests`

## Layout

```
metric_view-dbt/
  databricks.yml                          # bundle config and targets
  dbt_project.yml                         # dbt project; points at src/models
  dbt_profiles/profiles.yml               # profile the deployed job uses
  resources/metric_view_dbt.job.yml       # job with one dbt_task
  src/models/
    bookings_kpis.sql                     # the metric_view (jinja config + YAML body)
    schema.yml                            # dbt model docs
```

## Getting started

1. Point `dbt_profiles/profiles.yml` at one of your SQL warehouses (set `http_path`) and pick a `catalog`/`schema` you can write to.
2. `databricks bundle deploy`.
3. `databricks bundle run metric_view_dbt_job`.
4. Query the view from any SQL editor.

## Notes

- **dbt-databricks 1.12.0+ is required** — that's the version that introduced the `metric_view` materialization. The job pins it in the task environment (`resources/metric_view_dbt.job.yml`).
- Requires a Databricks Runtime / SQL warehouse with Metric View support (DBR 16.4+; serverless SQL warehouses qualify).
- The model file is `.sql` even though its body is YAML — dbt model files must use `.sql`, and the `metric_view` materialization wraps the body in `CREATE OR REPLACE VIEW ... LANGUAGE YAML AS $$ ... $$`.
- For production, replace `samples.wanderbricks.bookings` with a table from your own pipeline.
