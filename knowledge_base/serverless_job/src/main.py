from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, count, round as round_

spark = SparkSession.builder.getOrCreate()

# Summarize Wanderbricks property reviews.
reviews = spark.read.table("samples.wanderbricks.reviews").filter("is_deleted = false")
summary = (
    reviews.groupBy("property_id")
    .agg(
        count("*").alias("num_reviews"),
        round_(avg("rating"), 2).alias("avg_rating"),
    )
    .orderBy("num_reviews", ascending=False)
)
print("Top-reviewed Wanderbricks properties:")
summary.show(10)
