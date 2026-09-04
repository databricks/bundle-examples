# Databricks notebook source
from pyspark.sql import SparkSession


spark = SparkSession.builder.getOrCreate()
missing_view = "__failing_job_examples_missing_orders_7f3f2a9c__"
spark.catalog.dropGlobalTempView(missing_view)
missing_table = f"global_temp.{missing_view}"

print(f"Reading required input table: {missing_table}")
spark.read.table(missing_table).count()
