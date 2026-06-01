-- Create (or replace) a Unity Catalog Metric View over samples.wanderbricks.bookings.
-- See https://docs.databricks.com/metric-views/yaml-ref for the YAML syntax.
--
-- Once deployed and run, query the metric view from any SQL editor with:
--   SELECT MEASURE(total_bookings), MEASURE(total_revenue)
--   FROM <catalog>.<your_schema>.bookings_kpis
--   WHERE check_in_month >= '2024-01-01'
--   GROUP BY check_in_month;

CREATE SCHEMA IF NOT EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}});
USE CATALOG IDENTIFIER({{catalog}});
USE IDENTIFIER({{schema}});

CREATE OR REPLACE VIEW bookings_kpis
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.0
comment: Booking KPIs (count, revenue, AOV, guests) over samples.wanderbricks.bookings.
source: samples.wanderbricks.bookings

filter: status = 'confirmed'

dimensions:
  - name: check_in_date
    expr: check_in
  - name: check_in_month
    expr: date_trunc('MONTH', check_in)
  - name: guests_count
    expr: guests_count

measures:
  - name: total_bookings
    expr: COUNT(1)
    comment: Number of confirmed bookings.
  - name: total_revenue
    expr: SUM(total_amount)
    comment: Total revenue across confirmed bookings.
  - name: avg_booking_value
    expr: AVG(total_amount)
    comment: Average revenue per confirmed booking.
  - name: total_guests
    expr: SUM(guests_count)
    comment: Total guests across confirmed bookings.
$$;
