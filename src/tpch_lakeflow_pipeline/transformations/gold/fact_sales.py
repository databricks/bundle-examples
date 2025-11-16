"""
Sales fact table containing transactional sales data.
"""
import dlt
from framework.config import Config
from framework.utils import get_or_create_spark_session
from framework.fact_utils import extract_dimension_names, build_dimension_mappings, enrich_with_surrogate_keys

# Configuration
config = Config.from_spark_config()
spark = get_or_create_spark_session()
silver_catalog = config.silver_catalog
silver_schema = config.silver_schema
gold_catalog = config.gold_catalog
gold_schema = config.gold_schema


@dlt.table(
    name=f"{gold_catalog}.{gold_schema}.fact_sales",
    comment="Sales fact table containing transactional sales data with measures and foreign keys to dimension tables",
    table_properties={
        "quality": "gold",
        "layer": "fact",
        "delta.enableChangeDataFeed": "true"
    }
)
def fact_sales():
    """
    Creates sales fact table with measures and foreign keys to dimensions.
    Enriches natural keys with surrogate keys from dimension tables.
    
    Returns:
        DataFrame: Sales fact table with transactional data and surrogate keys
    """
    # Get base fact table with natural keys
    base_fact_df = spark.sql(f"""
        SELECT
            -- Foreign keys (natural keys)
            cast(date_format(orders.o_orderdate, 'yyyyMMdd') as int)        as calendar_order_id,
            cast(date_format(lineitem.l_commitdate, 'yyyyMMdd') as int)     as calendar_commit_id,
            cast(date_format(lineitem.l_receiptdate, 'yyyyMMdd') as int)    as calendar_receipt_id,
            cast(date_format(lineitem.l_shipdate, 'yyyyMMdd') as int)       as calendar_ship_id,
            orders.o_custkey                                                as customer_key,
            lineitem.l_partkey                                              as part_key,
            lineitem.l_suppkey                                              as supplier_key,

            -- Degenerate dimensions
            lineitem.l_orderkey                                             as order_header_code,
            lineitem.l_linenumber                                           as order_line_code,
            
            -- Additive measures
            lineitem.l_quantity                                             as order_quantity,
            lineitem.l_extendedprice                                        as order_extended_price_usd,
            lineitem.l_discount                                             as order_discount_usd,
            lineitem.l_tax                                                  as order_tax_usd,
            partsupp.ps_supplycost                                          as part_supply_cost_usd,
            
            -- Semi-additive measures
            datediff(lineitem.l_commitdate, orders.o_orderdate)             as order_commit_lag_days,
            datediff(lineitem.l_receiptdate, orders.o_orderdate)            as order_receipt_lag_days,
            datediff(lineitem.l_shipdate, orders.o_orderdate)               as order_ship_lag_days,
            
            -- Audit column
            current_timestamp()                                             as load_timestamp
            
        FROM 
            {silver_catalog}.{silver_schema}.lineitem as lineitem
        LEFT JOIN
            {silver_catalog}.{silver_schema}.orders as orders ON lineitem.l_orderkey = orders.o_orderkey
        LEFT JOIN
            {silver_catalog}.{silver_schema}.partsupp as partsupp ON lineitem.l_partkey = partsupp.ps_partkey AND lineitem.l_suppkey = partsupp.ps_suppkey
    """)
    
    # Extract dimension names and build mappings
    dimension_names = extract_dimension_names(base_fact_df)
    dimension_mappings = build_dimension_mappings(dimension_names)
    
    # Enrich with surrogate keys from dimension tables
    enriched_fact_df = enrich_with_surrogate_keys(
        fact_df=base_fact_df,
        dimension_mappings=dimension_mappings,
        catalog=gold_catalog,
        schema=gold_schema,
        spark=spark,
        handle_missing='use_default'  # Use -1 for missing dimension keys
    )
    
    return enriched_fact_df
