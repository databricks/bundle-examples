CREATE OR REPLACE MATERIALIZED VIEW peak_hour AS
SELECT
  EXTRACT(HOUR FROM tpep_pickup_datetime) AS pickup_hour,
  COUNT(*) AS trip_count
FROM trips_raw
GROUP BY pickup_hour
ORDER BY trip_count DESC;
