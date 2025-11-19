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
    name=f"{config.silver_catalog}.{config.silver_schema}.test_orders",
    comment="Test view for orders table with strict data quality expectations",
    table_properties={
        "quality": "test",
        "pipelines.autoOptimize.managed": "true"
    }
)
# Null percentage expectations - these are intentionally strict and may fail
@dlt.expect_or_fail("expect_custkey_null_percentage", 
                    "(SUM(CASE WHEN o_custkey IS NULL THEN 1 ELSE 0 END) / COUNT(*) * 100) < 0.1")
@dlt.expect_or_fail("expect_orderstatus_null_percentage", 
                    "(SUM(CASE WHEN o_orderstatus IS NULL THEN 1 ELSE 0 END) / COUNT(*) * 100) < 0.5")
@dlt.expect_or_fail("expect_totalprice_null_percentage", 
                    "(SUM(CASE WHEN o_totalprice IS NULL THEN 1 ELSE 0 END) / COUNT(*) * 100) < 0.01")
@dlt.expect_or_fail("expect_orderdate_null_percentage", 
                    "(SUM(CASE WHEN o_orderdate IS NULL THEN 1 ELSE 0 END) / COUNT(*) * 100) < 0.1")
@dlt.expect_or_fail("expect_orderpriority_null_percentage", 
                    "(SUM(CASE WHEN o_orderpriority IS NULL THEN 1 ELSE 0 END) / COUNT(*) * 100) < 1.0")
@dlt.expect_or_fail("expect_clerk_null_percentage", 
                    "(SUM(CASE WHEN o_clerk IS NULL THEN 1 ELSE 0 END) / COUNT(*) * 100) < 2.0")
# Additional strict expectations
@dlt.expect_or_fail("expect_valid_status_percentage", 
                    "(SUM(CASE WHEN o_orderstatus IN ('O', 'F', 'P') THEN 1 ELSE 0 END) / COUNT(*) * 100) >= 95")
@dlt.expect_or_fail("expect_valid_priority_percentage", 
                    "(SUM(CASE WHEN o_orderpriority IN ('1-URGENT', '2-HIGH', '3-MEDIUM', '4-NOT SPECIFIED', '5-LOW') THEN 1 ELSE 0 END) / COUNT(*) * 100) >= 90")
@dlt.expect_or_fail("expect_positive_totalprice_percentage", 
                    "(SUM(CASE WHEN o_totalprice <= 0 THEN 1 ELSE 0 END) / COUNT(*) * 100) < 0.01")
def test_orders():
    """
    Creates test view for orders with strict data quality expectations.
    
    Expectations that will likely fail:
    - No more than 0.1% null values in o_custkey
    - No more than 0.5% null values in o_orderstatus  
    - No more than 0.01% null values in o_totalprice (extremely strict)
    - No more than 0.1% null values in o_orderdate
    - No more than 1% null values in o_orderpriority
    - No more than 2% null values in o_clerk
    - At least 95% of orders have valid status codes
    - At least 90% of orders have valid priority codes
    - Less than 0.01% orders with zero/negative total price
    
    Returns:
        DataFrame: Orders data with calculated quality metrics
    """
    df = spark.sql(f"""
        SELECT
            o_orderkey,
            o_custkey,
            o_orderstatus,
            o_totalprice,
            o_orderdate,
            o_orderpriority,
            o_clerk,
            o_shippriority,
            o_comment,
            
            -- Add calculated quality metrics for testing
            CASE WHEN o_custkey IS NULL THEN 1 ELSE 0 END as has_null_custkey,
            CASE WHEN o_orderstatus IS NULL THEN 1 ELSE 0 END as has_null_status,
            CASE WHEN o_totalprice IS NULL THEN 1 ELSE 0 END as has_null_price,
            CASE WHEN o_orderdate IS NULL THEN 1 ELSE 0 END as has_null_orderdate,
            CASE WHEN o_orderpriority IS NULL THEN 1 ELSE 0 END as has_null_priority,
            CASE WHEN o_clerk IS NULL THEN 1 ELSE 0 END as has_null_clerk,
            
            current_timestamp() as test_timestamp
            
        FROM {config.silver_catalog}.{config.silver_schema}.orders
    """)
    
    return df
