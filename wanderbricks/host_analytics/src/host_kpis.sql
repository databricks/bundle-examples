USE CATALOG {{catalog}};
USE IDENTIFIER({{schema}});
CREATE OR REPLACE TABLE host_kpis AS
SELECT h.host_id, h.name AS host_name, h.country,
       count(DISTINCT p.property_id) AS properties,
       count(b.booking_id) AS bookings,
       round(sum(b.total_amount), 2) AS revenue,
       round(avg(r.rating), 2) AS avg_rating
FROM samples.wanderbricks.hosts h
JOIN samples.wanderbricks.properties p ON h.host_id = p.host_id
LEFT JOIN samples.wanderbricks.bookings b ON p.property_id = b.property_id
LEFT JOIN samples.wanderbricks.reviews r ON p.property_id = r.property_id
GROUP BY h.host_id, h.name, h.country;
