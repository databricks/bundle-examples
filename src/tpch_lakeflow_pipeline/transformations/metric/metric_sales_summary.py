# """
# Sales metrics view aggregating fact_sales with multiple dimensions.
# Provides key business metrics for sales analysis and reporting.
# """
# import dlt
# from pyspark.sql import SparkSession
# from framework.config import Config

# # Configuration
# config = Config.from_spark_config()
# spark = SparkSession.getActiveSession()

# @dlt.table(
#     name=f"{config.gold_catalog}.{config.gold_schema}.metric_sales_summary",
#     comment="Aggregated sales metrics by customer, part, supplier, and time dimensions",
#     table_properties={
#         "quality": "gold",
#         "layer": "metric",
#         "delta.enableChangeDataFeed": "true"
#     }
# )
# def metric_sales_summary():
#     """
#     Creates metric view with aggregated sales KPIs.
    
#     Aggregates by:
#     - Calendar (order date)
#     - Customer
#     - Part
#     - Supplier
    
#     Returns:
#         DataFrame: Aggregated sales metrics with dimensional attributes
#     """
#     df = spark.sql(f"""
#         WITH base_metrics AS (
#             SELECT
#                 -- Dimension foreign keys
#                 fs.calendar_order_id,
#                 fs.customer_id,
#                 fs.part_id,
#                 fs.supplier_id,
                
#                 -- Dimension attributes for easier filtering and grouping
#                 cal.calendar_year,
#                 cal.calendar_quarter_of_year,
#                 cal.calendar_month_of_year,
#                 cal.calendar_month_name,
#                 cal.calendar_week_of_year_iso,
                
#                 cust.customer_name,
#                 cust.customer_segment,
#                 cust.customer_nation as customer_nation,
#                 cust.customer_region as customer_region,
                
#                 part.part_name,
#                 part.part_brand,
#                 part.part_type,
#                 part.part_mfgr,
                
#                 sup.supplier_name,
#                 sup.supplier_nation,
#                 sup.supplier_region,
                
#                 -- Measures from fact table
#                 fs.order_quantity,
#                 fs.order_extended_price_usd,
#                 fs.order_discount_usd,
#                 fs.order_tax_usd,
#                 fs.part_supply_cost_usd,
#                 fs.order_commit_lag_days,
#                 fs.order_receipt_lag_days,
#                 fs.order_ship_lag_days
                
#             FROM {config.gold_catalog}.{config.gold_schema}.fact_sales fs
            
#             -- Join with dimensions
#             LEFT JOIN {config.gold_catalog}.{config.gold_schema}.dim_calendar cal
#                 ON fs.calendar_order_id = cal.calendar_id
                
#             LEFT JOIN {config.gold_catalog}.{config.gold_schema}.dim_customer cust
#                 ON fs.customer_id = cust.customer_id
                
#             LEFT JOIN {config.gold_catalog}.{config.gold_schema}.dim_part part
#                 ON fs.part_id = part.part_id
                
#             LEFT JOIN {config.gold_catalog}.{config.gold_schema}.dim_supplier sup
#                 ON fs.supplier_id = sup.supplier_id
#         )
        
#         SELECT
#             -- Time dimensions
#             calendar_year,
#             calendar_quarter_of_year,
#             calendar_month_of_year,
#             calendar_month_name,
#             calendar_week_of_year_iso,
            
#             -- Customer dimensions
#             customer_id,
#             customer_name,
#             customer_segment,
#             customer_nation,
#             customer_region,
            
#             -- Part dimensions
#             part_id,
#             part_name,
#             part_brand,
#             part_type,
#             part_mfgr,
            
#             -- Supplier dimensions
#             supplier_id,
#             supplier_name,
#             supplier_nation,
#             supplier_region,
            
#             -- Volume metrics
#             count(*)                                                as total_orders,
#             sum(order_quantity)                                     as total_quantity,
            
#             -- Revenue metrics
#             sum(order_extended_price_usd)                           as total_revenue_usd,
#             avg(order_extended_price_usd)                           as avg_order_value_usd,
            
#             -- Cost and profit metrics
#             sum(part_supply_cost_usd * order_quantity)              as total_cost_usd,
#             sum(order_extended_price_usd - 
#                 (part_supply_cost_usd * order_quantity))            as total_gross_profit_usd,
#             avg((order_extended_price_usd - 
#                 (part_supply_cost_usd * order_quantity)) / 
#                 nullif(order_extended_price_usd, 0)) * 100          as avg_profit_margin_pct,
            
#             -- Discount metrics
#             sum(order_discount_usd)                                 as total_discount_usd,
#             avg(order_discount_usd / 
#                 nullif(order_extended_price_usd, 0)) * 100          as avg_discount_pct,
            
#             -- Tax metrics
#             sum(order_tax_usd)                                      as total_tax_usd,
            
#             -- Net revenue (after discount, before tax)
#             sum(order_extended_price_usd - order_discount_usd)      as total_net_revenue_usd,
            
#             -- Operational efficiency metrics
#             avg(order_commit_lag_days)                              as avg_commit_lag_days,
#             avg(order_receipt_lag_days)                             as avg_receipt_lag_days,
#             avg(order_ship_lag_days)                                as avg_ship_lag_days,
            
#             -- Metadata
#             current_timestamp()                                     as metric_calculated_at
            
#         FROM base_metrics
        
#         -- Exclude dummy/unknown dimension values from aggregations
#         WHERE customer_id > 0
#           AND part_id > 0
#           AND supplier_id > 0
#           AND calendar_order_id > 0
        
#         GROUP BY
#             -- Time dimensions
#             calendar_year,
#             calendar_quarter_of_year,
#             calendar_month_of_year,
#             calendar_month_name,
#             calendar_week_of_year_iso,
            
#             -- Customer dimensions
#             customer_id,
#             customer_name,
#             customer_segment,
#             customer_nation,
#             customer_region,
            
#             -- Part dimensions
#             part_id,
#             part_name,
#             part_brand,
#             part_type,
#             part_mfgr,
            
#             -- Supplier dimensions
#             supplier_id,
#             supplier_name,
#             supplier_nation,
#             supplier_region
#     """)
    
#     return df
