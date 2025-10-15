# AI Document Processing Workflow for RAG with Structured Streaming

A Databricks Asset Bundle demonstrating **incremental document processing** using `ai_parse_document`, chunking, and Databricks Workflows with Structured Streaming.

## Overview

This example shows how to build an incremental workflow that:
1. **Parses** PDFs and images using [`ai_parse_document`](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_parse_document)
2. **Extracts** clean text with incremental processing
3. **Chunks** text into smaller pieces suitable for embedding
4. **Indexes** chunks using Databricks Vector Search for RAG applications

All stages run as Python notebook tasks in a Databricks Workflow using Structured Streaming with serverless compute.

## Architecture

```
Source Documents (UC Volume)
         ↓
    Task 1: ai_parse_document    → parsed_documents_raw (variant)
         ↓
    Task 2: text extraction      → parsed_documents_text (string)
         ↓
    Task 3: text chunking        → parsed_documents_text_chunked (string)
         ↓
    Task 4: vector search index  → Vector Search Index
```

### Key Features

- **Incremental processing**: Only new files are processed using Structured Streaming checkpoints
- **Serverless compute**: Runs on serverless compute for cost efficiency
- **Task dependencies**: Sequential execution with automatic dependency management
- **Parameterized**: Catalog, schema, volumes, and table names configurable via variables
- **Error handling**: Gracefully handles parsing failures
- **Token-aware chunking**: Smart text splitting based on embedding model tokenization
- **Change Data Feed**: Enables efficient incremental updates through the pipeline

## Prerequisites

- Databricks workspace with Unity Catalog
- Databricks CLI v0.218.0+
- Unity Catalog volumes for:
  - Source documents (PDFs/images)
  - Parsed output images
  - Streaming checkpoints
  - Chunking cache
- AI functions (`ai_parse_document`)
- Embedding model endpoint (e.g., `databricks-gte-large-en`)
- Vector Search endpoint (or it will be created automatically)

## Quick Start

1. **Install and authenticate**
   ```bash
   databricks auth login --host https://your-workspace.cloud.databricks.com
   ```

2. **Configure** `databricks.yml` with your workspace settings

3. **Validate** the bundle configuration
   ```bash
   databricks bundle validate
   ```

4. **Deploy**
   ```bash
   databricks bundle deploy
   ```

5. **Upload documents** to your source volume

6. **Run workflow** from the Databricks UI (Workflows)

## Configuration

Edit `databricks.yml`:

```yaml
variables:
  catalog: main                                                    # Your catalog
  schema: default                                                  # Your schema
  source_volume_path: /Volumes/main/default/source_documents      # Source PDFs
  output_volume_path: /Volumes/main/default/parsed_output         # Parsed images
  checkpoint_base_path: /tmp/checkpoints/ai_parse_workflow        # Checkpoints
  chunking_cache_location: /tmp/cache/chunking                    # Chunking cache
  raw_table_name: parsed_documents_raw                            # Table names
  text_table_name: parsed_documents_text
  chunked_table_name: parsed_documents_text_chunked
  vector_index_name: parsed_documents_vector_index
  embedding_model_endpoint: databricks-gte-large-en               # Embedding model
  vector_search_endpoint_name: vector-search-shared-endpoint      # Vector Search endpoint
```

## Workflow Tasks

### Task 1: Document Parsing
**File**: `src/transformations/01_parse_documents.py`

Uses `ai_parse_document` to extract text, tables, and metadata from PDFs/images:
- Reads files from volume using Structured Streaming
- Stores variant output with bounding boxes
- Incremental: checkpointed streaming prevents reprocessing
- Supports PDF, JPG, JPEG, PNG files

### Task 2: Text Extraction
**File**: `src/transformations/02_extract_text.py`

Extracts clean concatenated text using `transform()`:
- Reads from previous task's table via streaming
- Handles both parser v1.0 and v2.0 formats
- Uses `transform()` for efficient text extraction
- Includes error handling for failed parses
- Enables Change Data Feed (CDF) on output table

### Task 3: Text Chunking
**File**: `src/transformations/03_chunk_text.py`

Chunks text into smaller pieces suitable for embedding:
- Reads from text table via streaming using CDF
- Uses LangChain's RecursiveCharacterTextSplitter
- Token-aware chunking based on embedding model
- Supports multiple embedding models (GTE, BGE, OpenAI)
- Configurable chunk size and overlap
- Creates MD5 hash as chunk_id for deduplication
- Enables Change Data Feed (CDF) on output table

### Task 4: Vector Search Index
**File**: `src/transformations/04_vector_search_index.py`

Creates and manages Databricks Vector Search index:
- Creates or validates Vector Search endpoint
- Creates Delta Sync index from chunked text table
- Automatically generates embeddings using specified model
- Triggers index sync to process new/updated chunks
- Uses triggered pipeline type for on-demand updates
- Robust error handling and status checking

## Project Structure

```
.
├── databricks.yml                      # Bundle configuration
├── requirements.txt                    # Python dependencies
├── resources/
│   └── vector_search_ingestion.job.yml # Workflow definition
├── src/
│   └── transformations/
│       ├── 01_parse_documents.py       # Parse PDFs/images with ai_parse_document
│       ├── 02_extract_text.py          # Extract text from parsed documents
│       ├── 03_chunk_text.py            # Chunk text for embedding
│       └── 04_vector_search_index.py   # Create Vector Search index
└── README.md
```

## Resources

- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/)
- [Databricks Workflows](https://docs.databricks.com/workflows/)
- [Structured Streaming](https://docs.databricks.com/structured-streaming/)
- [`ai_parse_document` Function](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_parse_document)
- [Databricks Vector Search](https://docs.databricks.com/generative-ai/vector-search.html)
- [LangChain Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/)
