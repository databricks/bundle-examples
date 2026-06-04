# AI Document Processing Pipeline with Lakeflow

A Databricks Asset Bundle demonstrating **incremental document processing** using `ai_parse_document`, `ai_query`, and Lakeflow Declarative Pipelines.

## Overview

This example shows how to build an incremental streaming pipeline that:
1. **Parses** PDFs and images using [`ai_parse_document`](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_parse_document)
2. **Extracts** clean text with incremental processing
3. **Analyzes** content using [`ai_query`](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_query) with LLMs

All stages use [Lakeflow Declarative Pipelines](https://docs.databricks.com/aws/en/dlt/concepts) streaming tables for efficient incremental processing.

## Architecture

```
Source Documents (UC Volume)
         ↓
    ai_parse_document → parsed_documents_raw (variant)
         ↓
    text extraction   → parsed_documents_text (string)
         ↓
    ai_query          → parsed_documents_structured (json)
```

### Key Features

- **Incremental processing**: Only new files are processed using Lakeflow streaming tables
- **Error handling**: Gracefully handles parsing failures
- **Visual debugging**: Interactive notebook for inspecting results

## Prerequisites

- Databricks workspace with Unity Catalog
- Databricks CLI v0.218.0+
- Unity Catalog volumes for:
  - Source documents (PDFs/images)
  - Parsed output images
- AI functions (`ai_parse_document`, `ai_query`)

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

6. **Run pipeline** from the Databricks UI (Lakeflow Pipelines)

## Configuration

Edit `databricks.yml`:

```yaml
variables:
  catalog: main                                          # Your catalog
  schema: default                                        # Your schema
  source_volume_path: /Volumes/main/default/source_docs # Source PDFs
  output_volume_path: /Volumes/main/default/parsed_out  # Parsed images
```

## Pipeline Stages

### Stage 1: Document Parsing
**File**: `src/transformations/ai_parse_document_variant.sql`

Uses `ai_parse_document` to extract text, tables, and metadata from PDFs/images:
- Reads files from volume using `READ_FILES`
- Stores variant output with bounding boxes
- Incremental: processes only new files

### Stage 2: Text Extraction
**File**: `src/transformations/ai_parse_document_text.sql`

Extracts clean concatenated text using `transform()`:
- Handles both parser v1.0 and v1.1 formats
- Uses `transform()` for incremental append (no aggregations)
- Includes error handling for failed parses

### Stage 3: AI Query Extraction
**File**: `src/transformations/ai_query_extraction.sql`

Applies LLM to extract structured insights:
- Uses `ai_query` with Claude Sonnet 4
- Customizable prompt for domain-specific extraction
- Outputs structured JSON

## Visual Debugger

The included notebook visualizes parsing results with interactive bounding boxes.

**Open**: `src/explorations/ai_parse_document -- debug output.py`

**Configure widgets**:
- `input_file`: `/Volumes/main/default/source_docs/sample.pdf`
- `image_output_path`: `/Volumes/main/default/parsed_out/`
- `page_selection`: `all` (or `1-3`, `1,5,10`)

**Features**:
- Color-coded bounding boxes by element type
- Hover tooltips showing extracted content
- Automatic image scaling
- Page selection support

## Customization

**Change source file patterns**:
```sql
-- In ai_parse_document_variant.sql
FROM STREAM READ_FILES(
  '/Volumes/main/default/source_docs/*.{pdf,jpg,png}',
  format => 'binaryFile'
)
```

**Customize AI extraction**:
```sql
-- In ai_query_extraction.sql
ai_query(
  'databricks-claude-sonnet-4',
  concat('Extract key dates and amounts from: ', text),
  returnType => 'STRING',
  modelParameters => named_struct('max_tokens', 2000, 'temperature', 0.1)
)
```

## Project Structure

```
.
├── databricks.yml                      # Bundle configuration
├── resources/
│   └── ai_parse_document_pipeline.pipeline.yml
├── src/
│   ├── transformations/
│   │   ├── ai_parse_document_variant.sql
│   │   ├── ai_parse_document_text.sql
│   │   └── ai_query_extraction.sql
│   └── explorations/
│       └── ai_parse_document -- debug output.py
└── README.md
```

## Key Concepts

### Incremental Processing with Lakeflow
Streaming tables process only new data:
```sql
CREATE OR REFRESH STREAMING TABLE table_name AS (
  SELECT * FROM STREAM(source_table)
)
```

### Avoiding Complete Mode
Using `transform()` instead of aggregations enables incremental append:
```sql
-- Good: Incremental append
transform(array, element -> element.content)

-- Avoid: Forces complete mode
collect_list(...) GROUP BY ...
```

## Resources

- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/)
- [Lakeflow Declarative Pipelines](https://docs.databricks.com/aws/en/dlt/concepts)
- [`ai_parse_document` Function](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_parse_document)
- [`ai_query` Function](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_query)

