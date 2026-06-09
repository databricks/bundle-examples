from pyspark import pipelines as dp
from pyspark.sql.functions import avg, count, round as round_


# Aggregate ratings up to destination level.
@dp.table
def destination_ratings():
    pr = spark.read.table("property_ratings")
    props = spark.read.table("samples.wanderbricks.properties")
    dests = spark.read.table("samples.wanderbricks.destinations")
    return (
        pr.join(props, "property_id")
        .join(dests, "destination_id")
        .groupBy("destination", "country")
        .agg(count("*").alias("rated_properties"), round_(avg("avg_rating"), 2).alias("avg_rating"))
    )
