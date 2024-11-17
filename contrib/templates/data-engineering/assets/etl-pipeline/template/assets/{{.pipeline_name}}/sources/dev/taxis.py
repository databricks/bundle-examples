import dlt
from pyspark.sql import SparkSession, DataFrame


@dlt.view(
    comment="Small set of taxis for development (uses LIMIT 10)"
)
def taxis() -> DataFrame:
    spark = SparkSession.builder.getOrCreate()
    return spark.sql("SELECT * FROM samples.nyctaxi.trips LIMIT 10")