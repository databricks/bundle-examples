from pathlib import Path
from framework.utils import add_metadata_columns
from framework.metadata import load_table_configs
from framework.config import Config
from framework.dlt import create_dlt_table

# Configuration
config = Config.from_spark_config()

# Metadata path (relative to project root)
METADATA_PATH = Path(__file__).resolve().parents[4] / "pipelines" / "pipeline_tpch" / "metadata" / "bronze"

# Table definitions
def create_bronze_table(table_config: dict):
    """
    Creates a materialized view in Lakeflow Declarative Pipelines for the specified table.
    
    Args:
        table_config (dict): Table configuration with source, destination, and primary_keys.
        
    The materialized view is created in the catalog and schema specified by
    the bronze_catalog and bronze_schema Spark configuration variables.
    """

    full_table_name = f"{config.bronze_catalog}.{config.bronze_schema}.{table_config['destination']}"
    source_table = table_config["source"]

    # Get optional input parameters
    description = table_config.get("description")
    primary_keys = table_config.get("primary_keys")
    expectations_warn = table_config.get("expectations_warn", {})
    expectations_fail_update = table_config.get("expectations_fail_update", {})
    expectations_drop_row = table_config.get("expectations_drop_row", {})

    # Define source function
    def source_function():
        """Reads the source table and returns it as a DataFrame."""
        df = spark.read.table(source_table)
        df = add_metadata_columns(df)
        return df
    
    # Create DLT table using shared function
    return create_dlt_table(
        table_name=full_table_name,
        source_function=source_function,
        # description=description,
        # primary_keys=primary_keys,
        # expectations_warn=expectations_warn,
        # expectations_fail_update=expectations_fail_update,
        # expectations_drop_row=expectations_drop_row
    )

if __name__ == "__main__":
    
    # Load table configuration from metadata directory
    tables_config = load_table_configs(METADATA_PATH)

    # Create table for each configuration
    for table_config in tables_config:
        create_bronze_table(table_config)