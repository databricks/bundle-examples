# Databricks notebook source
from pyspark.sql import SparkSession


spark = SparkSession.builder.getOrCreate()
available_view = "__failing_job_examples_orders_input_7f3f2a9c__"
configured_input_view = dbutils.widgets.get("input_view")
spark.range(1).createOrReplaceTempView(available_view)

print(f"Reading configured input view: {configured_input_view}")
input_schema = spark.read.table(configured_input_view).schema
print(f"Resolved input schema: {input_schema.simpleString()}")
