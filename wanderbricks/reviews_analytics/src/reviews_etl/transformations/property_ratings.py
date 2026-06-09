from pyspark import pipelines as dp
from pyspark.sql.functions import avg, count, round as round_


# Silver: rating + volume per property, with a quality expectation.
@dp.table(expectations={"valid_rating": "rating BETWEEN 1 AND 5"})
def property_ratings():
    return (
        spark.read.table("reviews_bronze")
        .groupBy("property_id")
        .agg(count("*").alias("num_reviews"), round_(avg("rating"), 2).alias("avg_rating"))
    )
