"""
Supplier dimension table with enriched attributes.
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
    name=f"{config.gold_catalog}.{config.gold_schema}.dim_supplier",
    comment="Supplier dimension table with enriched attributes",
    table_properties={
        "quality": "gold",
        "layer": "dimension",
        "delta.enableChangeDataFeed": "true"
    }
)
def dim_supplier():
    """
    Creates supplier dimension with natural key and enriched attributes.
    Includes a dummy row with supplier_key = -1 for unknown suppliers.
    
    Returns:
        DataFrame: Supplier dimension with attributes from supplier, nation, and region
    """
    df = spark.sql(f"""
        SELECT
            sup.s_suppkey                      as supplier_key,
            sup.s_name                         as supplier_name,
            sup.s_address                      as supplier_address,
            sup.s_phone                        as supplier_phone,
            coalesce(nat.n_name, 'Unknown')    as supplier_nation,
            coalesce(reg.r_name, 'Unknown')    as supplier_region,
            sup.s_acctbal                      as supplier_acctbal,
            current_timestamp()                as load_timestamp
        FROM
            {config.silver_catalog}.{config.silver_schema}.supplier sup
        LEFT JOIN
            {config.silver_catalog}.{config.silver_schema}.nation nat ON sup.s_nationkey = nat.n_nationkey
        LEFT JOIN
            {config.silver_catalog}.{config.silver_schema}.region reg ON nat.n_regionkey = reg.r_regionkey
    """)
    
    # Add surrogate ID first, then add dummy row
    df = add_surrogate_id(df, "supplier_id")
    df = add_dummy_row(df)
    
    return df
