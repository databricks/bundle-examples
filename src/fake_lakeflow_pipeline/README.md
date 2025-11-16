# fake_lakeflow_pipeline

This pipeline demonstrates reading from a custom Faker data source into a bronze layer table.

## Overview

A simple pipeline that uses a custom PySpark DataSource to generate synthetic data with the Faker library.

## Data Source

The custom `FakeDataSource` generates data with the following fixed schema:
- `name` (string)
- `date` (string)  
- `zipcode` (string)
- `state` (string)

## Pipeline Structure

### Bronze Layer
- **Table**: `fake_data`
- **Source**: Custom Faker data source via `spark.read.format("fake").load()`
- **Rows**: 1,000 synthetic records
- **Processing**: Raw ingestion + metadata columns (`ingest_timestamp`)

## Deployment

```bash
# Deploy to development
databricks bundle deploy --target dev

# Run the pipeline
databricks bundle run pipeline_fake_lakeflow_pipeline
```

## Dependencies

- Python >=3.10, <=3.13
- Faker library
- Framework package
- PySpark with Delta Live Tables
