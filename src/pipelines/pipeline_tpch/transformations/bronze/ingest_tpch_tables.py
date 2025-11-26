import dlt
from pathlib import Path
from pyspark.sql.functions import col
from framework.utils import add_metadata_columns, load_table_configs
from framework.config import Config
from framework.write import create_dlt_table

# Configuration
config = Config.from_spark_config()

# Table definitions
def create_bronze_table(table_name: str):
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
    
    # Define source function
    def source_function():
        """Reads the source table from samples.tpch and returns it as a DataFrame."""
        source_catalog = tables_config["source"]["catalog"]
        source_schema = tables_config["source"]["schema"]
        df = spark.read.table(f"{source_catalog}.{source_schema}.{table_name}")
        df = add_metadata_columns(df)
        return df
    
    # Create DLT table using shared function
    return create_dlt_table(
        table_name=table_name,
        catalog=config.bronze_catalog,
        schema=config.bronze_schema,
        description=description,
        primary_keys=primary_keys,
        quality_level="bronze",
        source_function=source_function,
        metadata=tables_config.get("metadata")
    )

if __name__ == "__main__":

    # Load table configuration from all JSON files in the directory 
    tables_config = load_table_configs("./")

    # Extract table names from configuration
    tables_list = [table["name"] for table in tables_config["tables"]]

    for table_name in tables_list:
        create_bronze_table(table_name)