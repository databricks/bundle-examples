"""
Utility functions for fact table operations.
"""
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from typing import List, Dict, Optional
spark = SparkSession.getActiveSession()


def build_dimension_mappings(df: DataFrame) -> Dict[str, Dict[str, str]]:
    """
    Builds dimension mappings following standard naming conventions.
    
    Assumes:
    - Natural key column: <dimension>_key
    - Surrogate key column: <dimension>_id
    
    Args:
        dimension_names (List[str]): List of dimension names
    
    Returns:
        Dict[str, Dict[str, str]]: Mapping configuration for enrich_with_surrogate_keys
        
    Example:
        >>> mappings = build_dimension_mappings(['customer', 'part', 'supplier'])
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
