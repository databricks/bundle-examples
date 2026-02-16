# Databricks notebook source
from pyspark.sql import functions as F

df = (
    spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "csv")
    .option("cloudFiles.schemaLocation", "/tmp/autoloader/_checkpoint/my_stream")
    .load("/Volumes/main/raw/incoming")
)
