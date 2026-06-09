import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, count, current_date

p = argparse.ArgumentParser()
p.add_argument("--catalog", required=True)
p.add_argument("--schema", required=True)
args = p.parse_args()

spark = SparkSession.builder.getOrCreate()
bookings = spark.read.table("samples.wanderbricks.bookings")
props = spark.read.table("samples.wanderbricks.properties")
# Naive forecast: per-destination average occupancy from historical bookings.
preds = (bookings.join(props, "property_id")
         .groupBy("destination_id")
         .agg(count("booking_id").alias("historical_bookings"),
              avg("guests_count").alias("avg_party_size"))
         .withColumn("scored_at", current_date()))
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {args.catalog}.{args.schema}")
preds.write.mode("overwrite").saveAsTable(f"{args.catalog}.{args.schema}.occupancy_predictions")
print("occupancy_predictions written")
