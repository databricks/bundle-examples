-- Bronze: stream raw bookings from the source dataset.
CREATE OR REFRESH STREAMING TABLE bookings_bronze
AS SELECT * FROM STREAM samples.wanderbricks.bookings;
