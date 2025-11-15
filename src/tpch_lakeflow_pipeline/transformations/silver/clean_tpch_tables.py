import dlt
from pyspark.sql.functions import col


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

    @dlt.table(name=f"{silver_catalog}.{silver_schema}.{table}")
    def lakeflow_pipelines_table():
        return spark.read.table(f"{bronze_catalog}.{bronze_schema}.{table}")


if __name__ == "__main__":
    # Configuration
    bronze_catalog = spark.conf.get("bronze_catalog")
    bronze_schema = spark.conf.get("bronze_schema")
    silver_catalog = spark.conf.get("silver_catalog")
    silver_schema = spark.conf.get("silver_schema")

    for table in tables_list:
        create_materialized_table(table)
