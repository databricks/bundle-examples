---
name: configure-volume
description: Expert assistance for Volume resources in Unity Catalog. Use when users want to create volumes for file storage, configure volume access, or integrate volumes with jobs and notebooks.
---

# Resource: Volume - Unity Catalog Volume Configuration

## Instructions

1. **Understand volume needs**
   - Managed or external?
   - Storage location requirements?
   - Access patterns?

2. **Fetch documentation**
   - WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/resources (volumes section)

3. **Find example**
   - knowledge_base/write_from_job_to_volume/

4. **Provide configuration**
   - Volume resource
   - Path references
   - Grants if needed

## Key Patterns

### Managed Volume
```yaml
resources:
  volumes:
    my_volume:
      name: my_volume
      catalog_name: ${var.catalog}
      schema_name: ${var.schema}
      volume_type: MANAGED
      comment: "Managed volume for data files"
```

### External Volume
```yaml
resources:
  volumes:
    external_volume:
      name: external_data
      catalog_name: ${var.catalog}
      schema_name: ${var.schema}
      volume_type: EXTERNAL
      storage_location: "s3://bucket/path/"
```

### Volume with Grants
```yaml
resources:
  volumes:
    shared_volume:
      name: shared_files
      catalog_name: ${var.catalog}
      schema_name: ${var.schema}
      volume_type: MANAGED
      grants:
        - principal: account users
          privileges:
            - READ_VOLUME
            - WRITE_VOLUME
```

## Accessing Volumes

In code, reference volumes:
```python
# Path format: /Volumes/{catalog}/{schema}/{volume}/
volume_path = f"/Volumes/{catalog}/{schema}/{volume_name}/data.csv"

# Read file
df = spark.read.csv(volume_path)

# Write file
df.write.csv(volume_path)
```

## Volume Privileges

- `READ_VOLUME` - Read files
- `WRITE_VOLUME` - Write files

## Examples

```
User: "Create a volume for storing processed data files"

Steps:
1. Read knowledge_base/write_from_job_to_volume/
2. Create managed volume resource
3. Show path format for accessing
4. Explain grants if sharing needed
```
