# Databricks notebook source
from databricks.sdk.runtime import dbutils

bad_records = 123  # result of a data quality check
dbutils.jobs.taskValues.set(key="bad_records", value=bad_records)
