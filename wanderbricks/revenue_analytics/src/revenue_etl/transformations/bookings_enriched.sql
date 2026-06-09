-- Silver: enrich with property + destination, with a data-quality expectation.
CREATE MATERIALIZED VIEW bookings_enriched (
  CONSTRAINT valid_amount EXPECT (total_amount > 0) ON VIOLATION DROP ROW
) AS
SELECT b.booking_id, b.user_id, b.check_in, b.check_out, b.total_amount, b.status,
       p.property_type, p.host_id, d.destination, d.country
FROM bookings_bronze b
JOIN samples.wanderbricks.properties p ON b.property_id = p.property_id
JOIN samples.wanderbricks.destinations d ON p.destination_id = d.destination_id;
