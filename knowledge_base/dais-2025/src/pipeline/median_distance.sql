CREATE OR REPLACE MATERIALIZED VIEW median_distance AS
SELECT
  pickup_zip,
  dropoff_zip,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY trip_distance) AS median_distance
FROM trips_raw
GROUP BY pickup_zip, dropoff_zip;
