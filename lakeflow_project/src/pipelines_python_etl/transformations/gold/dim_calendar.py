# Databricks notebook source
# MAGIC %md
# MAGIC #####Configuration

# COMMAND ----------

# General packages and utils
from lighthouse import config, view

# COMMAND ----------

# Manipulation  of default catalog settings
config.base_catalog = "samples"
config.curated_catalog = "my_catalog"
curated_schema = "tpch"
spark.sql(f"create schema if not exists {config.curated_catalog}.{curated_schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC #####Parameters

# COMMAND ----------

dimension_name = "dim__calendar"
dimension_table = f"{config.curated_catalog}.{curated_schema}.{dimension_name}"

# COMMAND ----------

# MAGIC %md
# MAGIC #####Transform

# COMMAND ----------

beginDate = '1990-01-01'
endDate = '2029-12-31'

(
  spark.sql(f"select explode(sequence(to_date('{beginDate}'), to_date('{endDate}'), interval 1 day)) as calendarDate")
    .createOrReplaceTempView('dates')
)

# COMMAND ----------

# MAGIC %sql 
# MAGIC create or replace temporary view stage_calendar as 
# MAGIC select
# MAGIC   year(calendarDate) * 10000 + month(calendarDate) * 100 + day(calendarDate) as calendar_id,
# MAGIC   CalendarDate as calendar_key,
# MAGIC   year(calendarDate) AS calendar_year,
# MAGIC   month(calendarDate) as calendar_month_of_year,
# MAGIC   date_format(calendarDate, 'MMMM') as calendar_month_name,
# MAGIC   dayofmonth(calendarDate) as calendar_day_of_month,
# MAGIC   dayofweek(calendarDate) AS calendar_day_of_week,
# MAGIC   date_format(calendarDate, 'EEEE') as calendar_day_name,
# MAGIC   case
# MAGIC     when weekday(calendarDate) < 5 then 'Y'
# MAGIC     else 'N'
# MAGIC   end as calendar_is_week_day,
# MAGIC   case
# MAGIC     when calendarDate = last_day(calendarDate) then 'Y'
# MAGIC     else 'N'
# MAGIC   end as calendar_is_last_day_of_month,
# MAGIC   dayofyear(calendarDate) as calendar_day_of_year,
# MAGIC   weekofyear(calendarDate) as calendar_week_of_year_iso,
# MAGIC   quarter(calendarDate) as calendar_quarter_of_year
# MAGIC from
# MAGIC   dates
# MAGIC order by
# MAGIC   calendarDate

# COMMAND ----------

# MAGIC %md
# MAGIC #####Table

# COMMAND ----------

# Drop table if exists
spark.sql(f"drop table if exists {dimension_table};")

# Define table
spark.sql(f"""
    create table if not exists {dimension_table} (
         calendar_id INT PRIMARY KEY
        ,calendar_key DATE
        ,calendar_year INT
        ,calendar_month_of_year INT
        ,calendar_month_name STRING
        ,calendar_day_of_month INT
        ,calendar_day_of_week INT
        ,calendar_day_name STRING
        ,calendar_is_week_day BOOLEAN
        ,calendar_is_last_day_of_month BOOLEAN
        ,calendar_day_of_year INT
        ,calendar_week_of_year_iso INT
        ,calendar_quarter_of_year INT
    );
""")

# Add table properties
spark.sql(f"""
    ALTER TABLE {dimension_table} 
    SET TBLPROPERTIES("primary_key_columns" = '[calendar_key]', 'surrogate_column' = 'calendar_id');
""")

# COMMAND ----------

# MAGIC %md
# MAGIC #####Load

# COMMAND ----------

spark.sql(f"""
    merge into {dimension_table} as calendar
    using stage_calendar
    on calendar.calendar_id = stage_calendar.calendar_id
    when matched
    then update set *
    when not matched
    then insert *
""")

# COMMAND ----------

#Create view with user friendly names. To print the query definition, set debug=1
view.create_view(
    catalog_name=config.curated_catalog,
    database_name=curated_schema,
    table_name=dimension_name,
    view_owner=config.default_object_owner,
    debug=0,
)
