-- Gold: revenue per destination.
CREATE MATERIALIZED VIEW revenue_by_destination AS
SELECT destination, country, count(*) AS bookings, round(sum(total_amount), 2) AS revenue
FROM bookings_enriched GROUP BY destination, country;
