from pyspark import pipelines as dp


# Bronze: active (non-deleted) reviews.
@dp.table
def reviews_bronze():
    return spark.read.table("samples.wanderbricks.reviews").filter("is_deleted = false")
