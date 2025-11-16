"""
Customer dimension table with enriched attributes.
"""
import dlt
from framework.config import Config
from framework.utils import get_or_create_spark_session
from framework.dimension_utils import add_dummy_row

# Configuration
config = Config.from_spark_config()
spark = get_or_create_spark_session()
silver_catalog = config.silver_catalog
silver_schema = config.silver_schema
gold_catalog = config.gold_catalog
gold_schema = config.gold_schema


@dlt.table(
    name=f"{gold_catalog}.{gold_schema}.dim_customer",
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
            {silver_catalog}.{silver_schema}.customer cust
        LEFT JOIN
            {silver_catalog}.{silver_schema}.nation nat ON cust.c_nationkey = nat.n_nationkey
        LEFT JOIN
            {silver_catalog}.{silver_schema}.region reg ON nat.n_regionkey = reg.r_regionkey
    """)
    
    return add_dummy_row(df, "customer_key", spark)
