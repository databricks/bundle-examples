# Databricks notebook source
# MAGIC %md
# MAGIC # Extract Structured Data using AI Query
# MAGIC
# MAGIC This notebook uses Structured Streaming to extract structured JSON from document text using ai_query.

# COMMAND ----------

# Get parameters
dbutils.widgets.text("catalog", "main", "Catalog name")
dbutils.widgets.text("schema", "default", "Schema name")
dbutils.widgets.text("checkpoint_location", "/Volumes/main/default/checkpoints/extract_structured", "Checkpoint location")
dbutils.widgets.text("source_table_name", "parsed_documents_text", "Source table name")
dbutils.widgets.text("table_name", "parsed_documents_structured", "Output table name")

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

from pyspark.sql.functions import col, concat, current_timestamp, expr, length, lit

# Read from source table using Structured Streaming
text_stream = (spark.readStream
    .format("delta")
    .table(source_table_name)
    .filter(
        (col("text").isNotNull()) &
        (col("error_status").isNull()) &
        (length(col("text")) > 100)
    )
)

# Extract structured data using ai_query
structured_df = text_stream.withColumn(
    "extracted_json",
    expr("""
        ai_query(
            'databricks-claude-sonnet-4',
            concat(
                'Extract key information from this document and return as JSON. ',
                'Include: document_type, key_entities (names, organizations, locations), ',
                'dates, amounts, and a brief summary (max 100 words). ',
                'Document text: ',
                text
            ),
            returnType => 'STRING',
            modelParameters => named_struct(
                'max_tokens', 2000,
                'temperature', 0.1
            )
        )
    """)
).withColumn(
    "extraction_timestamp", current_timestamp()
).select("path", "extracted_json", "parsed_at", "extraction_timestamp")

# Write to Delta table with streaming
(structured_df.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", checkpoint_location)
    .option("mergeSchema", "true")
    .trigger(availableNow=True)
    .toTable(table_name)
)
