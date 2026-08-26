import dlt
from pyspark.sql.functions import lit

@dlt.table
def gold_summary():
    return spark.range(10).withColumn("revenue", lit(100.0))
