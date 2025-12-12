# Databricks notebook source
lookup_file_name = dbutils.widgets.get("lookup_file_name")
index = int(dbutils.widgets.get("index"))

# COMMAND ----------

import json

with open(lookup_file_name, "r") as f:
    data = json.load(f)
date = data[index].get("date")

print(date)

# COMMAND ----------
