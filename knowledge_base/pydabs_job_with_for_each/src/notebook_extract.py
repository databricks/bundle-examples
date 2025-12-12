# Databricks notebook source
lookup_file_name = dbutils.widgets.get("lookup_file_name")

# COMMAND ----------

import json
from datetime import datetime, timedelta

indexes = range(0, 10)
start_date = datetime.today()
data = [
    {"date": (start_date + timedelta(days=index)).strftime("%Y-%m-%d")}
    for index in indexes
]
dbutils.fs.put(lookup_file_name, json.dumps(data), overwrite=True)
dbutils.jobs.taskValues.set("indexes", list(indexes))

# COMMAND ----------
