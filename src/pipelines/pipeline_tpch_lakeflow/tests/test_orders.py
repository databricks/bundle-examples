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
    name=f"{config.silver_catalog}.{config.silver_schema}.test_tpch_orders",
    comment="Test orders table with strict data quality expectations",
    private=True
)
# Null percentage expectations
@dlt.expect_or_fail("expect_custkey_null_percentage", 
                    "custkey_null_pct < 0.01")
@dlt.expect_or_fail("expect_orderstatus_null_percentage", 
                    "orderstatus_null_pct < 0.01")
@dlt.expect_or_fail("expect_totalprice_null_percentage", 
                    "totalprice_null_pct < 0.01")
def test_orders():
    """
    Creates test view for orders with strict data quality expectations:
    - No more than 1% null values in o_custkey
    - No more than 1% null values in o_orderstatus  
    - No more than 1% null values in o_totalprice
    
    """
    df = spark.sql(f"""
        SELECT
            SUM(CASE WHEN o_custkey IS NULL THEN 1 ELSE 0 END) / COUNT(*) as custkey_null_pct,
            SUM(CASE WHEN o_orderstatus IS NULL THEN 1 ELSE 0 END) / COUNT(*) as orderstatus_null_pct,
            SUM(CASE WHEN o_totalprice IS NULL THEN 1 ELSE 0 END) / COUNT(*) as totalprice_null_pct
            
        FROM {config.silver_catalog}.{config.silver_schema}.orders
        GROUP BY ALL
    """)
    
    return df
