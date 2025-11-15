import dlt
from pyspark.sql.functions import col

catalog = "workspace"

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

    @dlt.table(name=f"{table}")
    def lakeflow_pipelines_table():
        return spark.read.table(f"samples.tpch.{table}")


for table in tables_list:
    create_materialized_table(table)
