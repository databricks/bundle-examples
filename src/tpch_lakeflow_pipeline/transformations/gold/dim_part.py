"""
Part dimension table with product attributes.
"""
import dlt
from pyspark.sql import SparkSession
from framework.config import Config
from framework.dimension_utils import add_dummy_row, add_surrogate_id

# Configuration
config = Config.from_spark_config()
spark = SparkSession.getActiveSession()

# Table definition
@dlt.table(
    name=f"{config.gold_catalog}.{config.gold_schema}.dim_part",
    comment="Part dimension table with product attributes",
    table_properties={
        "quality": "gold",
        "layer": "dimension",
        "delta.enableChangeDataFeed": "true"
    }
)
def dim_part():
    """
    Creates part dimension with natural key and product attributes.
    Includes a dummy row with part_key = -1 for unknown parts.
    
    Returns:
        DataFrame: Part dimension with product attributes
    """
    df = spark.sql(f"""
        SELECT
            part.p_partkey                      as part_key,
            part.p_name                         as part_name,
            part.p_mfgr                         as part_mfgr,
            part.p_brand                        as part_brand,
            part.p_type                         as part_type,
            part.p_size                         as part_size,
            part.p_container                    as part_container,
            part.p_retailprice                  as part_retailprice,
            current_timestamp()                 as load_timestamp
        FROM
            {config.silver_catalog}.{config.silver_schema}.part part
    """)
    
    # Add surrogate ID first, then add dummy row
    df = add_surrogate_id(df, "part_id")
    df = add_dummy_row(df, "part_id")
    
    return df
