USE CATALOG {{catalog}};
USE IDENTIFIER({{schema}});
CREATE OR REPLACE TABLE property_revenue AS
SELECT p.property_id, p.property_type,
       count(b.booking_id) AS bookings,
       round(sum(b.total_amount), 2) AS revenue
FROM samples.wanderbricks.properties p
LEFT JOIN samples.wanderbricks.bookings b ON p.property_id = b.property_id
GROUP BY p.property_id, p.property_type;
