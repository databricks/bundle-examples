# Databricks notebook source
# MAGIC %md
# MAGIC # Parse Documents using ai_parse_document
# MAGIC
# MAGIC This notebook uses Structured Streaming to incrementally parse PDFs and images using the ai_parse_document function.

# COMMAND ----------

# Get parameters
dbutils.widgets.text("catalog", "main", "Catalog name")
dbutils.widgets.text("schema", "default", "Schema name")
dbutils.widgets.text(
    "source_volume_path", "/Volumes/main/default/source_documents", "Source volume path"
)
dbutils.widgets.text(
    "output_volume_path", "/Volumes/main/default/parsed_output", "Output volume path"
)
dbutils.widgets.text(
    "checkpoint_location",
    "/Volumes/main/default/checkpoints/parse_documents",
    "Checkpoint location",
)
dbutils.widgets.text("table_name", "parsed_documents_raw", "Output table name")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
source_volume_path = dbutils.widgets.get("source_volume_path")
output_volume_path = dbutils.widgets.get("output_volume_path")
checkpoint_location = dbutils.widgets.get("checkpoint_location")
table_name = dbutils.widgets.get("table_name")

# COMMAND ----------

# Set catalog and schema
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

# COMMAND ----------

from pyspark.sql.functions import col, current_timestamp, expr
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    BinaryType,
    TimestampType,
    LongType,
)

# Define schema for binary files (must match exact schema expected by binaryFile format)
binary_file_schema = StructType(
    [
        StructField("path", StringType(), False),
        StructField("modificationTime", TimestampType(), False),
        StructField("length", LongType(), False),
        StructField("content", BinaryType(), True),
    ]
)

# Read files using Structured Streaming
files_df = (
    spark.readStream.format("binaryFile")
    .schema(binary_file_schema)
    .option("pathGlobFilter", "*.{pdf,jpg,jpeg,png}")
    .option("recursiveFileLookup", "true")
    .load(source_volume_path)
)

# Parse documents with ai_parse_document
parsed_df = (
    files_df.repartition(8, expr("crc32(path) % 8"))
    .withColumn(
        "parsed",
        expr(f"""
            ai_parse_document(
                content,
                map(
                    'version', '2.0',
                    'imageOutputPath', '{output_volume_path}',
                    'descriptionElementTypes', '*'
                )
            )
        """),
    )
    .withColumn("parsed_at", current_timestamp())
    .select("path", "parsed", "parsed_at")
)

# Write to Delta table with streaming
(
    parsed_df.writeStream.format("delta")
    .outputMode("append")
    .option("checkpointLocation", checkpoint_location)
    .option("delta.feature.variantType-preview", "supported")
    .option("mergeSchema", "true")
    .trigger(availableNow=True)
    .toTable(table_name)
)
