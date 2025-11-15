CREATE MATERIALIZED VIEW ${gold_catalog}.${gold_schema}.fact_sales
(
    -- Foreign keys to dimension tables
    calendar_order_id INT COMMENT 'Foreign key to dim_calendar for order date (format: yyyyMMdd)',
    calendar_commit_id INT COMMENT 'Foreign key to dim_calendar for commit date (format: yyyyMMdd)',
    calendar_receipt_id INT COMMENT 'Foreign key to dim_calendar for receipt date (format: yyyyMMdd)',
    calendar_ship_id INT COMMENT 'Foreign key to dim_calendar for ship date (format: yyyyMMdd)',
    customer_key BIGINT COMMENT 'Natural business key for customer dimension',
    part_key BIGINT COMMENT 'Natural business key for part dimension',
    supplier_key BIGINT COMMENT 'Natural business key for supplier dimension',
    
    -- Degenerate dimensions (transaction identifiers)
    order_header_code BIGINT COMMENT 'Order header identifier from source system',
    order_line_code INT COMMENT 'Line number within the order',
    
    -- Additive measures
    order_quantity DECIMAL(18,2) COMMENT 'Quantity of parts ordered',
    order_extended_price_usd DECIMAL(18,2) COMMENT 'Extended price in USD (quantity * list price)',
    order_discount_usd DECIMAL(18,2) COMMENT 'Discount amount in USD',
    order_tax_usd DECIMAL(18,2) COMMENT 'Tax amount in USD',
    part_supply_cost_usd DECIMAL(18,2) COMMENT 'Cost to supply the part in USD',
    
    -- Semi-additive measures (lag calculations)
    order_commit_lag_days INT COMMENT 'Days between order date and commit date',
    order_receipt_lag_days INT COMMENT 'Days between order date and receipt date',
    order_ship_lag_days INT COMMENT 'Days between order date and ship date',
    
    -- Audit column
    load_timestamp TIMESTAMP COMMENT 'Timestamp when the record was loaded into the gold layer'
)
COMMENT 'Sales fact table containing transactional sales data with measures and foreign keys to dimension tables'
TBLPROPERTIES (
    'quality' = 'gold',
    'layer' = 'fact',
    'delta.enableChangeDataFeed' = 'true'
)
AS
SELECT
    -- Foreign keys
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
    timediff(day, orders.o_orderdate, lineitem.l_commitdate)        as order_commit_lag_days,
    timediff(day, orders.o_orderdate, lineitem.l_receiptdate)       as order_receipt_lag_days,
    timediff(day, orders.o_orderdate, lineitem.l_shipdate)          as order_ship_lag_days,
    
    -- Audit column
    current_timestamp()                                             as load_timestamp
    
FROM 
    ${silver_catalog}.${silver_schema}.lineitem as lineitem
LEFT JOIN
    ${silver_catalog}.${silver_schema}.orders as orders ON lineitem.l_orderkey = orders.o_orderkey
LEFT JOIN
    ${silver_catalog}.${silver_schema}.partsupp as partsupp ON lineitem.l_partkey = partsupp.ps_partkey AND lineitem.l_suppkey = partsupp.ps_suppkey