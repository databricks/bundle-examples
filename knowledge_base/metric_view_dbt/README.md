# Unity Catalog Metric View using dbt

This project demonstrates how to materialize a [Unity Catalog Metric View](https://docs.databricks.com/metric-views/) via dbt-databricks using Declarative Automation Bundles. The metric view is defined as a dbt model with the [`metric_view` materialization](https://github.com/databricks/dbt-databricks/pull/1285) added in **dbt-databricks 1.12.0**.

**Learn more:** [Unity Catalog Metric Views](https://docs.databricks.com/aws/en/metric-views/) · SQL-job variant: [`../metric_view`](../metric_view)

## Concrete example: Definition and Usage

This project defines `bookings_kpis`, a metric view over the public sample dataset `samples.wanderbricks.bookings`.

### Metric View Definition (dbt model)

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

### SQL Usage

Once materialized, query the metric view from any SQL editor:

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

The view integrates seamlessly with:

- SQL editors and notebooks
- Databricks SQL dashboards / AI/BI Genie
- Any BI tool that connects to your workspace

## Getting Started With This Project

### Prerequisites

* Databricks workspace with Unity Catalog enabled
* A SQL warehouse on a runtime that supports Unity Catalog metric views (Public Preview; any recent serverless or PRO warehouse)
* Databricks CLI installed and configured

### Setup

1. In `databricks.yml`, replace `https://company.databricks.com` with your workspace URL.
2. In `dbt_profiles/profiles.yml`, set `http_path` to one of your warehouses (`databricks warehouses list`) and update `catalog` to one you can write to (the default `main` is often not writable).

### Deployment

Deploy to dev:
```bash
databricks bundle deploy --target dev
databricks bundle run metric_view_dbt_job --target dev
```

Deploy to production:
```bash
databricks bundle deploy --target prod
databricks bundle run metric_view_dbt_job --target prod
```

The metric view will be created at `<catalog>.<your_username>.bookings_kpis` (dev) or `<catalog>.default.bookings_kpis` (prod).

## Advanced Topics

**Scheduling:** The job has a daily `periodic` trigger so `dbt run` re-applies the view definition in production. [Development-mode](https://docs.databricks.com/dev-tools/bundles/deployment-modes.html) deploys pause the trigger automatically, so it only fires after `bundle deploy --target prod`.

**dbt-databricks version:** Requires `dbt-databricks >= 1.12.0` (the `metric_view` materialization). The job pins this in its task environment (`resources/metric_view_dbt.job.yml`).

**File extension:** The model file is `.sql` even though its body is YAML — dbt model files must use `.sql`. dbt-databricks wraps the body in `CREATE OR REPLACE VIEW … LANGUAGE YAML AS $$ … $$` at run time.

**Custom source table:** Point `source:` in the YAML body at any UC table you read from. For production, replace the public `samples.wanderbricks.bookings` with a curated table from your own pipeline.

## Learn More

- [Unity Catalog Metric Views](https://docs.databricks.com/metric-views/) — Official documentation
- [Metric View YAML Reference](https://docs.databricks.com/metric-views/yaml-ref)
- [`metric_view` materialization in dbt-databricks](https://github.com/databricks/dbt-databricks/pull/1285)
- [Declarative Automation Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)
