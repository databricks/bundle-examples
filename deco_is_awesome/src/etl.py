from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# v3: read the upstream raw bookings table before aggregating
raw = spark.read.table("main.deco.raw_bookings")
print("daily_etl v3: extracted", raw.count(), "rows")
