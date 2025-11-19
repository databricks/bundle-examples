"""
Ingest data from custom Faker data source into bronze layer.
"""
import dlt
from pyspark.sql import SparkSession
from pyspark.sql.datasource import DataSource, DataSourceReader
from pyspark.sql.types import StructType
from framework.config import Config
from framework.utils import add_metadata_columns


# Configuration
config = Config.from_spark_config()
spark = SparkSession.getActiveSession()

# Table definition
@dlt.table(
    name=f"{config.bronze_catalog}.{config.bronze_schema}.fake_data",
    comment="Bronze layer table with synthetic data from Faker data source",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def fake_data():
    """
    Reads synthetic data from custom Faker data source.
    Schema: name, date, zipcode, state
    
    Returns:
        DataFrame: Raw fake data with metadata columns
    """
    # Read from custom Faker data source
    df = spark.read.format("fake").option("numRows", "1000").load()
    
    # Add metadata columns
    df = add_metadata_columns(df)
    
    return df

