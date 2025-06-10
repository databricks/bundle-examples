import dlt
from pyspark.sql import SparkSession

spark: SparkSession


@dlt.table
def trips_raw():
    source_table = spark.conf.get("source_table")
    return spark.read.table(source_table)
