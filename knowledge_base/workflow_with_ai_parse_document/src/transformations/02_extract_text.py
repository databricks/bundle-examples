# Databricks notebook source
# MAGIC %md
# MAGIC # Extract Text from Parsed Documents
# MAGIC
# MAGIC This notebook uses Structured Streaming to extract clean text from parsed documents.

# COMMAND ----------

# Get parameters
dbutils.widgets.text("catalog", "users", "Catalog name")
dbutils.widgets.text("schema", "jas_bali", "Schema name")
dbutils.widgets.text("checkpoint_location", "/tmp/checkpoints/extract_text", "Checkpoint location")
dbutils.widgets.text("source_table_name", "parsed_documents_raw", "Source table name")
dbutils.widgets.text("table_name", "parsed_documents_text", "Output table name")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
checkpoint_location = dbutils.widgets.get("checkpoint_location")
source_table_name = dbutils.widgets.get("source_table_name")
table_name = dbutils.widgets.get("table_name")

# COMMAND ----------

# Set catalog and schema
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

# COMMAND ----------

from pyspark.sql.functions import col, concat_ws, expr, lit, when

# Read from source table using Structured Streaming
parsed_stream = (spark.readStream
    .format("delta")
    .table(source_table_name)
)

# Extract text from parsed documents
text_df = parsed_stream.withColumn(
    "text",
    when(
        expr("try_cast(parsed:error_status AS STRING)").isNotNull(),
        lit(None)
    ).otherwise(
        concat_ws(
            "\n\n",
            expr("""
                transform(
                    CASE
                        WHEN try_cast(parsed:metadata:version AS STRING) = '1.0'
                        THEN try_cast(parsed:document:pages AS ARRAY<VARIANT>)
                        ELSE try_cast(parsed:document:elements AS ARRAY<VARIANT>)
                    END,
                    element -> try_cast(element:content AS STRING)
                )
            """)
        )
    )
).withColumn(
    "error_status",
    expr("try_cast(parsed:error_status AS STRING)")
).select("path", "text", "error_status", "parsed_at")

# Write to Delta table with streaming
(text_df.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", checkpoint_location)
    .option("mergeSchema", "true")
    .trigger(availableNow=True)
    .toTable(table_name)
)
