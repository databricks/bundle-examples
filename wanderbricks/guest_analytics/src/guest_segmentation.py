import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, round as round_, sum as sum_

p = argparse.ArgumentParser()
p.add_argument("--catalog", required=True)
p.add_argument("--schema", required=True)
args = p.parse_args()

spark = SparkSession.builder.getOrCreate()
users = spark.read.table("samples.wanderbricks.users")
bookings = spark.read.table("samples.wanderbricks.bookings")

segments = (
    users.join(bookings, users.user_id == bookings.user_id)
    .groupBy(users.user_type, users.is_business)
    .agg(count("*").alias("bookings"), round_(sum_("total_amount"), 2).alias("total_spend"))
)
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {args.catalog}.{args.schema}")
segments.write.mode("overwrite").saveAsTable(f"{args.catalog}.{args.schema}.guest_segments")
print("Wrote guest_segments:")
segments.orderBy(col("total_spend").desc()).show()
