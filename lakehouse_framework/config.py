"""
Configuration management for the Lakehouse Framework.

This module handles loading and managing configuration for the lakeflow pipelines.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MedallionConfig:
    """
    Configuration for medallion architecture layers.
    
    Attributes:
        bronze_catalog: Catalog name for bronze layer
        bronze_schema: Schema name for bronze layer
        silver_catalog: Catalog name for silver layer
        silver_schema: Schema name for silver layer
        gold_catalog: Catalog name for gold layer
        gold_schema: Schema name for gold layer
    """
    bronze_catalog: str
    bronze_schema: str
    silver_catalog: str
    silver_schema: str
    gold_catalog: str
    gold_schema: str
    
    @classmethod
    def from_spark_config(cls) -> "MedallionConfig":
        """
        Load configuration from Spark configuration.
        
        Returns:
            MedallionConfig instance populated from Spark config
        """
        from lakehouse_framework.utils import get_spark_config
        
        return cls(
            bronze_catalog=get_spark_config("bronze_catalog", "catalog"),
            bronze_schema=get_spark_config("bronze_schema", "bronze"),
            silver_catalog=get_spark_config("silver_catalog", "catalog"),
            silver_schema=get_spark_config("silver_schema", "silver"),
            gold_catalog=get_spark_config("gold_catalog", "catalog"),
            gold_schema=get_spark_config("gold_schema", "gold"),
        )
    
    def get_layer_path(self, layer: str) -> str:
        """
        Get the fully qualified catalog.schema path for a medallion layer.
        
        Args:
            layer: Layer name (bronze, silver, or gold)
            
        Returns:
            Fully qualified catalog.schema string
        """
        layer = layer.lower()
        if layer == "bronze":
            return f"{self.bronze_catalog}.{self.bronze_schema}"
        elif layer == "silver":
            return f"{self.silver_catalog}.{self.silver_schema}"
        elif layer == "gold":
            return f"{self.gold_catalog}.{self.gold_schema}"
        else:
            raise ValueError(f"Invalid layer: {layer}. Must be bronze, silver, or gold.")
