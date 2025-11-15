import dlt
from pyspark.sql.functions import col
from utilities.util_library import add_metadata_columns

def create_materialized_table(table_name: str):
    """
    Creates a materialized view in Lakeflow Declarative Pipelines for the specified table.
    
    Args:
        table_name (str): Name of the table to create as a materialized view.
        
    The materialized view is created in the catalog and schema specified by
    the bronze_catalog and bronze_schema Spark configuration variables.
    The source data is read from the samples.tpch schema.
    """
    @dlt.table(name=f"{bronze_catalog}.{bronze_schema}.{table}")
    def lakeflow_pipelines_table(table_name):
        """
        Reads the source table from samples.tpch and returns it as a DataFrame.
        """
        df = spark.read.table(f"samples.tpch.{table_name}")
        df = add_metadata_columns(df)
        return df

if __name__ == "__main__":
    # Configuration
    bronze_catalog = spark.conf.get("bronze_catalog")
    bronze_schema = spark.conf.get("bronze_schema")
    tables_list = ["customer", "lineitem", "orders", "nation", "part", "partsupp", "region", "supplier"]

    for table in tables_list:
        create_materialized_table(table)