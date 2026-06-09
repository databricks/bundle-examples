from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
tables = ["bookings", "reviews", "properties", "destinations", "hosts", "users", "payments"]
for t in tables:
    n = spark.read.table(f"samples.wanderbricks.{t}").count()
    print(f"samples.wanderbricks.{t}: {n} rows")
print("platform health check complete")
