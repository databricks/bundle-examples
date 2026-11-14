# Databricks notebook source
# MAGIC %md
# MAGIC # Chunk Text from Parsed Documents
# MAGIC
# MAGIC This notebook uses Structured Streaming to chunk text from parsed documents into smaller pieces suitable for embedding.

# COMMAND ----------

# MAGIC %pip install -r ../../requirements.txt -q
# MAGIC %restart_python

# COMMAND ----------

# Get parameters
dbutils.widgets.text("catalog", "", "Catalog name")
dbutils.widgets.text("schema", "", "Schema name")
dbutils.widgets.text("checkpoint_location", "", "Checkpoint location")
dbutils.widgets.text("chunking_cache_location", "", "Chunking cache location")
dbutils.widgets.text("source_table_name", "parsed_documents_text", "Source table name")
dbutils.widgets.text("table_name", "parsed_documents_text_chunked", "Output table name")
dbutils.widgets.text("embedding_model_endpoint", "databricks-gte-large-en", "Embedding model endpoint")
dbutils.widgets.text("chunk_size_tokens", "1024", "Chunk size in tokens")
dbutils.widgets.text("chunk_overlap_tokens", "256", "Chunk overlap in tokens")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
checkpoint_location = dbutils.widgets.get("checkpoint_location")
chunking_cache_location = dbutils.widgets.get("chunking_cache_location")
source_table_name = dbutils.widgets.get("source_table_name")
table_name = dbutils.widgets.get("table_name")
embedding_model_endpoint = dbutils.widgets.get("embedding_model_endpoint")
chunk_size_tokens = int(dbutils.widgets.get("chunk_size_tokens"))
chunk_overlap_tokens = int(dbutils.widgets.get("chunk_overlap_tokens"))

# COMMAND ----------

# Set catalog and schema
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define chunking utilities

# COMMAND ----------

from typing import Optional
import os

# Set the TRANSFORMERS_CACHE environment variable to a writable directory
os.environ['TRANSFORMERS_CACHE'] = chunking_cache_location
HF_CACHE_DIR = chunking_cache_location

# Embedding Models Configuration
EMBEDDING_MODELS = {
    "gte-large-en-v1.5": {
        "context_window": 8192,
        "type": "SENTENCE_TRANSFORMER",
    },
    "bge-large-en-v1.5": {
        "context_window": 512,
        "type": "SENTENCE_TRANSFORMER",
    },
    "bge_large_en_v1_5": {
        "context_window": 512,
        "type": "SENTENCE_TRANSFORMER",
    },
    "text-embedding-ada-002": {
        "context_window": 8192,
        "type": "OPENAI",
    },
    "text-embedding-3-small": {
        "context_window": 8192,
        "type": "OPENAI",
    },
    "text-embedding-3-large": {
        "context_window": 8192,
        "type": "OPENAI",
    },
}

def get_embedding_model_tokenizer(endpoint_type: str) -> Optional[dict]:
    from transformers import AutoTokenizer
    import tiktoken

    EMBEDDING_MODELS_W_TOKENIZER = {
        "gte-large-en-v1.5": {
            "tokenizer": lambda: AutoTokenizer.from_pretrained(
                "Alibaba-NLP/gte-large-en-v1.5", cache_dir=HF_CACHE_DIR
            ),
            "context_window": 8192,
            "type": "SENTENCE_TRANSFORMER",
        },
        "bge-large-en-v1.5": {
            "tokenizer": lambda: AutoTokenizer.from_pretrained(
                "BAAI/bge-large-en-v1.5", cache_dir=HF_CACHE_DIR
            ),
            "context_window": 512,
            "type": "SENTENCE_TRANSFORMER",
        },
        "bge_large_en_v1_5": {
            "tokenizer": lambda: AutoTokenizer.from_pretrained(
                "BAAI/bge-large-en-v1.5", cache_dir=HF_CACHE_DIR
            ),
            "context_window": 512,
            "type": "SENTENCE_TRANSFORMER",
        },
        "text-embedding-ada-002": {
            "context_window": 8192,
            "tokenizer": lambda: tiktoken.encoding_for_model("text-embedding-ada-002"),
            "type": "OPENAI",
        },
        "text-embedding-3-small": {
            "context_window": 8192,
            "tokenizer": lambda: tiktoken.encoding_for_model("text-embedding-3-small"),
            "type": "OPENAI",
        },
        "text-embedding-3-large": {
            "context_window": 8192,
            "tokenizer": lambda: tiktoken.encoding_for_model("text-embedding-3-large"),
            "type": "OPENAI",
        },
    }
    return EMBEDDING_MODELS_W_TOKENIZER.get(endpoint_type).get("tokenizer")

def get_embedding_model_config(endpoint_type: str) -> Optional[dict]:
    return EMBEDDING_MODELS.get(endpoint_type)

def extract_endpoint_type(llm_endpoint) -> Optional[str]:
    try:
        return llm_endpoint.config.served_entities[0].external_model.name
    except AttributeError:
        try:
            return llm_endpoint.config.served_entities[0].foundation_model.name
        except AttributeError:
            return None

def detect_fmapi_embedding_model_type(model_serving_endpoint: str):
    from databricks.sdk import WorkspaceClient
    
    client = WorkspaceClient()
    try:
        llm_endpoint = client.serving_endpoints.get(name=model_serving_endpoint)
        endpoint_type = extract_endpoint_type(llm_endpoint)
    except Exception as e:
        endpoint_type = None

    embedding_config = (
        get_embedding_model_config(endpoint_type) if endpoint_type else None
    )

    if embedding_config:
        embedding_config["tokenizer"] = (
            get_embedding_model_tokenizer(endpoint_type) if endpoint_type else None
        )

    return (endpoint_type, embedding_config)

def get_recursive_character_text_splitter(
    model_serving_endpoint: str,
    embedding_model_name: str = None,
    chunk_size_tokens: int = None,
    chunk_overlap_tokens: int = 0,
):
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from transformers import AutoTokenizer
    import tiktoken

    # Detect the embedding model and its configuration
    embedding_model_name, chunk_spec = detect_fmapi_embedding_model_type(
        model_serving_endpoint
    )

    if chunk_spec is None or embedding_model_name is None:
        # Fall back to using provided embedding_model_name
        chunk_spec = EMBEDDING_MODELS.get(embedding_model_name)
        if chunk_spec is None:
            raise ValueError(
                f"Embedding model `{embedding_model_name}` not found. Available models: {EMBEDDING_MODELS.keys()}"
            )

    # Update chunk specification based on provided parameters
    chunk_spec["chunk_size_tokens"] = (
        chunk_size_tokens or chunk_spec["context_window"]
    )
    chunk_spec["chunk_overlap_tokens"] = chunk_overlap_tokens

    def _recursive_character_text_splitter(text: str):
        if text is None or text == "":
            return []
        
        tokenizer = chunk_spec["tokenizer"]()
        if chunk_spec["type"] == "SENTENCE_TRANSFORMER":
            splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
                tokenizer,
                chunk_size=chunk_spec["chunk_size_tokens"],
                chunk_overlap=chunk_spec["chunk_overlap_tokens"],
            )
        elif chunk_spec["type"] == "OPENAI":
            splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                tokenizer.name,
                chunk_size=chunk_spec["chunk_size_tokens"],
                chunk_overlap=chunk_spec["chunk_overlap_tokens"],
            )
        else:
            raise ValueError(f"Unsupported model type: {chunk_spec['type']}")
        return splitter.split_text(text)

    return _recursive_character_text_splitter

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create and apply chunking function

# COMMAND ----------

from pyspark.sql.functions import col, explode, udf, md5
from pyspark.sql.types import ArrayType, StringType

# Create the chunking function
print(f"Creating chunking function for embedding model: {embedding_model_endpoint}")
print(f"Chunk size: {chunk_size_tokens} tokens, Overlap: {chunk_overlap_tokens} tokens")

recursive_character_text_splitter_fn = get_recursive_character_text_splitter(
    model_serving_endpoint=embedding_model_endpoint,
    chunk_size_tokens=chunk_size_tokens,
    chunk_overlap_tokens=chunk_overlap_tokens,
)

# Create a UDF from the chunking function
chunking_udf = udf(
    recursive_character_text_splitter_fn, 
    returnType=ArrayType(StringType())
)

# Read from source table using Structured Streaming
parsed_stream = (spark.readStream
    .format("delta")
    .table(source_table_name)
)

# Apply chunking: only process rows without errors and with non-null text
chunked_array_df = (parsed_stream
    .filter(col("error_status").isNull())
    .filter(col("text").isNotNull())
    .withColumn("text_chunked_array", chunking_udf(col("text")))
)

# Explode the array of chunks into separate rows
chunked_df = (chunked_array_df
    .select(
        col("path"),
        col("parsed_at"),
        explode("text_chunked_array").alias("chunked_text")
    )
)

# Add chunk_id as MD5 hash of the chunked text
text_df = (chunked_df
    .withColumn("chunk_id", md5(col("chunked_text")))
    .select(
        col("chunk_id"),
        col("chunked_text"),
        col("path"),
        col("parsed_at")
    )
)

# Write to Delta table with streaming
(text_df.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", checkpoint_location)
    .option("mergeSchema", "true")
    .trigger(availableNow=True)
    .toTable(table_name)
)

# COMMAND ----------

# Enable CDF on the existing table
spark.sql(f"ALTER TABLE {catalog}.{schema}.{table_name} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")