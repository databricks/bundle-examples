"""
Time-based sales metrics for trend analysis.
Provides aggregated metrics at different time grains.
"""
import dlt
from pyspark.sql import SparkSession
from framework.config import Config

# Configuration
config = Config.from_spark_config()
spark = SparkSession.getActiveSession()

@dlt.table(
    name=f"{config.gold_catalog}.{config.gold_schema}.metric_sales_by_time",
    comment="Sales metrics aggregated by time dimensions (year, quarter, month, week)",
    table_properties={
        "quality": "gold",
        "layer": "metric",
        "delta.enableChangeDataFeed": "true"
    }
)
def metric_sales_by_time():
    """
    Creates time-based sales metrics for trend analysis.
    
    Returns:
        DataFrame: Sales metrics aggregated by time periods
    """
    df = spark.sql(f"""
        SELECT
            -- Time dimensions
            cal.calendar_year,
            cal.calendar_quarter_of_year,
            cal.calendar_month_of_year,
            cal.calendar_month_name,
            cal.calendar_week_of_year_iso,
            
            -- Order counts
            count(distinct fs.order_header_code)                    as distinct_orders,
            count(*)                                                as total_order_lines,
            
            -- Customer metrics
            count(distinct fs.customer_id)                          as distinct_customers,
            
            -- Volume metrics
            sum(fs.order_quantity)                                  as total_quantity_sold,
            avg(fs.order_quantity)                                  as avg_quantity_per_line,
            
            -- Revenue metrics
            sum(fs.order_extended_price_usd)                        as gross_revenue_usd,
            sum(fs.order_discount_usd)                              as total_discounts_usd,
            sum(fs.order_extended_price_usd - 
                fs.order_discount_usd)                              as net_revenue_usd,
            sum(fs.order_tax_usd)                                   as total_tax_usd,
            
            -- Average order values
            avg(fs.order_extended_price_usd)                        as avg_line_value_usd,
            sum(fs.order_extended_price_usd) / 
                nullif(count(distinct fs.order_header_code), 0)     as avg_order_value_usd,
            
            -- Cost and profitability
            sum(fs.part_supply_cost_usd * fs.order_quantity)        as total_supply_cost_usd,
            sum(fs.order_extended_price_usd - 
                (fs.part_supply_cost_usd * fs.order_quantity))      as gross_profit_usd,
            sum(fs.order_extended_price_usd - 
                (fs.part_supply_cost_usd * fs.order_quantity)) / 
                nullif(sum(fs.order_extended_price_usd), 0) * 100   as gross_margin_pct,
            
            -- Operational metrics
            avg(fs.order_commit_lag_days)                           as avg_commit_lag_days,
            avg(fs.order_receipt_lag_days)                          as avg_receipt_lag_days,
            avg(fs.order_ship_lag_days)                             as avg_ship_lag_days,
            max(fs.order_receipt_lag_days)                          as max_receipt_lag_days,
            min(fs.order_ship_lag_days)                             as min_ship_lag_days,
            
            -- Discount analysis
            avg(fs.order_discount_usd / 
                nullif(fs.order_extended_price_usd, 0)) * 100       as avg_discount_pct,
            max(fs.order_discount_usd / 
                nullif(fs.order_extended_price_usd, 0)) * 100       as max_discount_pct,
            
            -- Metadata
            current_timestamp()                                     as metric_calculated_at
            
        FROM {config.gold_catalog}.{config.gold_schema}.fact_sales fs
        
        LEFT JOIN {config.gold_catalog}.{config.gold_schema}.dim_calendar cal
            ON fs.calendar_order_id = cal.calendar_id
        
        WHERE fs.calendar_order_id > 0
          AND fs.customer_id > 0
        
        GROUP BY
            cal.calendar_year,
            cal.calendar_quarter_of_year,
            cal.calendar_month_of_year,
            cal.calendar_month_name,
            cal.calendar_week_of_year_iso
        
        ORDER BY
            cal.calendar_year,
            cal.calendar_month_of_year,
            cal.calendar_week_of_year_iso
    """)
    
    return df


@dlt.table(
    name=f"{config.gold_catalog}.{config.gold_schema}.metric_sales_by_customer",
    comment="Sales metrics aggregated by customer dimension",
    table_properties={
        "quality": "gold",
        "layer": "metric",
        "delta.enableChangeDataFeed": "true"
    }
)
def metric_sales_by_customer():
    """
    Creates customer-centric sales metrics.
    
    Returns:
        DataFrame: Sales metrics aggregated by customer
    """
    df = spark.sql(f"""
        SELECT
            -- Customer dimensions
            cust.customer_id,
            cust.customer_name,
            cust.customer_segment,
            cust.customer_nation,
            cust.customer_region,
            cust.customer_acctbal,
            
            -- Order metrics
            count(distinct fs.order_header_code)                    as total_orders,
            count(*)                                                as total_order_lines,
            min(cal.calendar_key)                                   as first_order_date,
            max(cal.calendar_key)                                   as last_order_date,
            datediff(max(cal.calendar_key), 
                     min(cal.calendar_key))                         as customer_lifetime_days,
            
            -- Product diversity
            count(distinct fs.part_id)                              as distinct_parts_purchased,
            count(distinct fs.supplier_id)                          as distinct_suppliers_used,
            
            -- Volume metrics
            sum(fs.order_quantity)                                  as lifetime_quantity,
            avg(fs.order_quantity)                                  as avg_quantity_per_line,
            
            -- Revenue metrics
            sum(fs.order_extended_price_usd)                        as lifetime_revenue_usd,
            sum(fs.order_extended_price_usd - 
                fs.order_discount_usd)                              as lifetime_net_revenue_usd,
            avg(fs.order_extended_price_usd)                        as avg_line_value_usd,
            sum(fs.order_extended_price_usd) / 
                nullif(count(distinct fs.order_header_code), 0)     as avg_order_value_usd,
            
            -- Profitability
            sum(fs.order_extended_price_usd - 
                (fs.part_supply_cost_usd * fs.order_quantity))      as lifetime_gross_profit_usd,
            sum(fs.order_extended_price_usd - 
                (fs.part_supply_cost_usd * fs.order_quantity)) / 
                nullif(sum(fs.order_extended_price_usd), 0) * 100   as avg_margin_pct,
            
            -- Discount behavior
            sum(fs.order_discount_usd)                              as lifetime_discounts_usd,
            avg(fs.order_discount_usd / 
                nullif(fs.order_extended_price_usd, 0)) * 100       as avg_discount_pct,
            
            -- Operational metrics
            avg(fs.order_receipt_lag_days)                          as avg_receipt_lag_days,
            
            -- Metadata
            current_timestamp()                                     as metric_calculated_at
            
        FROM {config.gold_catalog}.{config.gold_schema}.fact_sales fs
        
        INNER JOIN {config.gold_catalog}.{config.gold_schema}.dim_customer cust
            ON fs.customer_id = cust.customer_id
            
        LEFT JOIN {config.gold_catalog}.{config.gold_schema}.dim_calendar cal
            ON fs.calendar_order_id = cal.calendar_id
        
        WHERE fs.customer_id > 0
        
        GROUP BY
            cust.customer_id,
            cust.customer_name,
            cust.customer_segment,
            cust.customer_nation,
            cust.customer_region,
            cust.customer_acctbal
    """)
    
    return df


@dlt.table(
    name=f"{config.gold_catalog}.{config.gold_schema}.metric_sales_by_part",
    comment="Sales metrics aggregated by part (product) dimension",
    table_properties={
        "quality": "gold",
        "layer": "metric",
        "delta.enableChangeDataFeed": "true"
    }
)
def metric_sales_by_part():
    """
    Creates product-centric sales metrics.
    
    Returns:
        DataFrame: Sales metrics aggregated by part/product
    """
    df = spark.sql(f"""
        SELECT
            -- Part dimensions
            part.part_id,
            part.part_name,
            part.part_brand,
            part.part_type,
            part.part_mfgr,
            part.part_size,
            part.part_container,
            part.part_retailprice,
            
            -- Sales volume
            count(distinct fs.order_header_code)                    as orders_containing_part,
            count(*)                                                as total_order_lines,
            sum(fs.order_quantity)                                  as total_units_sold,
            avg(fs.order_quantity)                                  as avg_units_per_order,
            
            -- Customer reach
            count(distinct fs.customer_id)                          as distinct_customers,
            count(distinct fs.supplier_id)                          as distinct_suppliers,
            
            -- Revenue metrics
            sum(fs.order_extended_price_usd)                        as total_revenue_usd,
            avg(fs.order_extended_price_usd)                        as avg_revenue_per_line_usd,
            sum(fs.order_extended_price_usd) / 
                nullif(sum(fs.order_quantity), 0)                   as avg_revenue_per_unit_usd,
            
            -- Cost and profitability
            avg(fs.part_supply_cost_usd)                            as avg_supply_cost_usd,
            sum(fs.part_supply_cost_usd * fs.order_quantity)        as total_supply_cost_usd,
            sum(fs.order_extended_price_usd - 
                (fs.part_supply_cost_usd * fs.order_quantity))      as total_gross_profit_usd,
            avg((fs.order_extended_price_usd - 
                (fs.part_supply_cost_usd * fs.order_quantity)) / 
                nullif(fs.order_extended_price_usd, 0)) * 100       as avg_profit_margin_pct,
            
            -- Discount analysis
            sum(fs.order_discount_usd)                              as total_discounts_usd,
            avg(fs.order_discount_usd / 
                nullif(fs.order_extended_price_usd, 0)) * 100       as avg_discount_pct,
            
            -- Metadata
            current_timestamp()                                     as metric_calculated_at
            
        FROM {config.gold_catalog}.{config.gold_schema}.fact_sales fs
        
        INNER JOIN {config.gold_catalog}.{config.gold_schema}.dim_part part
            ON fs.part_id = part.part_id
        
        WHERE fs.part_id > 0
        
        GROUP BY
            part.part_id,
            part.part_name,
            part.part_brand,
            part.part_type,
            part.part_mfgr,
            part.part_size,
            part.part_container,
            part.part_retailprice
    """)
    
    return df


@dlt.table(
    name=f"{config.gold_catalog}.{config.gold_schema}.metric_sales_by_supplier",
    comment="Sales metrics aggregated by supplier dimension",
    table_properties={
        "quality": "gold",
        "layer": "metric",
        "delta.enableChangeDataFeed": "true"
    }
)
def metric_sales_by_supplier():
    """
    Creates supplier-centric sales metrics.
    
    Returns:
        DataFrame: Sales metrics aggregated by supplier
    """
    df = spark.sql(f"""
        SELECT
            -- Supplier dimensions
            sup.supplier_id,
            sup.supplier_name,
            sup.supplier_nation,
            sup.supplier_region,
            sup.supplier_acctbal,
            
            -- Volume metrics
            count(distinct fs.order_header_code)                    as orders_fulfilled,
            count(*)                                                as total_order_lines,
            sum(fs.order_quantity)                                  as total_units_supplied,
            
            -- Product and customer diversity
            count(distinct fs.part_id)                              as distinct_parts_supplied,
            count(distinct fs.customer_id)                          as distinct_customers_served,
            
            -- Revenue metrics
            sum(fs.order_extended_price_usd)                        as total_revenue_usd,
            avg(fs.order_extended_price_usd)                        as avg_line_value_usd,
            
            -- Cost and profitability
            sum(fs.part_supply_cost_usd * fs.order_quantity)        as total_supply_cost_usd,
            avg(fs.part_supply_cost_usd)                            as avg_unit_supply_cost_usd,
            sum(fs.order_extended_price_usd - 
                (fs.part_supply_cost_usd * fs.order_quantity))      as total_profit_generated_usd,
            
            -- Operational performance
            avg(fs.order_commit_lag_days)                           as avg_commit_lag_days,
            avg(fs.order_ship_lag_days)                             as avg_ship_lag_days,
            avg(fs.order_receipt_lag_days)                          as avg_receipt_lag_days,
            
            -- On-time delivery metrics
            sum(case when fs.order_ship_lag_days <= 7 
                then 1 else 0 end) / 
                nullif(count(*), 0) * 100                           as pct_shipped_within_week,
            sum(case when fs.order_receipt_lag_days <= 14 
                then 1 else 0 end) / 
                nullif(count(*), 0) * 100                           as pct_received_within_two_weeks,
            
            -- Metadata
            current_timestamp()                                     as metric_calculated_at
            
        FROM {config.gold_catalog}.{config.gold_schema}.fact_sales fs
        
        INNER JOIN {config.gold_catalog}.{config.gold_schema}.dim_supplier sup
            ON fs.supplier_id = sup.supplier_id
        
        WHERE fs.supplier_id > 0
        
        GROUP BY
            sup.supplier_id,
            sup.supplier_name,
            sup.supplier_nation,
            sup.supplier_region,
            sup.supplier_acctbal
    """)
    
    return df
