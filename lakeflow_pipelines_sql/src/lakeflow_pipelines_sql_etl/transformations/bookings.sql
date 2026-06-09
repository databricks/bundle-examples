-- Wanderbricks bookings (bronze): ingested from the samples dataset.
CREATE MATERIALIZED VIEW bookings AS
SELECT
  booking_id, user_id, property_id, check_in, check_out,
  guests_count, total_amount, status
FROM samples.wanderbricks.bookings;
