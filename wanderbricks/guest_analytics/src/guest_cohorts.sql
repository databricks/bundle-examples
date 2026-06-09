USE CATALOG {{catalog}};
USE IDENTIFIER({{schema}});
CREATE OR REPLACE TABLE guest_cohorts AS
SELECT u.country, u.user_type,
       count(DISTINCT u.user_id) AS guests,
       count(b.booking_id) AS bookings,
       round(sum(b.total_amount), 2) AS spend
FROM samples.wanderbricks.users u
JOIN samples.wanderbricks.bookings b ON u.user_id = b.user_id
GROUP BY u.country, u.user_type;
