"""
Tests for the Lakehouse Framework.

This module contains unit tests for the lakehouse framework package.
"""

import pytest
from lakehouse_framework.utils import get_catalog_schema, get_table_path
from lakehouse_framework.config import MedallionConfig


def test_get_catalog_schema():
    """Test catalog schema path construction."""
    result = get_catalog_schema("my_catalog", "my_schema")
    assert result == "my_catalog.my_schema"


def test_get_table_path():
    """Test table path construction."""
    result = get_table_path("my_catalog", "my_schema", "my_table")
    assert result == "my_catalog.my_schema.my_table"


def test_medallion_config_creation():
    """Test MedallionConfig creation."""
    config = MedallionConfig(
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
    """Test getting layer paths from MedallionConfig."""
    config = MedallionConfig(
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
    config = MedallionConfig(
        bronze_catalog="catalog",
        bronze_schema="bronze",
        silver_catalog="catalog",
        silver_schema="silver",
        gold_catalog="catalog",
        gold_schema="gold"
    )
    
    with pytest.raises(ValueError, match="Invalid layer"):
        config.get_layer_path("platinum")
