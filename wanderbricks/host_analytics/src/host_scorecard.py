import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, count, round as round_, sum as sum_

a = argparse.ArgumentParser(); a.add_argument("--catalog", required=True); a.add_argument("--schema", required=True)
args = a.parse_args()
spark = SparkSession.builder.getOrCreate()
h = spark.read.table("samples.wanderbricks.hosts")
p = spark.read.table("samples.wanderbricks.properties")
b = spark.read.table("samples.wanderbricks.bookings")
scorecard = (h.join(p, "host_id").join(b, "property_id", "left")
             .groupBy("host_id", "name")
             .agg(count("booking_id").alias("bookings"), round_(sum_("total_amount"), 2).alias("revenue")))
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {args.catalog}.{args.schema}")
scorecard.write.mode("overwrite").saveAsTable(f"{args.catalog}.{args.schema}.host_scorecard")
print("host_scorecard written")
