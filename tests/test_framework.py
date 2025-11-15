"""
Tests for the Lakehouse Framework.

This module contains unit tests for the lakehouse framework package.
"""

import pytest
from framework.utils import get_catalog_schema, get_table_path, add_metadata_columns, get_or_create_spark_session
from framework.config import Config

# Try to create Spark session, skip Spark tests if not available
try:
    spark = get_or_create_spark_session()
    SPARK_AVAILABLE = True
except Exception:
    SPARK_AVAILABLE = False
    spark = None

def test_get_catalog_schema():
    """Test catalog schema path construction."""
    result = get_catalog_schema("my_catalog", "my_schema")
    assert result == "my_catalog.my_schema"


def test_get_table_path():
    """Test table path construction."""
    result = get_table_path("my_catalog", "my_schema", "my_table")
    assert result == "my_catalog.my_schema.my_table"


def test_medallion_config_creation():
    """Test Config creation."""
    config = Config(
        bronze_catalog="catalog",
        bronze_schema="bronze",
        silver_catalog="catalog",
        silver_schema="silver",
        gold_catalog="catalog",
        gold_schema="gold"
    )
    
    assert config.bronze_catalog == "catalog"
    assert config.bronze_schema == "bronze"
    assert config.silver_catalog == "catalog"
    assert config.silver_schema == "silver"
    assert config.gold_catalog == "catalog"
    assert config.gold_schema == "gold"


def test_medallion_config_get_layer_path():
    """Test getting layer paths from Config."""
    config = Config(
        bronze_catalog="catalog",
        bronze_schema="bronze",
        silver_catalog="catalog",
        silver_schema="silver",
        gold_catalog="catalog",
        gold_schema="gold"
    )
    
    assert config.get_layer_path("bronze") == "catalog.bronze"
    assert config.get_layer_path("silver") == "catalog.silver"
    assert config.get_layer_path("gold") == "catalog.gold"


def test_medallion_config_invalid_layer():
    """Test that invalid layer raises ValueError."""
    config = Config(
        bronze_catalog="catalog",
        bronze_schema="bronze",
        silver_catalog="catalog",
        silver_schema="silver",
        gold_catalog="catalog",
        gold_schema="gold"
    )
    
    with pytest.raises(ValueError, match="Invalid layer"):
        config.get_layer_path("platinum")


@pytest.mark.skipif(True, reason="Requires Spark/Java environment")
def test_add_metadata_columns():
    """Test adding metadata columns to a DataFrame with real Spark."""
    from pyspark.sql import SparkSession
    from pyspark.sql.types import StructType, StructField, StringType, IntegerType
    
    # Create a local Spark session for testing
    spark = SparkSession.builder \
        .appName("test_add_metadata_columns") \
        .master("local[1]") \
        .getOrCreate()
    
    try:
        # Create a sample DataFrame
        schema = StructType([
            StructField("id", IntegerType(), True),
            StructField("name", StringType(), True)
        ])
        data = [(1, "Alice"), (2, "Bob"), (3, "Charlie")]
        df = spark.createDataFrame(data, schema)
        
        # Verify original DataFrame has 2 columns
        assert len(df.columns) == 2
        assert "ingest_timestamp" not in df.columns
        
        # Add metadata columns
        result_df = add_metadata_columns(df)
        
        # Verify new DataFrame has 3 columns
        assert len(result_df.columns) == 3
        assert "ingest_timestamp" in result_df.columns
        assert "id" in result_df.columns
        assert "name" in result_df.columns
        
        # Verify the ingest_timestamp column has values
        assert result_df.count() == 3
        timestamps = result_df.select("ingest_timestamp").collect()
        for row in timestamps:
            assert row.ingest_timestamp is not None
            
    finally:
        spark.stop()


@pytest.mark.skipif(True, reason="Requires Spark/Java environment")
def test_get_or_create_spark_session():
    """Test getting or creating a Spark session."""
    # First call should create a new session
    spark1 = get_or_create_spark_session("test_app")
    assert spark1 is not None
    assert spark1.sparkContext.appName == "test_app"
    
    try:
        # Second call should return the same session
        spark2 = get_or_create_spark_session("different_app")
        assert spark2 is not None
        assert spark1 == spark2  # Should be the same instance
        
    finally:
        spark1.stop()
