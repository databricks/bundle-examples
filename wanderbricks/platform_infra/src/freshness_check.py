from pyspark.sql import SparkSession
from pyspark.sql.functions import max as max_

spark = SparkSession.builder.getOrCreate()
for t in ["bookings", "reviews", "payments"]:
    df = spark.read.table(f"samples.wanderbricks.{t}")
    if "updated_at" in df.columns:
        latest = df.agg(max_("updated_at")).collect()[0][0]
        print(f"samples.wanderbricks.{t} latest updated_at: {latest}")
print("freshness check complete")
