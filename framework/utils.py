"""
Utility functions for the Lakehouse Framework.

This module provides common utility functions used across the lakeflow pipelines.
"""

from typing import Optional


def get_catalog_schema(catalog: str, schema: str) -> str:
    """
    Construct a fully qualified catalog.schema name.
    
    Args:
        catalog: The catalog name
        schema: The schema name
        
    Returns:
        Fully qualified catalog.schema string
    """
    return f"{catalog}.{schema}"


def get_table_path(catalog: str, schema: str, table: str) -> str:
    """
    Construct a fully qualified table path.
    
    Args:
        catalog: The catalog name
        schema: The schema name
        table: The table name
        
    Returns:
        Fully qualified catalog.schema.table string
    """
    return f"{catalog}.{schema}.{table}"


def get_spark_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a Spark configuration value.
    
    Args:
        key: Configuration key to retrieve
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.getActiveSession()
        if spark:
            return spark.conf.get(key, default)
        return default
    except Exception:
        return default


def add_metadata_columns(df):
    """
    Adds metadata columns to the input DataFrame.

    Parameters:
        df (DataFrame): Input Spark DataFrame.

    Returns:
        DataFrame: DataFrame with an additional 'ingest_timestamp' column containing the current timestamp.
    """
    from pyspark.sql.functions import current_timestamp
    return df.withColumn("ingest_timestamp", current_timestamp())


def get_or_create_spark_session(app_name: str = "lakehouse_framework"):
    """
    Get the active Spark session or create a new one if none exists.
    
    Args:
        app_name: Name for the Spark application (used only when creating a new session)
        
    Returns:
        SparkSession: The active or newly created Spark session
    """
    from pyspark.sql import SparkSession
    
    # Try to get the active session first
    spark = SparkSession.getActiveSession()
    
    if spark is None:
        # No active session, create a new one
        spark = SparkSession.builder \
            .appName(app_name) \
            .getOrCreate()
    
    return spark


def validate_table_config_schema(config: dict, filename: str = "") -> bool:
    """
    Validate the schema of a table configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
        filename: Optional filename for better error messages
        
    Returns:
        bool: True if valid, raises ValueError if invalid
        
    Raises:
        ValueError: If the configuration schema is invalid
    """
    file_info = f" in '{filename}'" if filename else ""
    
    # Check if it's a dictionary
    if not isinstance(config, dict):
        raise ValueError(f"Configuration entry{file_info} must be a dictionary")
    
    # Required fields
    if "source" not in config:
        raise ValueError(f"Configuration entry{file_info} is missing required 'source' field")
    
    if "destination" not in config:
        raise ValueError(f"Configuration entry{file_info} is missing required 'destination' field")
    
    if "primary_keys" not in config:
        raise ValueError(f"Configuration entry{file_info} is missing required 'primary_keys' field")
    
    # Validate types
    if not isinstance(config["source"], str):
        raise ValueError(f"'source'{file_info} must be a string")
    
    if not isinstance(config["destination"], str):
        raise ValueError(f"'destination'{file_info} must be a string")
    
    if not isinstance(config["primary_keys"], list):
        raise ValueError(f"'primary_keys'{file_info} must be a list")
    
    # Validate primary_keys list contains strings
    for idx, key in enumerate(config["primary_keys"]):
        if not isinstance(key, str):
            raise ValueError(f"primary_keys[{idx}]{file_info} must be a string")
    
    # Validate optional fields
    if "expectations" in config and not isinstance(config["expectations"], dict):
        raise ValueError(f"'expectations'{file_info} must be a dictionary")
    
    if "description" in config and not isinstance(config["description"], str):
        raise ValueError(f"'description'{file_info} must be a string")
    
    if "tags" in config:
        if not isinstance(config["tags"], list):
            raise ValueError(f"'tags'{file_info} must be a list")
        # Validate tags list contains strings
        for idx, tag in enumerate(config["tags"]):
            if not isinstance(tag, str):
                raise ValueError(f"tags[{idx}]{file_info} must be a string")
    
    return True


def load_table_configs(config_dir: str, validate: bool = True) -> list:
    """
    Load and merge all JSON configuration files from a directory.
    Each JSON file should contain a list of table configuration dictionaries.
    Optionally validates the schema of each configuration entry.
    
    Args:
        config_dir: Path to the directory containing JSON configuration files
        validate: If True, validate schema of each config entry (default: True)
        
    Returns:
        list: Combined list of all table configurations from all files
        
    Raises:
        ValueError: If validation is enabled and a config has invalid schema
        FileNotFoundError: If the config directory doesn't exist
    """
    import json
    from pathlib import Path
    
    config_dir = Path(config_dir)
    
    if not config_dir.exists():
        raise FileNotFoundError(f"Configuration directory not found: {config_dir}")
    
    if not config_dir.is_dir():
        raise ValueError(f"Path is not a directory: {config_dir}")
    
    all_configs = []
    json_files = sorted(config_dir.glob("*.json"))
    
    if not json_files:
        print(f"Warning: No JSON files found in {config_dir}")
        return all_configs
    
    for json_file in json_files:
        try:
            with open(json_file, "r") as f:
                file_configs = json.load(f)
            
            # Ensure it's a list
            if not isinstance(file_configs, list):
                raise ValueError(f"File '{json_file.name}' must contain a list of configurations")
            
            # Validate each config entry if requested
            if validate:
                for idx, config in enumerate(file_configs):
                    validate_table_config_schema(config, f"{json_file.name}[{idx}]")
            
            # Add all configs from this file
            all_configs.extend(file_configs)
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file '{json_file.name}': {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error loading config file '{json_file.name}': {str(e)}")
    
    print(f"Loaded {len(json_files)} configuration file(s) with {len(all_configs)} table(s)")
    
    return all_configs
