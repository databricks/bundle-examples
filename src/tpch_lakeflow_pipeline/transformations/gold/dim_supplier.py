"""
Supplier dimension table with enriched attributes.
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
    name=f"{gold_catalog}.{gold_schema}.dim_supplier",
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
            {silver_catalog}.{silver_schema}.supplier sup
        LEFT JOIN
            {silver_catalog}.{silver_schema}.nation nat ON sup.s_nationkey = nat.n_nationkey
        LEFT JOIN
            {silver_catalog}.{silver_schema}.region reg ON nat.n_regionkey = reg.r_regionkey
    """)
    
    return add_dummy_row(df, "supplier_key", spark)
