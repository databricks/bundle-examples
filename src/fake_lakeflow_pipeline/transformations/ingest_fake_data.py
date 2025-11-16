"""
Ingest data from custom Faker data source into bronze layer.
"""
import dlt
import sys
from pathlib import Path
from pyspark.sql import SparkSession
from framework.config import Config
from framework.utils import add_metadata_columns

# Add data_sources directory to path
data_sources_path = Path(__file__).parent.parent / "data_sources"
sys.path.insert(0, str(data_sources_path))

# Import the FakeDataSource
from fake_data_source import FakeDataSource

# Configuration
config = Config.from_spark_config()
spark = SparkSession.getActiveSession()

# Register the data source
spark.dataSource.register(FakeDataSource)


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

