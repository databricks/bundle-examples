import dlt
from pyspark.sql.functions import col

# Configuration
bronze_catalog = spark.conf.get("bronze_catalog")
bronze_schema = spark.conf.get("bronze_schema")
silver_catalog = spark.conf.get("silver_catalog")
silver_schema = spark.conf.get("silver_schema")

def create_materialized_table(table_name):

    @dlt.table(name=f"{silver_catalog}.{silver_schema}.{table_name}")
    def lakeflow_pipelines_table():
        df = spark.read.table(f"{bronze_catalog}.{bronze_schema}.{table_name}")
        return df


if __name__ == "__main__":

    tables_list = ["customer", "lineitem", "orders", "nation", "part", "partsupp", "region", "supplier"]

    for table_name in tables_list:
        create_materialized_table(table_name)
