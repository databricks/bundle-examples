# Unity Catalog Metric View (via a DABs job)

This example creates a [Unity Catalog Metric View](https://docs.databricks.com/aws/en/metric-views/) using a Databricks job that runs `CREATE OR REPLACE VIEW … WITH METRICS LANGUAGE YAML` on a SQL warehouse. See [`../metric_view_dbt`](../metric_view_dbt) for a dbt-based variant.

## What it does

Defines `bookings_kpis`, a metric view over the public sample dataset `samples.wanderbricks.bookings`. Once deployed and run, you can query it like:

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

The metric view exposes these dimensions and measures (see [`src/bookings_kpis.metric_view.sql`](src/bookings_kpis.metric_view.sql)):

- Dimensions: `check_in_date`, `check_in_month`, `status`, `guests_count`
- Measures: `total_bookings`, `total_revenue`, `avg_booking_value`, `total_guests`

## Layout

```
metric_view/
  databricks.yml                         # bundle config (catalog/schema/warehouse_id vars)
  resources/bookings_kpis.job.yml        # job with one sql_task
  src/bookings_kpis.metric_view.sql      # CREATE VIEW ... WITH METRICS LANGUAGE YAML
```

The job runs the SQL file on the warehouse you point it at. `{{catalog}}` and `{{schema}}` in the SQL are substituted from job parameters at run time.

## Getting started

1. Replace `<your-serverless-warehouse-id>` in `databricks.yml` with one of your warehouse IDs (`databricks warehouses list`).
2. `databricks bundle deploy`.
3. `databricks bundle run bookings_kpis_metric_view`.
4. Query the view from any SQL editor.

## Notes

- Requires Databricks Runtime / SQL warehouse with Metric View support (DBR 16.4+; serverless SQL warehouses are fine).
- For production, point `source:` at a curated table from your own pipeline rather than the public sample.
