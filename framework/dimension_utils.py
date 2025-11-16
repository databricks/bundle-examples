"""
Utility functions for dimension table operations.
"""
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, TimestampType
from typing import Dict, Any, List
spark = SparkSession.getActiveSession()

def add_dimension_metadata(df: DataFrame, metadata_columns: List[str] = None) -> DataFrame:
    """
    Adds metadata columns to a dimension DataFrame.
    
    By default, adds 'load_timestamp' column. Can be extended to add other metadata columns
    like 'created_by', 'updated_timestamp', 'source_system', etc.
    
    Args:
        df (DataFrame): The dimension DataFrame to add metadata to
        metadata_columns (List[str], optional): List of metadata columns to add.
            Supported values: 'load_timestamp', 'created_timestamp', 'updated_timestamp',
            'source_system', 'is_current', 'valid_from', 'valid_to'
            If None, defaults to ['load_timestamp']
    
    Returns:
        DataFrame: The dimension DataFrame with metadata columns added
        
    Example:
        >>> df = add_dimension_metadata(df)  # Adds load_timestamp
        >>> df = add_dimension_metadata(df, ['load_timestamp', 'source_system'])
    """
    if metadata_columns is None:
        metadata_columns = ['load_timestamp']
    
    result_df = df
    
    for column in metadata_columns:
        if column == 'load_timestamp':
            result_df = result_df.withColumn('load_timestamp', F.current_timestamp())
        elif column == 'created_timestamp':
            result_df = result_df.withColumn('created_timestamp', F.current_timestamp())
        elif column == 'updated_timestamp':
            result_df = result_df.withColumn('updated_timestamp', F.current_timestamp())
        elif column == 'source_system':
            result_df = result_df.withColumn('source_system', F.lit('TPC-H'))
        elif column == 'is_current':
            result_df = result_df.withColumn('is_current', F.lit(True))
        elif column == 'valid_from':
            result_df = result_df.withColumn('valid_from', F.current_timestamp())
        elif column == 'valid_to':
            result_df = result_df.withColumn('valid_to', F.lit(None).cast(TimestampType()))
        else:
            raise ValueError(f"Unsupported metadata column: {column}")
    
    return result_df


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
    
    Args:
        df (DataFrame): The dimension DataFrame
        surrogate_id_column (str): Name of the surrogate ID column to create (e.g., 'customer_id')
    
    Returns:
        DataFrame: The dimension DataFrame with surrogate ID column added
        
    Example:
        >>> df = add_surrogate_id(df, "customer_id")
    """
    # Add surrogate ID using monotonically_increasing_id
    result_df = df.withColumn(surrogate_id_column, F.monotonically_increasing_id() + 1)
    
    return result_df
