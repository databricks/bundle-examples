"""
Ingest data from Unity Catalog Volume using AutoLoader.

AutoLoader automatically processes new files as they arrive in cloud storage,
providing exactly-once semantics and schema evolution.
"""
import dlt
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp
from framework.config import Config
from framework.utils import add_metadata_columns

# Configuration
config = Config.from_spark_config()
spark = SparkSession.getActiveSession()

# AutoLoader configuration
VOLUME_PATH = spark.conf.get("volume_path", "/Volumes/catalog/schema/volume_name/data")
FILE_FORMAT = spark.conf.get("file_format", "json")  # json, csv, parquet, avro, text
SCHEMA_LOCATION = spark.conf.get("schema_location", None)


@dlt.table(
    name=f"{config.bronze_catalog}.{config.bronze_schema}.autoloader_data",
    comment="Bronze layer table ingesting data from Unity Catalog Volume using AutoLoader",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def autoloader_data():
    """
    Reads data from Unity Catalog Volume using AutoLoader (cloudFiles).
    
    AutoLoader features:
    - Incremental processing of new files
    - Automatic schema inference and evolution
    - Exactly-once processing semantics
    - Efficient handling of millions of files
    
    Returns:
        DataFrame: Streaming data from volume with metadata columns
    """
    # Configure AutoLoader options
    autoloader_options = {
        "cloudFiles.format": FILE_FORMAT,
        "cloudFiles.schemaLocation": SCHEMA_LOCATION or f"{VOLUME_PATH}/_schema",
        "cloudFiles.inferColumnTypes": "true",
        "cloudFiles.schemaEvolutionMode": "addNewColumns"
    }
    
    # Additional format-specific options
    if FILE_FORMAT == "csv":
        autoloader_options.update({
            "header": "true",
            "inferSchema": "true"
        })
    
    # Read from volume using AutoLoader
    df = (
        spark.readStream
        .format("cloudFiles")
        .options(**autoloader_options)
        .load(VOLUME_PATH)
    )
    
    # Add metadata columns
    df = add_metadata_columns(df)
    
    return df


@dlt.table(
    name=f"{config.bronze_catalog}.{config.bronze_schema}.autoloader_json_data",
    comment="Bronze layer table for JSON files from Unity Catalog Volume",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def autoloader_json_data():
    """
    Reads JSON files specifically from Unity Catalog Volume using AutoLoader.
    
    Returns:
        DataFrame: Streaming JSON data from volume
    """
    json_volume_path = spark.conf.get("json_volume_path", "/Volumes/catalog/schema/volume_name/json")
    
    df = (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", f"{json_volume_path}/_schema")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .load(json_volume_path)
    )
    
    df = add_metadata_columns(df)
    
    return df


@dlt.table(
    name=f"{config.bronze_catalog}.{config.bronze_schema}.autoloader_csv_data",
    comment="Bronze layer table for CSV files from Unity Catalog Volume",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def autoloader_csv_data():
    """
    Reads CSV files specifically from Unity Catalog Volume using AutoLoader.
    
    Returns:
        DataFrame: Streaming CSV data from volume
    """
    csv_volume_path = spark.conf.get("csv_volume_path", "/Volumes/catalog/schema/volume_name/csv")
    
    df = (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("cloudFiles.schemaLocation", f"{csv_volume_path}/_schema")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(csv_volume_path)
    )
    
    df = add_metadata_columns(df)
    
    return df
