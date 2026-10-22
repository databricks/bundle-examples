from pyspark import pipelines as dp


@dp.materialized_view
def permission_example():
    return spark.range(1)
