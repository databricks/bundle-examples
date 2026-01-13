---
name: manage-variables
description: Expert assistance with variables, interpolation, and resource references in bundles. Use when users need help with variable syntax, referencing resources, or understanding interpolation patterns.
---

# Variables & References - Variable and Interpolation Expert

## Instructions

1. **Understand variable needs**
   - What values vary per environment?
   - What resources need to reference each other?
   - What workspace context needed?

2. **Fetch documentation**
   - WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/variables

3. **Find examples**
   - Grep for variable patterns across examples
   - Look for ${var.}, ${resources.}, ${workspace.} usage

4. **Provide guidance**
   - Variable declarations
   - Target-specific values
   - Interpolation syntax
   - Resource references

## Variable Declaration

```yaml
variables:
  catalog:
    description: "Unity Catalog catalog name"
    default: "default_catalog"  # Optional default

  schema:
    description: "Schema for tables and views"
    # No default - must be provided in targets

  warehouse_id:
    description: "SQL Warehouse ID"

targets:
  dev:
    variables:
      catalog: dev_catalog
      schema: ${workspace.current_user.short_name}
      warehouse_id: "abc123"

  prod:
    variables:
      catalog: prod_catalog
      schema: prod
      warehouse_id: "xyz789"
```

## Interpolation Syntax

### User-Defined Variables
```yaml
${var.catalog}
${var.schema}
${var.warehouse_id}
```

### Bundle Metadata
```yaml
${bundle.name}           # Bundle name
${bundle.target}         # Current target (dev, prod, etc.)
${bundle.uuid}           # Bundle UUID
```

### Workspace Context
```yaml
${workspace.current_user.short_name}    # username (before @)
${workspace.current_user.userName}      # full email
${workspace.file_path}                  # Bundle file path in workspace
```

### Resource References
```yaml
${resources.jobs.my_job.id}                    # Job ID
${resources.pipelines.my_pipeline.id}          # Pipeline ID
${resources.schemas.my_schema.id}              # Schema ID
${resources.volumes.my_volume.id}              # Volume ID
${resources.models.my_model.id}                # Model ID
${resources.database_instances.my_db.id}       # Database instance ID
```

## Common Patterns

### Schema with User Isolation (Dev)
```yaml
variables:
  catalog:
    description: "Catalog name"
  schema:
    description: "Schema name"

targets:
  dev:
    mode: development
    variables:
      catalog: dev
      schema: ${workspace.current_user.short_name}  # Each user gets own schema
```

### Job Referencing Pipeline
```yaml
resources:
  pipelines:
    my_pipeline:
      name: "ETL Pipeline"
      # ... pipeline config

  jobs:
    pipeline_job:
      name: "Run Pipeline"
      tasks:
        - task_key: refresh
          pipeline_task:
            pipeline_id: ${resources.pipelines.my_pipeline.id}
```

### Cross-Resource Dependencies
```yaml
resources:
  schemas:
    my_schema:
      name: ${var.catalog}.${var.schema}

  volumes:
    my_volume:
      name: data_volume
      catalog_name: ${var.catalog}
      schema_name: ${var.schema}
      depends_on:
        - ${resources.schemas.my_schema.id}
```

### Path Construction
```yaml
resources:
  jobs:
    my_job:
      name: "${bundle.target}_etl_job"  # dev_etl_job, prod_etl_job
      tasks:
        - task_key: process
          spark_python_task:
            python_file: ${workspace.file_path}/src/process.py
            parameters:
              - "--catalog"
              - "${var.catalog}"
              - "--schema"
              - "${var.schema}"
```

## Variable Best Practices

1. **Use variables for environment-specific values**
   - Catalog/schema names
   - Cluster sizes
   - Warehouse IDs
   - Any value that changes per target

2. **Add descriptions to all variables**
   - Helps team understand purpose
   - Self-documenting configuration

3. **Use defaults sparingly**
   - Better to explicitly set in targets
   - Makes environment config visible

4. **Use workspace.current_user for dev isolation**
   - `${workspace.current_user.short_name}` for schemas
   - Enables multi-developer workflows

5. **Use resource references for dependencies**
   - Ensures correct deployment order
   - Makes dependencies explicit
   - Prevents hardcoding IDs

## Common Mistakes

```yaml
# WRONG - Missing ${}
catalog: var.catalog

# WRONG - Wrong syntax
catalog: {var.catalog}

# WRONG - Typo in property
schema: ${workspace.user.short_name}

# WRONG - Wrong resource type (plural)
pipeline_id: ${resources.pipeline.my_pipeline.id}  # Should be "pipelines"

# CORRECT
catalog: ${var.catalog}
schema: ${workspace.current_user.short_name}
pipeline_id: ${resources.pipelines.my_pipeline.id}
```

## Examples

```
User: "How do I make catalog name different per environment?"

Steps:
1. Show variable declaration
2. Configure catalog variable
3. Set different values in dev vs prod targets
4. Show usage: ${var.catalog}
5. Explain interpolation at deployment time
```

```
User: "Job needs to reference a pipeline"

Steps:
1. Show resource reference syntax
2. Use ${resources.pipelines.name.id}
3. Explain dependency handling
4. Show complete example with both resources
```
