# Databricks notebook source
from pyspark.sql import functions as F

source_table = "main.analytics.daily_events"
# Insert consumer logic here
df = spark.read.table(source_table)
