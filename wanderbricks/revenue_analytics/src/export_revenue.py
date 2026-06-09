from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
df = spark.read.table("samples.wanderbricks.bookings")
print(f"would export {df.count()} bookings to CSV")
