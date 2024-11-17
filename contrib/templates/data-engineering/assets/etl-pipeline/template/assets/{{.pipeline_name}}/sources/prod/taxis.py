import dlt
from pyspark.sql import SparkSession, DataFrame


@dlt.view
def taxis() -> DataFrame:
    spark = SparkSession.builder.getOrCreate()
    return spark.sql("SELECT * FROM samples.nyctaxi.trips")