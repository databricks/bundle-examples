# Databricks notebook source
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

# %sql 
# create or replace temporary view stage_calendar as 
# select
#   year(calendarDate) * 10000 + month(calendarDate) * 100 + day(calendarDate) as calendar_id,
#   CalendarDate as calendar_key,
#   year(calendarDate) AS calendar_year,
#   month(calendarDate) as calendar_month_of_year,
#   date_format(calendarDate, 'MMMM') as calendar_month_name,
#   dayofmonth(calendarDate) as calendar_day_of_month,
#   dayofweek(calendarDate) AS calendar_day_of_week,
#   date_format(calendarDate, 'EEEE') as calendar_day_name,
#   case
#     when weekday(calendarDate) < 5 then 'Y'
#     else 'N'
#   end as calendar_is_week_day,
#   case
#     when calendarDate = last_day(calendarDate) then 'Y'
#     else 'N'
#   end as calendar_is_last_day_of_month,
#   dayofyear(calendarDate) as calendar_day_of_year,
#   weekofyear(calendarDate) as calendar_week_of_year_iso,
#   quarter(calendarDate) as calendar_quarter_of_year
# from
#   dates
# order by
#   calendarDate

# COMMAND ----------

# MAGIC %md
# MAGIC #####Table

# COMMAND ----------

import dlt

@dlt.table(
    name="dim_calendar",
    comment="Materialized view of the calendar table"
)
def calendar_mv():
    return spark.sql("""
        select
          year(calendarDate) * 10000 + month(calendarDate) * 100 + day(calendarDate) as calendar_id,
          calendarDate as calendar_key,
          year(calendarDate) AS calendar_year,
          month(calendarDate) as calendar_month_of_year,
          date_format(calendarDate, 'MMMM') as calendar_month_name,
          dayofmonth(calendarDate) as calendar_day_of_month,
          dayofweek(calendarDate) AS calendar_day_of_week,
          date_format(calendarDate, 'EEEE') as calendar_day_name,
          case
            when weekday(calendarDate) < 5 then 'Y'
            else 'N'
          end as calendar_is_week_day,
          case
            when calendarDate = last_day(calendarDate) then 'Y'
            else 'N'
          end as calendar_is_last_day_of_month,
          dayofyear(calendarDate) as calendar_day_of_year,
          weekofyear(calendarDate) as calendar_week_of_year_iso,
          quarter(calendarDate) as calendar_quarter_of_year
        from dates
        order by calendarDate
    """)
