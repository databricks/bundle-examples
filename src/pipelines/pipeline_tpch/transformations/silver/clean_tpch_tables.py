from framework.config import Config
from framework.utils import add_metadata_columns, get_metadata_path
from framework.metadata import load_table_configs
from framework.dlt import create_dlt_table


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
    full_table_name = f"{config.silver_catalog}.{config.silver_schema}.{table_config['destination']}"
    source_table = table_config["source"]

    # Get optional input parameters
    description = table_config.get("description")
    primary_keys = table_config.get("primary_keys")
    expectations_warn = table_config.get("expectations_warn", {})
    expectations_fail_update = table_config.get("expectations_fail_update", {})
    expectations_drop_row = table_config.get("expectations_drop_row", {})
    
    # Define source function
    def source_function():
        """Reads the source table from bronze layer and returns it as a DataFrame."""
        # Construct full table path using bronze catalog and schema from config
        df = spark.read.table(f"{config.bronze_catalog}.{config.bronze_schema}.{source_table}")
        return df
    
    # Create DLT table using shared function
    return create_dlt_table(
        table_name=full_table_name,
        source_function=source_function,
        description=description,
        primary_keys=primary_keys,
        expectations_warn=expectations_warn,
        expectations_fail_update=expectations_fail_update,
        expectations_drop_row=expectations_drop_row
    )


if __name__ == "__main__":

    # Load table configuration from metadata directory
    tables_config = load_table_configs(get_metadata_path("pipeline_tpch", "silver"))

    # Create table for each configuration
    for table_config in tables_config:
        create_silver_table(table_config)
