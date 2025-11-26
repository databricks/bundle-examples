# autoloader_lakeflow_pipeline

This pipeline demonstrates incremental data ingestion from Unity Catalog Volumes using Databricks AutoLoader.

## Overview

AutoLoader (cloudFiles) provides an optimized way to incrementally process new data files as they arrive in cloud storage. It automatically handles:
- Schema inference and evolution
- Exactly-once processing guarantees
- Efficient tracking of processed files
- Scalability to millions of files

## Pipeline Structure

### Bronze Layer (`transformations/`)
- **`ingest_autoloader.py`**: AutoLoader ingestion with multiple examples

#### Tables Created:
1. **`autoloader_data`**: Generic AutoLoader table (configurable format)
2. **`autoloader_json_data`**: JSON-specific ingestion
3. **`autoloader_csv_data`**: CSV-specific ingestion

## Configuration

Set these Spark configurations in the pipeline YAML:

### Required
- `volume_path`: Path to Unity Catalog Volume (e.g., `/Volumes/catalog/schema/volume_name/data`)

### Optional
- `file_format`: Format of files (`json`, `csv`, `parquet`, `avro`, `text`) - default: `json`
- `schema_location`: Custom schema checkpoint location - default: `{volume_path}/_schema`
- `json_volume_path`: Specific path for JSON files
- `csv_volume_path`: Specific path for CSV files

## AutoLoader Features

### Schema Evolution
- **`addNewColumns`**: Automatically adds new columns when detected (default)
- **`rescue`**: Captures unexpected data in a `_rescued_data` column
- **`failOnNewColumns`**: Fails the stream when new columns appear

### File Formats Supported
- JSON
- CSV
- Parquet
- Avro
- Text
- Binary

### Key Options
- `cloudFiles.format`: File format to process
- `cloudFiles.schemaLocation`: Checkpoint location for schema tracking
- `cloudFiles.inferColumnTypes`: Automatically infer column types
- `cloudFiles.schemaEvolutionMode`: How to handle schema changes
- `cloudFiles.maxFilesPerTrigger`: Limit files processed per micro-batch

## Unity Catalog Volume Setup

### Create a Volume
```sql
CREATE VOLUME IF NOT EXISTS catalog.schema.volume_name;
```

### Upload Files
Upload files to the volume using:
- Databricks UI
- `dbutils.fs.cp()`
- Cloud provider CLI tools
- REST API

### Example Paths
```
/Volumes/lakehouse_bronze_dev/fake_data/landing_zone/json/
/Volumes/lakehouse_bronze_dev/fake_data/landing_zone/csv/
/Volumes/lakehouse_bronze_dev/fake_data/landing_zone/parquet/
```

## Deployment

```bash
# Deploy to development
databricks bundle deploy --target dev

# Run the pipeline
databricks bundle run pipeline_autoloader_lakeflow_pipeline
```

## Example Configuration in Pipeline YAML

```yaml
configuration:
  bronze_catalog: ${var.bronze_catalog}
  bronze_schema: ${resources.schemas.autoloader_bronze_schema.name}
  volume_path: /Volumes/${var.bronze_catalog}/${resources.schemas.autoloader_bronze_schema.name}/landing_zone/json
  file_format: json
  json_volume_path: /Volumes/${var.bronze_catalog}/${resources.schemas.autoloader_bronze_schema.name}/landing_zone/json
  csv_volume_path: /Volumes/${var.bronze_catalog}/${resources.schemas.autoloader_bronze_schema.name}/landing_zone/csv
```

## Processing Pattern

```
Unity Catalog Volume → AutoLoader → Bronze Tables → Silver Tables → Gold Tables
```

### Data Flow
1. **Source**: Files uploaded to Unity Catalog Volume
2. **Bronze**: AutoLoader streams new files into raw tables
3. **Silver**: Apply data quality and transformations
4. **Gold**: Create dimensional models for analytics

## Monitoring

AutoLoader provides detailed metrics:
- Number of files processed
- Number of rows processed
- Processing latency
- Schema evolution events

Access metrics via:
- Pipeline event logs
- Spark UI
- Delta Live Tables UI

## Best Practices

1. **Organize by format**: Use separate folders for different file formats
2. **Schema location**: Keep schema checkpoints separate from data
3. **Idempotency**: AutoLoader ensures exactly-once processing
4. **Schema evolution**: Use `addNewColumns` for flexible ingestion
5. **Volume organization**: Structure volumes by source system or data type

## Dependencies

- Unity Catalog enabled
- Delta Live Tables
- Framework package
- PySpark
