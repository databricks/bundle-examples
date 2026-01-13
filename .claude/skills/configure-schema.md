---
name: configure-schema
description: Expert assistance for Schema and Catalog resources in Unity Catalog. Use when users want to create schemas, configure catalogs, set up database instances, or manage Unity Catalog resources.
---

# Resource: Schema - Unity Catalog Schema Configuration

## Instructions

1. **Understand catalog/schema needs**
   - Unity Catalog hierarchy
   - Grants needed?
   - Database instance (OLTP) needed?

2. **Fetch documentation**
   - WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/resources (schemas section)

3. **Find examples**
   - knowledge_base/database_with_catalog/
   - knowledge_base/write_from_job_to_volume/

4. **Provide configuration**
   - Schema resource
   - Grants if needed
   - Database catalog if OLTP

## Key Patterns

### Basic Schema
```yaml
resources:
  schemas:
    my_schema:
      name: ${var.catalog}.${var.schema}
      comment: "Main schema for data pipeline"
```

### Schema with Grants
```yaml
resources:
  schemas:
    shared_schema:
      name: ${var.catalog}.${var.schema}
      grants:
        - principal: account users
          privileges:
            - SELECT
            - MODIFY
```

### Database Instance (OLTP)
```yaml
resources:
  database_instances:
    app_database:
      name: "app-db"
      instance_size: SMALL
      description: "Application database"

  database_catalogs:
    app_catalog:
      name: "app_catalog"
      database_instance:
        database_instance_source:
          database_instance_id: ${resources.database_instances.app_database.id}
```

## Unity Catalog Hierarchy

```
Catalog
└── Schema
    ├── Tables
    ├── Views
    ├── Functions
    └── Volumes
```

## Grant Privileges

- `SELECT` - Read data
- `MODIFY` - Write data
- `CREATE` - Create objects
- `EXECUTE` - Run functions
- `USE CATALOG` - Access catalog
- `USE SCHEMA` - Access schema

## Examples

```
User: "Create a schema with read access for all users"

Steps:
1. Read knowledge_base schema examples
2. Create schema resource
3. Add grants with SELECT privilege
4. Explain catalog.schema naming
```
