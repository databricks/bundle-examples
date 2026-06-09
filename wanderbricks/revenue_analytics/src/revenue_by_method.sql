USE CATALOG {{catalog}};
USE IDENTIFIER({{schema}});
CREATE OR REPLACE TABLE revenue_by_method AS
SELECT pay.payment_method,
       count(*) AS payments,
       round(sum(pay.amount), 2) AS total_revenue
FROM samples.wanderbricks.payments pay
JOIN samples.wanderbricks.bookings b ON pay.booking_id = b.booking_id
WHERE pay.status = 'completed'
GROUP BY pay.payment_method;
