"""
Write utilities for creating Delta Live Tables with metadata.
"""
import dlt
from typing import Dict, List, Callable, Optional
from pyspark.sql import DataFrame


def create_dlt_table(
    table_name: str,
    source_function: Callable[[], DataFrame],
    description: Optional[str] = "",
    primary_keys: Optional[List[str]] = [],
    expectations_warn: Optional[Dict[str, str]] = {},
    expectations_fail_update: Optional[Dict[str, str]] = {},
    expectations_drop_row: Optional[Dict[str, str]] = {},
    table_properties: Optional[Dict[str, str]] = {}
):
    """
    Creates a Delta Live Table (materialized view) with metadata and data quality expectations.
    
    Args:
        table_name (str): Full name of the table to create (catalog.schema.table)
        source_function (Callable): Function that returns the source DataFrame
        description (str, optional): Table description/comment
        primary_keys (List[str], optional): List of primary key column names
        expectations_warn (Dict[str, str], optional): Expectations that log warnings but allow data through
        expectations_fail_update (Dict[str, str], optional): Expectations that fail the pipeline update if violated
        expectations_drop_row (Dict[str, str], optional): Expectations that drop rows that don't meet criteria
        table_properties (Dict[str, str], optional): Table properties to set
    
    Returns:
        Function: The decorated DLT table function
    """
    
    # Validate argument defaults
    if primary_keys is None:
        primary_keys = []
    if expectations_warn is None:
        expectations_warn = {}
    if expectations_fail_update is None:
        expectations_fail_update = {}
    if expectations_drop_row is None:
        expectations_drop_row = {}
    if table_properties is None:
        table_properties = {}

    # Validate argument types
    if not isinstance(table_name, str):
        raise TypeError(f"table_name must be a str, got {type(table_name).__name__}")
    
    if not callable(source_function):
        raise TypeError(f"source_function must be callable, got {type(source_function).__name__}")
    
    if not isinstance(description, str):
        raise TypeError(f"description must be a str, got {type(description).__name__}")
    
    if not isinstance(primary_keys, list):
        raise TypeError(f"primary_keys must be a list, got {type(primary_keys).__name__}")
    
    if not all(isinstance(pk, str) for pk in primary_keys):
        raise TypeError("All items in primary_keys must be strings")
    
    if not isinstance(expectations_warn, dict):
        raise TypeError(f"expectations_warn must be a dict, got {type(expectations_warn).__name__}")
    
    if not isinstance(expectations_fail_update, dict):
        raise TypeError(f"expectations_fail_update must be a dict, got {type(expectations_fail_update).__name__}")
    
    if not isinstance(expectations_drop_row, dict):
        raise TypeError(f"expectations_drop_row must be a dict, got {type(expectations_drop_row).__name__}")
    
    if not isinstance(table_properties, dict):
        raise TypeError(f"table_properties must be a dict, got {type(table_properties).__name__}")

    # Create the DLT table decorator
    @dlt.table(
        name=table_name,
        comment=description,
        table_properties=table_properties
    )
    @dlt.expect_all_or_drop({f"{pk}_not_null": f"{pk} IS NOT NULL" for pk in primary_keys})
    @dlt.expect_all(expectations_warn)
    @dlt.expect_all_or_fail(expectations_fail_update)
    @dlt.expect_all_or_drop(expectations_drop_row)
    def table_function():
        """
        Generated table function that applies expectations and returns the source DataFrame.
        """
        return source_function()
    
    return table_function
