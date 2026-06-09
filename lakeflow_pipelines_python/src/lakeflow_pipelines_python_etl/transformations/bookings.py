from pyspark import pipelines as dp


# Wanderbricks bookings (bronze): ingested from the samples dataset.
@dp.table
def bookings():
    return spark.read.table("samples.wanderbricks.bookings")
