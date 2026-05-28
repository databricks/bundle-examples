-- Create (or replace) a Unity Catalog Metric View over samples.wanderbricks.bookings.
-- See https://docs.databricks.com/aws/en/metric-views/yaml-ref for the YAML syntax.
--
-- Once deployed and run, query the metric view from any SQL editor with:
--   SELECT MEASURE(total_bookings), MEASURE(total_revenue)
--   FROM <catalog>.<schema>.bookings_kpis
--   WHERE check_in_month >= '2024-01-01'
--   GROUP BY check_in_month;

USE CATALOG IDENTIFIER({{catalog}});
USE IDENTIFIER({{schema}});

CREATE OR REPLACE VIEW bookings_kpis
WITH METRICS
LANGUAGE YAML
AS $$
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
$$;
