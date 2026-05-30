# Unity Catalog Metric View

This project demonstrates how to create a [Unity Catalog Metric View](https://docs.databricks.com/aws/en/metric-views/) using Declarative Automation Bundles. Once registered, the metric view becomes available to analysts and BI tools across your workspace, queryable via the `MEASURE()` SQL function.


## Concrete example: Definition and Usage

## `bookings_kpis` metric view

This project defines `bookings_kpis`, a metric view over the public sample dataset `samples.wanderbricks.bookings`.

A SQL task in the job runs `CREATE OR REPLACE VIEW … WITH METRICS LANGUAGE YAML` from [`src/bookings_kpis.metric_view.sql`](src/bookings_kpis.metric_view.sql):

```sql
CREATE OR REPLACE VIEW bookings_kpis
WITH METRICS
LANGUAGE YAML
AS $$
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
$$;
```

`{{catalog}}` and `{{schema}}` in the SQL file are substituted from job parameters at run time.

### SQL Usage

Once registered, query the metric view from any SQL editor:

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
* A SQL warehouse on a runtime that supports Unity Catalog metric views
* Databricks CLI installed and configured

### Setup

1. In `databricks.yml`, replace `https://company.databricks.com` with your workspace URL, and replace `<your-warehouse-id>` with one of your warehouse IDs (`databricks warehouses list`).
2. If you don't have write access to `main`, change `catalog:` under `targets.dev.variables` to a catalog you can write to.

### Deployment

Deploy to dev:
```bash
databricks bundle deploy --target dev
databricks bundle run bookings_kpis_metric_view --target dev
```

Deploy to production:
```bash
databricks bundle deploy --target prod
databricks bundle run bookings_kpis_metric_view --target prod
```

The metric view will be created at `<catalog>.<your_username>.bookings_kpis` (dev) or `<catalog>.prod.bookings_kpis` (prod).

### Notes

- The job has a daily `periodic` trigger so the view definition is re-applied in production. [Development-mode](https://docs.databricks.com/dev-tools/bundles/deployment-modes.html) pauses the trigger automatically, so it only fires after `bundle deploy --target prod`.

- Set `source:` in the YAML body to any UC table you read from. The sample `samples.wanderbricks.bookings` is convenient for getting started. For production, use a table from your own pipeline.

## Learn More

- [Unity Catalog Metric Views](https://docs.databricks.com/metric-views/) — Official documentation
- [Metric View YAML Reference](https://docs.databricks.com/metric-views/yaml-ref)
- [Declarative Automation Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)
