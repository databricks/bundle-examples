"""
Utility functions for the Lakehouse Framework.

This module provides common utility functions used across the lakeflow pipelines.
"""

from typing import Optional
from pathlib import Path
import os


def get_metadata_path(pipeline_name: str, layer: str) -> Path:
    """Get metadata path from Spark config or use relative path for local development.
    
    Args:
        pipeline_name: Name of the pipeline (e.g., 'pipeline_tpch')
        layer: Data layer (e.g., 'bronze', 'silver', 'gold')
        
    Returns:
        Path to the metadata directory
    """
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.getActiveSession()
        if spark:
            workspace_path = spark.conf.get("workspace_path")
            return Path(workspace_path) / "pipelines" / pipeline_name / "metadata" / layer
    except Exception:
        pass
    # Fallback for local development
    return Path(os.getcwd()) / "pipelines" / pipeline_name / "metadata" / layer


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


