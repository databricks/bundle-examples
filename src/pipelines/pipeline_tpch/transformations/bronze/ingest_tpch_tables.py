from framework.utils import add_metadata_columns, load_table_configs
from framework.config import Config
from framework.write import create_dlt_table

# Configuration
config = Config.from_spark_config()

# Table definitions
def create_bronze_table(table_config: dict):
    """
    Creates a materialized view in Lakeflow Declarative Pipelines for the specified table.
    
    Args:
        table_config (dict): Table configuration with source, destination, and primary_keys.
        
    The materialized view is created in the catalog and schema specified by
    the bronze_catalog and bronze_schema Spark configuration variables.
    """
    table_name = table_config["destination"]
    source_table = table_config["source"]
    description = table_config.get("description", f"Bronze layer table for {table_name}")
    primary_keys = table_config["primary_keys"]
    
    # Get the three types of expectations
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
        table_name=table_name,
        catalog=config.bronze_catalog,
        schema=config.bronze_schema,
        description=description,
        primary_keys=primary_keys,
        source_function=source_function,
        expectations_warn=expectations_warn,
        expectations_fail_update=expectations_fail_update,
        expectations_drop_row=expectations_drop_row
    )

if __name__ == "__main__":
    from pathlib import Path
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    metadata_dir = script_dir / "metadata"
    
    # Load table configuration from all JSON files in the metadata directory 
    tables_config = load_table_configs(str(metadata_dir))

    print(tables_config)

    # Create table for each configuration
    for table_config in tables_config:
        create_bronze_table(table_config)