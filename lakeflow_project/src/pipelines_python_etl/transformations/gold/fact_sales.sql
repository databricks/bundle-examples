-- Please edit the sample below

CREATE MATERIALIZED VIEW fact_sales AS
SELECT
    -- Foreign keys
    cast(date_format(orders.o_orderdate, 'yyyyMMdd') as int)        as calendar_order_id,
    cast(date_format(lineitem.l_commitdate, 'yyyyMMdd') as int)     as calendar_commit_id,
    cast(date_format(lineitem.l_receiptdate, 'yyyyMMdd') as int)    as calendar_receipt_id,
    cast(date_format(lineitem.l_shipdate, 'yyyyMMdd') as int)       as calendar_ship_id,
    orders.o_custkey                                                as customer_key,
    lineitem.l_partkey                                              as part_key,
    lineitem.l_suppkey                                              as supplier_key,

    -- Measures
    lineitem.l_orderkey                                             as order_header_code,
    lineitem.l_linenumber                                           as order_line_code,
    lineitem.l_quantity                                             as order_quantity,
    lineitem.l_extendedprice                                        as order_extended_price_usd,
    lineitem.l_discount                                             as order_discount_usd,
    lineitem.l_tax                                                  as order_tax_usd,
    partsupp.ps_supplycost                                          as part_supply_cost_usd,
    timediff(day, orders.o_orderdate, lineitem.l_commitdate)        as order_commit_lag_days,
    timediff(day, orders.o_orderdate, lineitem.l_receiptdate)       as order_receipt_lag_days,
    timediff(day, orders.o_orderdate, lineitem.l_shipdate)          as order_ship_lag_days
    
FROM 
    silver_lineitem as lineitem
LEFT JOIN
    silver_orders as orders ON lineitem.l_orderkey = orders.o_orderkey
LEFT JOIN
    silver_partsupp as partsupp ON lineitem.l_partkey = partsupp.ps_partkey AND lineitem.l_suppkey = partsupp.ps_suppkey