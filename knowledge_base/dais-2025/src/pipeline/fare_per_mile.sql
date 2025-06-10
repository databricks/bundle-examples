CREATE OR REPLACE MATERIALIZED VIEW fare_per_mile AS
SELECT
  pickup_zip,
  AVG(fare_amount / trip_distance) AS avg_fare_per_mile
FROM trips_raw
WHERE trip_distance > 0
GROUP BY pickup_zip;
