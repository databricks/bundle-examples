import argparse

import mlflow
from pyspark.sql import SparkSession
from pyspark.sql.functions import datediff

p = argparse.ArgumentParser()
p.add_argument("--experiment", required=True)
args = p.parse_args()

spark = SparkSession.builder.getOrCreate()
bookings = spark.read.table("samples.wanderbricks.bookings")
# Simple "demand" features off the bookings table.
features = bookings.withColumn("nights", datediff("check_out", "check_in"))
avg_nights = features.agg({"nights": "avg"}).collect()[0][0]

mlflow.set_experiment(args.experiment)
with mlflow.start_run(run_name="baseline"):
    mlflow.log_metric("total_bookings", bookings.count())
    mlflow.log_metric("avg_nights", float(avg_nights))
print("Logged baseline occupancy run.")
