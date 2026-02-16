# Databricks notebook source
from databricks.sdk.runtime import dbutils

value = 42
dbutils.jobs.taskValues.set(key="answer", value=value)
print(f"Produced value: {value}")