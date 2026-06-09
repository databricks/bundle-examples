-- Wanderbricks revenue by destination (gold): bookings x properties x destinations.
CREATE MATERIALIZED VIEW revenue_by_destination AS
SELECT
  d.destination,
  d.country,
  count(*) AS number_of_bookings,
  round(sum(b.total_amount), 2) AS total_revenue
FROM bookings b
JOIN samples.wanderbricks.properties p ON b.property_id = p.property_id
JOIN samples.wanderbricks.destinations d ON p.destination_id = d.destination_id
GROUP BY d.destination, d.country;
