"""
Customer dimension table with enriched attributes.
"""
import dlt
from pyspark.sql import SparkSession
from framework.config import Config
from framework.utils import add_metadata_columns
from framework.dimension_utils import add_dummy_row, add_surrogate_id

# Configuration
config = Config.from_spark_config()
spark = SparkSession.getActiveSession()

# Table definition
@dlt.table(
    name=f"{config.gold_catalog}.{config.gold_schema}.dim_customer",
    comment="Customer dimension table with enriched attributes",
    table_properties={
        "quality": "gold",
        "layer": "dimension",
        "delta.enableChangeDataFeed": "true"
    }
)
def dim_customer():
    """
    Creates customer dimension with natural key and enriched attributes.
    Includes a dummy row with customer_key = -1 for unknown customers.
    
    Returns:
        DataFrame: Customer dimension with attributes from customer, nation, and region
    """
    df = spark.sql(f"""
        SELECT
            cust.c_custkey                      as customer_key,
            cust.c_name                         as customer_name,
            cust.c_address                      as customer_address,
            cust.c_phone                        as customer_phone,
            cust.c_mktsegment                   as customer_segment,
            coalesce(nat.n_name, 'Unknown')     as customer_nation,
            coalesce(reg.r_name, 'Unknown')     as customer_region,
            cust.c_acctbal                      as customer_acctbal,
            current_timestamp()                 as load_timestamp
        FROM
            {config.silver_catalog}.{config.silver_schema}.customer cust
        LEFT JOIN
            {config.silver_catalog}.{config.silver_schema}.nation nat ON cust.c_nationkey = nat.n_nationkey
        LEFT JOIN
            {config.silver_catalog}.{config.silver_schema}.region reg ON nat.n_regionkey = reg.r_regionkey
    """)
    
    # Add surrogate ID first, then add dummy row
    df = add_surrogate_id(df, "customer_id")
    df = add_metadata_columns(df)
    df = add_dummy_row(df)
    
    return df
