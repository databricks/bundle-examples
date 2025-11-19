-- Test Orders Data Quality
-- This materialized view includes expectations designed to test data quality
-- Some expectations are intentionally strict and may fail to demonstrate quality monitoring

CREATE OR REFRESH MATERIALIZED VIEW test_orders
COMMENT 'Test view for orders table with strict data quality expectations'
TBLPROPERTIES (
  'quality' = 'test',
  'pipelines.autoOptimize.managed' = 'true'
)
AS SELECT
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
  
FROM ${catalog}.${schema}.orders;

-- Expectations that will likely fail:

-- Expect no more than 0.1% null values in o_custkey
-- This is very strict and will fail if there are any nulls in a reasonably sized dataset
CONSTRAINT expect_custkey_null_percentage
EXPECT (
  (SELECT SUM(has_null_custkey) / COUNT(*) * 100 FROM test_orders) < 0.1
) ON VIOLATION FAIL UPDATE;

-- Expect no more than 0.5% null values in o_orderstatus
-- This strict check will fail if data quality is not perfect
CONSTRAINT expect_orderstatus_null_percentage
EXPECT (
  (SELECT SUM(has_null_status) / COUNT(*) * 100 FROM test_orders) < 0.5
) ON VIOLATION FAIL UPDATE;

-- Expect no more than 0.01% null values in o_totalprice
-- Extremely strict - almost no nulls allowed
CONSTRAINT expect_totalprice_null_percentage
EXPECT (
  (SELECT SUM(has_null_price) / COUNT(*) * 100 FROM test_orders) < 0.01
) ON VIOLATION FAIL UPDATE;

-- Expect no more than 0.1% null values in o_orderdate
-- Critical field should have very few nulls
CONSTRAINT expect_orderdate_null_percentage
EXPECT (
  (SELECT SUM(has_null_orderdate) / COUNT(*) * 100 FROM test_orders) < 0.1
) ON VIOLATION FAIL UPDATE;

-- Expect no more than 1% null values in o_orderpriority
CONSTRAINT expect_orderpriority_null_percentage
EXPECT (
  (SELECT SUM(has_null_priority) / COUNT(*) * 100 FROM test_orders) < 1.0
) ON VIOLATION FAIL UPDATE;

-- Expect no more than 2% null values in o_clerk
CONSTRAINT expect_clerk_null_percentage
EXPECT (
  (SELECT SUM(has_null_clerk) / COUNT(*) * 100 FROM test_orders) < 2.0
) ON VIOLATION FAIL UPDATE;

-- Additional strict expectations that may fail:

-- Expect average order total to be within reasonable range
CONSTRAINT expect_reasonable_avg_order_total
EXPECT (
  (SELECT AVG(o_totalprice) FROM test_orders WHERE o_totalprice IS NOT NULL) BETWEEN 10000 AND 500000
) ON VIOLATION FAIL UPDATE;

-- Expect at least 95% of orders have valid status codes
CONSTRAINT expect_valid_status_percentage
EXPECT (
  (SELECT COUNT(*) FROM test_orders WHERE o_orderstatus IN ('O', 'F', 'P')) / 
  (SELECT COUNT(*) FROM test_orders) * 100 >= 95
) ON VIOLATION FAIL UPDATE;

-- Expect at least 90% of orders have valid priority codes
CONSTRAINT expect_valid_priority_percentage
EXPECT (
  (SELECT COUNT(*) FROM test_orders 
   WHERE o_orderpriority IN ('1-URGENT', '2-HIGH', '3-MEDIUM', '4-NOT SPECIFIED', '5-LOW')) / 
  (SELECT COUNT(*) FROM test_orders) * 100 >= 90
) ON VIOLATION FAIL UPDATE;

-- Expect very few (< 0.01%) orders with negative or zero total price
-- This is intentionally strict to catch any data anomalies
CONSTRAINT expect_positive_totalprice_percentage
EXPECT (
  (SELECT COUNT(*) FROM test_orders WHERE o_totalprice <= 0) / 
  (SELECT COUNT(*) FROM test_orders) * 100 < 0.01
) ON VIOLATION FAIL UPDATE;
