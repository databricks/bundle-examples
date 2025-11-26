import dlt
from pathlib import Path
from pyspark.sql.functions import col
from framework.config import Config
from framework.utils import add_metadata_columns, load_table_configs
from framework.write import create_dlt_table


# Configuration
config = Config.from_spark_config()

def create_silver_table(table_config: dict):
    """
    Creates a cleaned materialized view in Lakeflow Declarative Pipelines for the specified table.
    
    Args:
        table_config (dict): Table configuration with source, destination, primary_keys, and expectations.
        
    The materialized view is created in the silver catalog and schema with data quality expectations.
    The source data is read from the bronze layer.
    """
    table_name = table_config["destination"]
    source_table = table_config["source"]
    description = table_config.get("description", f"Silver layer table for {table_name}")
    primary_keys = table_config["primary_keys"]
    
    # Get the three types of expectations
    expectations_warn = table_config.get("expectations_warn", {})
    expectations_fail_update = table_config.get("expectations_fail_update", {})
    expectations_drop_row = table_config.get("expectations_drop_row", {})
    
    # Define source function
    def source_function():
        """Reads the source table from bronze layer and returns it as a DataFrame."""
        # Parse source to get catalog and schema
        source_parts = source_table.split(".")
        if len(source_parts) == 2:
            # If source is "bronze.table", use config catalogs
            df = spark.read.table(f"{config.bronze_catalog}.{config.bronze_schema}.{source_parts[1]}")
        else:
            # If fully qualified, use as-is
            df = spark.read.table(source_table)
        return df
    
    # Create DLT table using shared function
    return create_dlt_table(
        table_name=table_name,
        catalog=config.silver_catalog,
        schema=config.silver_schema,
        description=description,
        primary_keys=primary_keys,
        source_function=source_function,
        expectations_warn=expectations_warn,
        expectations_fail_update=expectations_fail_update,
        expectations_drop_row=expectations_drop_row
    )


if __name__ == "__main__":

    # Load table configuration from all JSON files in the metadata directory
    tables_config = load_table_configs("./metadata")

    # Create table for each configuration
    for table_config in tables_config:
        create_silver_table(table_config)
