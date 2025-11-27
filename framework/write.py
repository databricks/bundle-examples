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

    # Create the DLT table decorator
    @dlt.table(
        name=table_name,
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
