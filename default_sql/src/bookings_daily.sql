-- Daily Wanderbricks booking metrics (see resources/bookings.job.yml).

USE CATALOG {{catalog}};
USE IDENTIFIER({{schema}});

CREATE OR REPLACE MATERIALIZED VIEW
  bookings_daily
AS SELECT
  check_in AS booking_date,
  count(*) AS number_of_bookings,
  round(sum(total_amount), 2) AS total_revenue
FROM bookings_raw
-- In dev only look at recent bookings; in prod aggregate everything.
WHERE {{bundle_target}} = "prod" OR check_in >= '2024-06-01'
GROUP BY check_in;
