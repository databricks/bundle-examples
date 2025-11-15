import dlt
from pyspark.sql.functions import col
from lakehouse_framework.config import Config

# Configuration
config = Config.from_spark_config()
bronze_catalog = config.bronze_catalog
bronze_schema = config.bronze_schema
silver_catalog = config.silver_catalog
silver_schema = config.silver_schema

def create_materialized_table(table_name):

    @dlt.table(name=f"{silver_catalog}.{silver_schema}.{table_name}")
    def lakeflow_pipelines_table():
        df = spark.read.table(f"{bronze_catalog}.{bronze_schema}.{table_name}")
        return df


if __name__ == "__main__":

    tables_list = ["customer", "lineitem", "orders", "nation", "part", "partsupp", "region", "supplier"]

    for table_name in tables_list:
        create_materialized_table(table_name)
