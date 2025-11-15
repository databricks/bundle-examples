import dlt
from pyspark.sql.functions import col

source_catalog = current_catalog()
source_schema = current_schema()
target_schema = source_schema.replace("bronze", "silver")

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

    @dlt.table(name=f"{source_catalog}.{target_schema}.{table}")
    def lakeflow_pipelines_table():
        return spark.read.table(f"{source_catalog}.{source_schema}.{table}")


for table in tables_list:
    create_materialized_table(table)
