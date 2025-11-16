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
    VOLUME_PATH = f"{config.bronze_catalog}.{config.bronze_schema}.landing_zone"

    autoloader_options = {
        "cloudFiles.format": "json",
        "cloudFiles.schemaLocation": f"{VOLUME_PATH}/_schema",
        "cloudFiles.inferColumnTypes": "true",
        "cloudFiles.schemaEvolutionMode": "addNewColumns"
    }
    
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