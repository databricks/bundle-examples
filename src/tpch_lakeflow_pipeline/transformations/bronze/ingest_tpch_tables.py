import dlt
from pyspark.sql.functions import col

# Configuration
bronze_catalog = spark.conf.get("bronze_catalog")
bronze_schema = spark.conf.get("bronze_schema")

tables_list = [
    "customer",
    "lineitem",
    "orders",
    "nation",
    "part",
    "partsupp",
    "region",
    "supplier"
]

def create_materialized_table(table):

    @dlt.table(name=f"{bronze_catalog}.{bronze_schema}.{table}")
    def lakeflow_pipelines_table():
        return spark.read.table(f"samples.tpch.{table}")


for table in tables_list:
    create_materialized_table(table)
