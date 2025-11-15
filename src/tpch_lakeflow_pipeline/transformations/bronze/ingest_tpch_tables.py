import dlt
from pathlib import Path
from pyspark.sql.functions import col
from lakehouse_framework.utils import add_metadata_columns, get_or_create_spark_session, load_table_configs
from lakehouse_framework.config import Config

# Configuration
config = Config.from_spark_config()
spark = get_or_create_spark_session()
bronze_catalog = config.bronze_catalog
bronze_schema = config.bronze_schema

def create_materialized_table(table_name: str):
    """
    Creates a materialized view in Lakeflow Declarative Pipelines for the specified table.
    
    Args:
        table_name (str): Name of the table to create as a materialized view.
        
    The materialized view is created in the catalog and schema specified by
    the bronze_catalog and bronze_schema Spark configuration variables.
    The source data is read from the samples.tpch schema.
    """
    # Find table metadata from config
    table_metadata = next((t for t in tables_config["tables"] if t["name"] == table_name), None)
    
    if table_metadata is None:
        raise ValueError(f"Table {table_name} not found in configuration")
    
    description = table_metadata.get("description", f"Bronze layer table for {table_name}")
    primary_keys = [key.strip() for key in table_metadata.get("primary_key", "").split(",")]
    
    # Build table properties with primary key information
    table_properties = {
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true",
        "primary_key": ", ".join(primary_keys)
    }
    
    @dlt.table(
        name=f"{bronze_catalog}.{bronze_schema}.{table_name}",
        comment=description,
        table_properties=table_properties,
        primary_keys=primary_keys if primary_keys and primary_keys[0] else None
    )
    @dlt.expect_all_or_drop({f"{pk}_not_null": f"{pk} IS NOT NULL" for pk in primary_keys})
    def lakeflow_pipelines_table():
        """
        Reads the source table from samples.tpch and returns it as a DataFrame.
        """
        source_catalog = tables_config["source"]["catalog"]
        source_schema = tables_config["source"]["schema"]
        df = spark.read.table(f"{source_catalog}.{source_schema}.{table_name}")
        df = add_metadata_columns(df)
        return df
    
    return lakeflow_pipelines_table

if __name__ == "__main__":

    # Load table configuration from all JSON files in the directory 
    tables_config = load_table_configs("./")

    # Extract table names from configuration
    tables_list = [table["name"] for table in tables_config["tables"]]

    for table_name in tables_list:
        create_materialized_table(table_name)