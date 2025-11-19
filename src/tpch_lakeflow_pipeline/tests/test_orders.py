"""
Test Orders Data Quality
This materialized view includes expectations designed to test data quality.
Some expectations are intentionally strict and may fail to demonstrate quality monitoring.
"""
import dlt
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, current_timestamp, sum as _sum, count as _count, avg as _avg
from framework.config import Config

# Configuration
config = Config.from_spark_config()
spark = SparkSession.getActiveSession()

@dlt.table(
    name=f"{config.silver_catalog}.{config.silver_schema}.TEST_tpch_orders",
    comment="TEST: Orders table with strict data quality expectations",
    private=True
)
# Null percentage expectations - these are intentionally strict and may fail
@dlt.expect_or_fail("expect_custkey_null_percentage", 
                    "(SUM(CASE WHEN o_custkey IS NULL THEN 1 ELSE 0 END) / COUNT(*) * 100) < 0.1")
@dlt.expect_or_fail("expect_orderstatus_null_percentage", 
                    "(SUM(CASE WHEN o_orderstatus IS NULL THEN 1 ELSE 0 END) / COUNT(*) * 100) < 0.5")
@dlt.expect_or_fail("expect_totalprice_null_percentage", 
                    "(SUM(CASE WHEN o_totalprice IS NULL THEN 1 ELSE 0 END) / COUNT(*) * 100) < 0.01")
def test_orders():
    """
    Creates test view for orders with strict data quality expectations.
    
    Expectations that will likely fail:
    - No more than 0.1% null values in o_custkey
    - No more than 0.5% null values in o_orderstatus  
    - No more than 0.01% null values in o_totalprice (extremely strict)
    
    Returns:
        DataFrame: Orders data with calculated quality metrics
    """
    df = spark.sql(f"""
        SELECT
            o_orderkey,
            o_custkey,
            o_orderstatus,
            o_totalprice,
            
            -- Add calculated quality metrics for testing
            CASE WHEN o_custkey IS NULL THEN 1 ELSE 0 END as has_null_custkey,
            CASE WHEN o_orderstatus IS NULL THEN 1 ELSE 0 END as has_null_status,
            CASE WHEN o_totalprice IS NULL THEN 1 ELSE 0 END as has_null_price
            
        FROM {config.silver_catalog}.{config.silver_schema}.orders
    """)
    
    return df
