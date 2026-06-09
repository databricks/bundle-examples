-- Ingest Wanderbricks bookings into a managed streaming table.
-- Executed by Databricks Workflows (see resources/bookings.job.yml).

USE CATALOG {{catalog}};
USE IDENTIFIER({{schema}});

CREATE OR REFRESH STREAMING TABLE
  bookings_raw
AS SELECT
  booking_id,
  user_id,
  property_id,
  check_in,
  check_out,
  guests_count,
  total_amount,
  status
FROM STREAM samples.wanderbricks.bookings;
