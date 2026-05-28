{#
  A Unity Catalog Metric View, materialized by dbt-databricks.

  Everything below the `config(...)` line is the metric-view YAML body (see
  https://docs.databricks.com/aws/en/metric-views/yaml-ref). The metric_view
  materialization wraps it in:

      CREATE OR REPLACE VIEW <relation> WITH METRICS LANGUAGE YAML AS <yaml>

  so the file looks like SQL to dbt but its contents are YAML. (These jinja
  comments are stripped at compile time; SQL `--` comments would be passed
  through verbatim into the YAML body and break the view definition.)

  Query the resulting metric view from any SQL editor:

      SELECT
        check_in_month,
        MEASURE(total_bookings)    AS bookings,
        MEASURE(total_revenue)     AS revenue,
        MEASURE(avg_booking_value) AS aov
      FROM main.<your_schema>.bookings_kpis
      WHERE check_in_date >= '2024-01-01'
      GROUP BY check_in_month
      ORDER BY check_in_month;
#}
{{ config(materialized='metric_view') }}

version: 0.1
source: samples.wanderbricks.bookings

filter: "status = 'confirmed'"

dimensions:
  - name: check_in_date
    expr: check_in
  - name: check_in_month
    expr: date_trunc('MONTH', check_in)
  - name: status
    expr: status
  - name: guests_count
    expr: guests_count

measures:
  - name: total_bookings
    expr: COUNT(1)
  - name: total_revenue
    expr: SUM(total_amount)
  - name: avg_booking_value
    expr: AVG(total_amount)
  - name: total_guests
    expr: SUM(guests_count)
