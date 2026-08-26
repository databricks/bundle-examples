from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.getOrCreate()

# v4: enforce a data-quality row-count check before aggregating
df = spark.range(0, 100).withColumn("amount", F.col("id") * 2)
expected_min = 500
actual = df.count()
if actual < expected_min:
    raise ValueError(
        f"daily_etl v4 quality check failed: got {actual} rows, expected >= {expected_min}"
    )
print("daily_etl v4: validated", actual, "rows")
