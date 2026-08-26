from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit

spark = SparkSession.builder.getOrCreate()

bookings = spark.range(1, 501).withColumnRenamed("id", "booking_id") \
    .withColumn("amount", (col("booking_id") % lit(7)) * lit(19.5)) \
    .withColumn("status", lit("confirmed"))

print("daily_etl v2: extracted", bookings.count(), "bookings; revenue =", bookings.agg({"amount": "sum"}).collect()[0][0])
