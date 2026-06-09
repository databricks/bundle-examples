from pyspark import pipelines as dp
from pyspark.sql.functions import avg, count, round as round_


# Average rating and review volume per property.
@dp.table
def property_ratings():
    reviews = spark.read.table("samples.wanderbricks.reviews").filter("is_deleted = false")
    return (
        reviews.groupBy("property_id")
        .agg(count("*").alias("num_reviews"), round_(avg("rating"), 2).alias("avg_rating"))
    )
