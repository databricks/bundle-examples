# Databricks notebook source
# MAGIC %md
# MAGIC ## Paste the table config JSON you would like to debug from `./configs/tables.json` and assign to variable `table_config`
# MAGIC For example,
# MAGIC ```
# MAGIC table_config = r'''
# MAGIC {
# MAGIC   "name": "all_employees",
# MAGIC   "format": "csv",
# MAGIC   "format_options": {
# MAGIC     "escape": "\"",
# MAGIC     "multiLine": "false"
# MAGIC   }
# MAGIC   "schema_hints": "id int, name string"
# MAGIC }
# MAGIC '''
# MAGIC ```
# MAGIC Only `name` and `format` are required for a table.

# COMMAND ----------

table_config = r'''
  {
    "name": "employees",
    "format": "csv",
    "format_options": {
      "escape": "\""
    },
    "schema_hints": "id int, name string"
  }
'''

# COMMAND ----------

# MAGIC %md
# MAGIC ## Click `Run all` and inspect the parsed result. Iterate on the config until the result looks good

# COMMAND ----------

import json
import tempfile
from utils import tablemanager
from utils import envmanager

if not envmanager.has_default_storage():
  print("WARNING: Current catalog is not using default storage, some file push feature may not be available")

# Load table config
table_config_json = json.loads(table_config)
tablemanager.validate_config(table_config_json)
table_name = table_config_json["name"]
table_volume_path_data = tablemanager.get_table_volume_path(table_name)

assert tablemanager.has_data_file(table_name), f"No data file found in {table_volume_path_data}. Please upload at least 1 file to {table_volume_path_data}"

# Put schema location in temp directory
with tempfile.TemporaryDirectory() as tmpdir:
  display(tablemanager.get_df_with_config(spark, table_config_json, tmpdir))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Copy and paste the modified config back to the `./configs/tables.json` in the DAB folder