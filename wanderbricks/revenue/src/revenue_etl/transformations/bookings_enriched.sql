-- Silver: bookings joined with property + destination context.
CREATE MATERIALIZED VIEW bookings_enriched AS
SELECT b.booking_id, b.user_id, b.check_in, b.check_out, b.total_amount, b.status,
       p.property_type, p.host_id, d.destination, d.country
FROM samples.wanderbricks.bookings b
JOIN samples.wanderbricks.properties p ON b.property_id = p.property_id
JOIN samples.wanderbricks.destinations d ON p.destination_id = d.destination_id;
