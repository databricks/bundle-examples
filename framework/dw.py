"""
Data Warehouse utility functions for dimension and fact table operations.

This module provides common utility functions used for building star schema
data warehouses following the Kimball methodology.
"""
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, TimestampType
from typing import Dict, Any, List

spark = SparkSession.getActiveSession()


# =============================================================================
# Dimension Table Utilities
# =============================================================================

def add_dummy_row(df: DataFrame) -> DataFrame:
    """
    Adds a dummy row to a dimension table with surrogate key -1 and 'N/A' for text fields.
    
    This is useful for handling missing or unknown dimension values in fact tables,
    following the Kimball methodology for data warehousing.
    
    Args:
        df (DataFrame): The dimension DataFrame to add a dummy row to

    Returns:
        DataFrame: The dimension DataFrame with a dummy row prepended
        
    Example:
        >>> dim_customer_df = add_dummy_row(dim_customer_df)
    """

    # Build dummy row data based on column types
    dummy_data: Dict[str, Any] = {}
    
    for field in df.schema.fields:
        column_name = field.name
        column_type = field.dataType
        
        # All columns ending with _id or _key get -1
        if column_name.endswith('_id') or column_name.endswith('_key'):
            dummy_data[column_name] = -1
        elif isinstance(column_type, (StringType,)):
            # String fields get 'N/A'
            dummy_data[column_name] = "N/A"
        elif isinstance(column_type, TimestampType):
            # Timestamp fields get epoch time (1970-01-01) as a Python datetime
            from datetime import datetime
            dummy_data[column_name] = datetime(1970, 1, 1, 0, 0, 0)
        else:
            # Decimal, Integer, and other numeric types get NULL
            dummy_data[column_name] = None
    
    # Create dummy row DataFrame
    dummy_row_df = spark.createDataFrame([dummy_data], schema=df.schema)
    
    # Union dummy row with original DataFrame
    result_df = dummy_row_df.union(df)
    
    return result_df


def add_surrogate_id(df: DataFrame, surrogate_id_column: str) -> DataFrame:
    """
    Adds a surrogate ID column to a dimension table based on the natural key.
    
    The surrogate ID is generated using monotonically_increasing_id() to ensure uniqueness,
    then adjusted to start from 1 (with -1 reserved for dummy/unknown rows).
    The surrogate ID column is placed as the first column in the DataFrame.
    
    Args:
        df (DataFrame): The dimension DataFrame
        surrogate_id_column (str): Name of the surrogate ID column to create (e.g., 'customer_id')
    
    Returns:
        DataFrame: The dimension DataFrame with surrogate ID column added as the first column
        
    Example:
        >>> df = add_surrogate_id(df, "customer_id")
    """
    # Add surrogate ID using monotonically_increasing_id
    result_df = df.withColumn(surrogate_id_column, F.monotonically_increasing_id() + 1)
    
    # Reorder columns to put surrogate_id_column first
    other_columns = [col for col in result_df.columns if col != surrogate_id_column]
    result_df = result_df.select(surrogate_id_column, *other_columns)
    
    return result_df


# =============================================================================
# Fact Table Utilities
# =============================================================================

def build_dimension_mappings(df: DataFrame) -> Dict[str, Dict[str, str]]:
    """
    Builds dimension mappings following standard naming conventions.
    
    Assumes:
    - Natural key column: <dimension>_key
    - Surrogate key column: <dimension>_id
    
    Args:
        df (DataFrame): The fact DataFrame to extract dimension mappings from
    
    Returns:
        Dict[str, Dict[str, str]]: Mapping configuration for enrich_with_surrogate_keys
        
    Example:
        >>> mappings = build_dimension_mappings(fact_df)
        >>> # Returns: {
        >>> #     'customer': {'natural_key': 'customer_key', 'surrogate_key': 'customer_id'},
        >>> #     'part': {'natural_key': 'part_key', 'surrogate_key': 'part_id'},
        >>> #     'supplier': {'natural_key': 'supplier_key', 'surrogate_key': 'supplier_id'}
        >>> # }
    """
    dimension_names = []
    
    for column_name in df.columns:
        if column_name.endswith('_key'):
            # Extract dimension name by removing '_key' suffix
            dimension_name = column_name[:-4]  # Remove last 4 characters ('_key')
            dimension_names.append(dimension_name)
    
    mappings = {}
    
    for dim_name in dimension_names:
        mappings[dim_name] = {
            'natural_key': f'{dim_name}_key',
            'surrogate_key': f'{dim_name}_id'
        }
    
    return mappings


def enrich_with_surrogate_keys(
    fact_df: DataFrame,
    dimension_mappings: Dict[str, Dict[str, str]],
    catalog: str,
    schema: str,
    handle_missing: str = 'use_default'
) -> DataFrame:
    """
    Enriches a fact table with surrogate keys from dimension tables.
    
    Performs lookups in dimension tables to replace natural keys with surrogate keys.
    Follows the pattern: <dimension>_key (natural) -> <dimension>_id (surrogate)
    
    Args:
        fact_df (DataFrame): The fact table DataFrame with natural keys
        dimension_mappings (Dict[str, Dict[str, str]]): Mapping of dimension names to their column mappings.
            Format: {
                'dimension_name': {
                    'natural_key': 'column_name_in_dimension',
                    'surrogate_key': 'surrogate_column_name'
                }
            }
            Example: {
                'customer': {'natural_key': 'customer_key', 'surrogate_key': 'customer_id'},
                'part': {'natural_key': 'part_key', 'surrogate_key': 'part_id'}
            }
        catalog (str): Target catalog where dimension tables reside
        schema (str): Target schema where dimension tables reside
        handle_missing (str): How to handle missing dimension keys.
            'use_default': Use -1 for missing keys (default)
            'drop': Drop rows with missing keys
            'keep_null': Keep NULL for missing keys
    
    Returns:
        DataFrame: Fact table with surrogate keys added
        
    Example:
        >>> mappings = {
        ...     'customer': {'natural_key': 'customer_key', 'surrogate_key': 'customer_id'},
        ...     'part': {'natural_key': 'part_key', 'surrogate_key': 'part_id'}
        ... }
        >>> enriched_fact = enrich_with_surrogate_keys(fact_df, mappings, 'gold_catalog', 'gold_schema')
    """
    
    for dimension_name, mapping in dimension_mappings.items():
        natural_key_col = mapping['natural_key']
        surrogate_key_col = mapping['surrogate_key']
               
        # Read dimension table
        dim_table_path = f"{catalog}.{schema}.dim_{dimension_name}"
        
        try:
            dim_df = spark.read.table(dim_table_path)
        except Exception as e:
            print(f"Warning: Could not read dimension table {dim_table_path}: {e}")
            continue
        
        # Select only the natural key and surrogate key from dimension
        dim_lookup = dim_df.select(
            F.col(natural_key_col),
            F.col(surrogate_key_col)
        )
        
        # Join fact table with dimension lookup
        fact_df = fact_df.join(
            dim_lookup,
            fact_df[natural_key_col] == dim_lookup[natural_key_col],
            "left"
        ).drop(natural_key_col)

        # Handle missing keys based on strategy
        if handle_missing == 'use_default':
            # Replace NULL surrogate keys with -1
            fact_df = fact_df.withColumn(
                surrogate_key_col,
                F.coalesce(F.col(surrogate_key_col), F.lit(-1))
            )
            
        elif handle_missing == 'drop':
            # Drop rows where surrogate key is NULL
            fact_df = fact_df.filter(F.col(surrogate_key_col).isNotNull())

    # Reorder columns: all _id columns first, then all other columns
    id_columns = [col for col in fact_df.columns if col.endswith('_id')]
    other_columns = [col for col in fact_df.columns if not col.endswith('_id')]
    fact_df = fact_df.select(id_columns + other_columns)

    return fact_df
