"""
Write utilities for creating Delta Live Tables with metadata.
"""
import dlt
from typing import Dict, List, Callable, Optional
from pyspark.sql import DataFrame


def create_dlt_table(
    table_name: str,
    catalog: str,
    schema: str,
    description: str,
    primary_keys: List[str],
    quality_level: str,
    source_function: Callable[[], DataFrame],
    expectations_warn: Optional[Dict[str, str]] = None,
    expectations_fail_update: Optional[Dict[str, str]] = None,
    expectations_drop_row: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, any]] = None,
    additional_properties: Optional[Dict[str, str]] = None
):
    """
    Creates a Delta Live Table (materialized view) with metadata and data quality expectations.
    
    Args:
        table_name (str): Name of the table to create
        catalog (str): Target catalog name
        schema (str): Target schema name
        description (str): Table description/comment
        primary_keys (List[str]): List of primary key column names
        quality_level (str): Quality level (bronze, silver, gold)
        source_function (Callable): Function that returns the source DataFrame
        expectations_warn (Dict[str, str], optional): Expectations that log warnings but allow data through
        expectations_fail_update (Dict[str, str], optional): Expectations that fail the pipeline update if violated
        expectations_drop_row (Dict[str, str], optional): Expectations that drop rows that don't meet criteria
        metadata (Dict[str, any], optional): Metadata tags to add to table properties
        additional_properties (Dict[str, str], optional): Additional table properties
    
    Returns:
        Function: The decorated DLT table function
    """
    # Build table properties
    table_properties = {
        "quality": quality_level,
        "pipelines.autoOptimize.managed": "true",
        "primary_key": ", ".join(primary_keys)
    }
    
    # Add metadata as table tags
    if metadata:
        for key, value in metadata.items():
            table_properties[f"metadata.{key}"] = str(value)
    
    # Add any additional properties
    if additional_properties:
        table_properties.update(additional_properties)
    
    # Create the DLT table decorator
    @dlt.table(
        name=f"{catalog}.{schema}.{table_name}",
        comment=description,
        table_properties=table_properties
    )
    @dlt.expect_all_or_drop({f"{pk}_not_null": f"{pk} IS NOT NULL" for pk in primary_keys})
    def table_function():
        """
        Generated table function that applies expectations and returns the source DataFrame.
        """
        return source_function()
    
    # Apply expectations based on type
    # Apply warn expectations (log warnings but don't drop or fail)
    if expectations_warn:
        table_function = dlt.expect_all(expectations_warn)(table_function)
    
    # Apply fail_update expectations (fail the pipeline if violated)
    if expectations_fail_update:
        table_function = dlt.expect_all_or_fail(expectations_fail_update)(table_function)
    
    # Apply drop_row expectations (drop rows that don't meet criteria)
    if expectations_drop_row:
        table_function = dlt.expect_all_or_drop(expectations_drop_row)(table_function)
    
    return table_function
