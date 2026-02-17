# Databricks notebook source

# Runs once per item in the for-each. Do not call dbutils.jobs.taskValues.set() here.\n",
from databricks.sdk.runtime import dbutils

# Current iteration value passed from the for-each task (base_parameters: item = {{input}})\n",
current_item = dbutils.widgets.get("item")
print(f"Processing item: {current_item}")
