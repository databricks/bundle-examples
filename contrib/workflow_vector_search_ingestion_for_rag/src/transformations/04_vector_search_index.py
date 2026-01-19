# Databricks notebook source
# MAGIC %md
# MAGIC # Create Vector Search Index
# MAGIC
# MAGIC This notebook creates a Databricks Vector Search endpoint and index from document text.

# COMMAND ----------

# MAGIC %pip install -r ../../requirements.txt -q
# MAGIC %restart_python

# COMMAND ----------

# Get parameters
dbutils.widgets.text("catalog", "", "Catalog name")
dbutils.widgets.text("schema", "", "Schema name")
dbutils.widgets.text("source_table_name", "parsed_documents_text_chunked", "Source table name")
dbutils.widgets.text("endpoint_name", "vector-search-shared-endpoint", "Vector Search endpoint name")
dbutils.widgets.text("index_name", "parsed_documents_vector_index", "Vector Search index name")
dbutils.widgets.text("primary_key", "chunk_id", "Primary key column")
dbutils.widgets.text("embedding_source_column", "chunked_text", "Text column for embeddings")
dbutils.widgets.text("embedding_model_endpoint", "databricks-gte-large-en", "Embedding model endpoint")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
source_table_name = dbutils.widgets.get("source_table_name")
endpoint_name = dbutils.widgets.get("endpoint_name")
index_name = dbutils.widgets.get("index_name")
primary_key = dbutils.widgets.get("primary_key")
embedding_source_column = dbutils.widgets.get("embedding_source_column")
embedding_model_endpoint = dbutils.widgets.get("embedding_model_endpoint")

# COMMAND ----------

# Set catalog and schema
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.vectorsearch import (
    EndpointType,
    VectorSearchIndexesAPI,
    DeltaSyncVectorIndexSpecRequest,
    EmbeddingSourceColumn,
    PipelineType,
    VectorIndexType,
)
from databricks.sdk.errors.platform import ResourceDoesNotExist, BadRequest
import time

# Initialize clients
w = WorkspaceClient()
vsc = VectorSearchClient()

# COMMAND ----------

# Helper functions for robust endpoint and index management

def find_endpoint(endpoint_name: str):
    """Check if vector search endpoint exists."""
    try:
        vector_search_endpoints = w.vector_search_endpoints.list_endpoints()
        for ve in vector_search_endpoints:
            if ve.name == endpoint_name:
                return ve
        return None
    except Exception:
        return None

def create_or_validate_endpoint(endpoint_name: str):
    """Create or validate vector search endpoint exists and is online."""
    print(f"Checking if endpoint '{endpoint_name}' exists...")
    
    endpoint = find_endpoint(endpoint_name)
    
    if endpoint:
        print(f"Endpoint '{endpoint_name}' already exists.")
        # Use built-in wait method to ensure it's online
        try:
            w.vector_search_endpoints.wait_get_endpoint_vector_search_endpoint_online(endpoint_name)
            print(f"Endpoint '{endpoint_name}' is online!")
        except Exception as e:
            print(f"Warning: Could not verify endpoint is online: {e}")
    else:
        print(f"Endpoint does not exist. Creating endpoint '{endpoint_name}'...")
        print("Please wait, this can take up to 20 minutes...")
        
        # Use the built-in create_endpoint_and_wait method
        w.vector_search_endpoints.create_endpoint_and_wait(
            endpoint_name,
            endpoint_type=EndpointType.STANDARD
        )
        
        # Ensure it's online
        w.vector_search_endpoints.wait_get_endpoint_vector_search_endpoint_online(endpoint_name)
        print(f"Endpoint '{endpoint_name}' is online!")

def find_index(index_name: str):
    """Check if vector search index exists."""
    try:
        return w.vector_search_indexes.get_index(index_name=index_name)
    except ResourceDoesNotExist:
        return None

def wait_for_index_to_be_ready(index_name: str):
    """Wait for index to be ready using status.ready boolean."""
    index = find_index(index_name)
    if not index:
        raise Exception(f"Index {index_name} not found")
    
    while not index.status.ready:
        print(f"Index {index_name} is not ready yet, waiting 30 seconds...")
        print(f"Current status: {index.status}")
        time.sleep(30)
        index = find_index(index_name)
        if not index:
            raise Exception(f"Index {index_name} disappeared during wait")
    
    print(f"Index {index_name} is ready!")

# COMMAND ----------

# Create or validate Vector Search endpoint
create_or_validate_endpoint(endpoint_name)

# COMMAND ----------

# Create Vector Search Index
full_index_name = f"{catalog}.{schema}.{index_name}"
full_source_table_name = f"{catalog}.{schema}.{source_table_name}"

print(f"Managing vector search index '{full_index_name}' on table '{full_source_table_name}'...")

try:
    existing_index = find_index(full_index_name)
    
    if existing_index:
        print(f"Index '{full_index_name}' already exists.")
        
        # Wait for index to be ready if it's not
        wait_for_index_to_be_ready(full_index_name)
        
        print(f"Index status: {existing_index.status}")
        
        # Try to sync the index
        if existing_index.status.ready:
            print("Syncing existing index...")
            try:
                w.vector_search_indexes.sync_index(index_name=full_index_name)
                print("Index sync kicked off successfully!")
            except BadRequest as e:
                print(f"Index sync already in progress or failed: {e}")
                print("Please wait for the index to finish syncing.")
        else:
            print("Index is not ready for syncing yet.")
    else:
        print(f"Index does not exist, creating '{full_index_name}'...")
        print("Computing document embeddings and Vector Search Index. This can take 15 minutes or longer.")
        
        # Create delta sync index spec
        delta_sync_spec = DeltaSyncVectorIndexSpecRequest(
            source_table=full_source_table_name,
            pipeline_type=PipelineType.TRIGGERED,
            embedding_source_columns=[
                EmbeddingSourceColumn(
                    name=embedding_source_column,
                    embedding_model_endpoint_name=embedding_model_endpoint,
                )
            ],
        )
        
        # Create the index
        w.vector_search_indexes.create_index(
            name=full_index_name,
            endpoint_name=endpoint_name,
            primary_key=primary_key,
            index_type=VectorIndexType.DELTA_SYNC,
            delta_sync_index_spec=delta_sync_spec,
        )
        
        print(f"Vector search index '{full_index_name}' created successfully!")
        print("Note: The index will continue syncing/embedding in the background.")
        print("Wait for the index to be ready before querying it.")
                
except Exception as e:
    print(f"Error managing vector search index: {e}")
    raise

# COMMAND ----------

print(f"Vector Search setup complete!")
print(f"Endpoint: {endpoint_name}")
print(f"Index: {full_index_name}")
print(f"Note: Check the index status in the Databricks UI to ensure it's fully synced before querying.")
