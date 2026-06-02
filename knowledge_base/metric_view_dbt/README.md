# Unity Catalog Metric View using dbt

This project demonstrates how to materialize a [Unity Catalog Metric View](https://docs.databricks.com/metric-views/) via dbt-databricks using Declarative Automation Bundles. The metric view is defined as a dbt model with the [`metric_view` materialization](https://github.com/databricks/dbt-databricks/pull/1285) added in dbt-databricks 1.12.0.

For the SQL-job variant, see [`../metric_view`](../metric_view).

## `bookings_kpis` metric view

This project defines `bookings_kpis`, a metric view over the public sample dataset `samples.wanderbricks.bookings`.

The model lives in [`src/models/bookings_kpis.sql`](src/models/bookings_kpis.sql):

```sql
{{ config(materialized='metric_view') }}

version: 1.0
source: samples.wanderbricks.bookings
filter: status = 'confirmed'
dimensions:
  - name: check_in_month
    expr: date_trunc('MONTH', check_in)
measures:
  - name: total_bookings
    expr: COUNT(1)
  - name: total_revenue
    expr: SUM(total_amount)
```

The `{{ config(materialized='metric_view') }}` line is the only jinja; everything below it is the metric view YAML body. dbt-databricks issues the equivalent `CREATE OR REPLACE VIEW … WITH METRICS LANGUAGE YAML` against the warehouse at `dbt run` time.

Once materialized, query the metric view from any SQL editor:

```sql
SELECT
  check_in_month,
  MEASURE(total_bookings) AS bookings,
  MEASURE(total_revenue)  AS revenue
FROM <catalog>.<your_schema>.bookings_kpis
GROUP BY check_in_month
ORDER BY check_in_month;
```

## Get started

### Prerequisites

* Databricks workspace with Unity Catalog enabled
* A SQL warehouse on a runtime that supports Unity Catalog metric views
* Databricks CLI installed and configured

### Setup

1. In `dbt_profiles/profiles.yml`, set `http_path` (in both `dev` and `prod`) to one of your warehouses (`databricks warehouses list`) and update `catalog` to one you can write to (the default `main` is often not writable).

### Deployment

Deploy to dev:

```bash
databricks bundle deploy --target dev
```

```bash
databricks bundle run metric_view_dbt_job --target dev
```

Deploy to production:

```bash
databricks bundle deploy --target prod
```

```bash
databricks bundle run metric_view_dbt_job --target prod
```

The metric view will be created at `<catalog>.<your_username>.bookings_kpis` (dev) or `<catalog>.prod.bookings_kpis` (prod).

### Notes

- The job has a daily `periodic` trigger so `dbt run` re-applies the view definition in production. [Development-mode](https://docs.databricks.com/dev-tools/bundles/deployment-modes.html) pauses the trigger automatically, so it only fires after `bundle deploy --target prod`.
- Requires `dbt-databricks >= 1.12.0` (the version that introduced the `metric_view` materialization). The job pins this in its task environment.
- The model file is `.sql` even though its body is YAML — dbt model files must use `.sql`. dbt-databricks wraps the body in `CREATE OR REPLACE VIEW … LANGUAGE YAML AS $$ … $$` at run time.
- Set `source:` in the YAML body to any UC table you read from. For production, replace `samples.wanderbricks.bookings` with a table from your own pipeline.

## Learn more

- [Unity Catalog Metric Views](https://docs.databricks.com/metric-views/) — Official documentation
- [Metric View YAML Reference](https://docs.databricks.com/metric-views/yaml-ref)
- [`metric_view` materialization in dbt-databricks](https://github.com/databricks/dbt-databricks/pull/1285)
- [Declarative Automation Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)
