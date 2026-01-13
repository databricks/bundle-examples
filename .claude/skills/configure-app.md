---
name: configure-app
description: Expert assistance for Databricks Apps resources. Use when users want to deploy apps (Dash, Streamlit, Gradio, etc.) or configure app integrations with databases.
---

# Resource: App - Databricks Apps Configuration

## Instructions

1. **Understand app type**
   - What framework? (Dash, Streamlit, Gradio)
   - Database connections needed?
   - Permissions required?

2. **Fetch documentation**
   - WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/resources (apps section)

3. **Find examples**
   - knowledge_base/databricks_app/
   - knowledge_base/app_with_database/

4. **Provide configuration**
   - App resource YAML
   - source_code_path
   - Database connections if needed

## Key Patterns

### Basic App
```yaml
resources:
  apps:
    my_app:
      name: "My Dashboard App"
      source_code_path: ./src/app
```

### App with Database
```yaml
resources:
  database_instances:
    app_db:
      name: "app-database"
      instance_size: SMALL

  apps:
    my_app:
      name: "App with Database"
      source_code_path: ./src/app
      resources:
        - name: main_db
          database_instance:
            database_instance_source:
              database_instance_id: ${resources.database_instances.app_db.id}
          permission: CAN_CONNECT_AND_CREATE
```

### App with Permissions
```yaml
resources:
  apps:
    team_app:
      name: "Team Dashboard"
      source_code_path: ./src/app
      permissions:
        - group_name: analysts
          level: CAN_VIEW
        - group_name: engineers
          level: CAN_MANAGE
```

## Examples

```
User: "Deploy a Streamlit app with database access"

Steps:
1. Read knowledge_base/app_with_database/
2. Configure database_instances resource
3. Configure app with database reference
4. Explain app structure and requirements
```
