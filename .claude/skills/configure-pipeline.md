---
name: configure-pipeline
description: Expert assistance for configuring Delta Live Tables (DLT) pipeline resources. Use when users want to create/modify pipelines, set up data transformations, or configure streaming pipelines.
---

# Resource: Pipeline - DLT Pipeline Configuration

## Instructions

When helping with pipeline resources:

1. **Understand pipeline needs**
   - Python or SQL based?
   - Streaming or batch?
   - Schema and catalog requirements

2. **Fetch documentation**
   - WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/resources (pipelines section)

3. **Find examples**
   - lakeflow_pipelines_python/ - Python DLT
   - lakeflow_pipelines_sql/ - SQL DLT
   - knowledge_base/pipeline_with_schema/ - With Unity Catalog
   - default_python/resources/default_python_etl.pipeline.yml

4. **Provide configuration**
   - Pipeline resource YAML
   - Library paths
   - Schema/catalog setup
   - Compute configuration

## Key Patterns

### Basic Python Pipeline
```yaml
resources:
  pipelines:
    my_pipeline:
      name: "ETL Pipeline"
      libraries:
        - notebook:
            path: ./src/notebooks/etl.py
      target: ${var.catalog}.${var.schema}
      channel: CURRENT
```

### Serverless Pipeline
```yaml
resources:
  pipelines:
    serverless_pipeline:
      name: "Serverless DLT"
      libraries:
        - notebook:
            path: ./src/notebooks/transform.py
      target: ${var.catalog}.${var.schema}
      catalog: ${var.catalog}
      channel: CURRENT  # Serverless by default
```

### Pipeline with Cluster
```yaml
resources:
  pipelines:
    cluster_pipeline:
      name: "Cluster-based Pipeline"
      libraries:
        - notebook:
            path: ./src/notebooks/process.py
      target: ${var.catalog}.${var.schema}
      clusters:
        - label: default
          node_type_id: ${var.cluster_node_type}
          num_workers: ${var.cluster_workers}
```

### SQL Pipeline
```yaml
resources:
  pipelines:
    sql_pipeline:
      name: "SQL DLT Pipeline"
      libraries:
        - file:
            path: ./src/dlt/transforms.sql
      target: ${var.catalog}.${var.schema}
```

### Continuous Pipeline
```yaml
resources:
  pipelines:
    streaming_pipeline:
      name: "Continuous Streaming"
      libraries:
        - notebook:
            path: ./src/streaming/ingest.py
      target: ${var.catalog}.${var.schema}
      continuous: true
```

## Related Skills

- `resource-job` - To trigger pipelines with pipeline_task
- `resource-schema` - For schema configuration
- `variables-references` - For catalog/schema variables

## Examples

```
User: "Create a DLT pipeline for Python transformations"

Steps:
1. Read lakeflow_pipelines_python/ example
2. Generate pipeline with notebook library
3. Configure target schema
4. Explain DLT expectations and table definitions
```
