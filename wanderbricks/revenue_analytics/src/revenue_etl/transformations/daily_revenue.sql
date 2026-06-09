-- Gold: daily revenue.
CREATE MATERIALIZED VIEW daily_revenue AS
SELECT check_in AS booking_date, count(*) AS bookings, round(sum(total_amount), 2) AS revenue
FROM bookings_enriched GROUP BY check_in;
