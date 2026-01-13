---
name: secure-bundle
description: Expert guidance on permissions, grants, and security configurations in bundles. Use when users need help with access control, service principals, secrets, or Unity Catalog grants.
---

# Permissions & Security - Security Configuration Expert

## Instructions

1. **Understand security needs**
   - Who needs access? (users, groups, service principals)
   - What level of access? (view, run, manage)
   - Unity Catalog grants needed?
   - Secrets to manage?

2. **Fetch documentation**
   - WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/permissions
   - WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/run-as

3. **Find examples**
   - knowledge_base/job_read_secret/ - Secret management
   - Look for permissions and grants in examples

4. **Provide configuration**
   - Permissions for bundle resources
   - Grants for Unity Catalog resources
   - Service principal setup
   - Secret access patterns

## Resource Permissions

### Bundle-Level Permissions
```yaml
targets:
  prod:
    mode: production
    permissions:
      - user_name: deployer@company.com
        level: CAN_MANAGE
      - group_name: data_engineers
        level: CAN_RUN
      - group_name: analysts
        level: CAN_VIEW
      - service_principal_name: sp-automation
        level: CAN_MANAGE
```

### Resource-Level Permissions
```yaml
resources:
  jobs:
    sensitive_job:
      name: "Sensitive Data Processing"
      permissions:
        - group_name: data_engineers
          level: CAN_MANAGE
        - group_name: analysts
          level: CAN_VIEW
      # ... job config
```

### Permission Levels

| Level | Can View | Can Run | Can Modify | Use When |
|-------|----------|---------|------------|----------|
| `CAN_VIEW` | ✓ | ✗ | ✗ | Read-only access |
| `CAN_RUN` | ✓ | ✓ | ✗ | Execute but not modify |
| `CAN_MANAGE` | ✓ | ✓ | ✓ | Full control |
| `IS_OWNER` | ✓ | ✓ | ✓ | Ownership |

## Unity Catalog Grants

### Schema Grants
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
        - principal: data_engineers
          privileges:
            - CREATE
```

### Model Grants
```yaml
resources:
  registered_models:
    my_model:
      name: ${var.catalog}.${var.schema}.my_model
      catalog_name: ${var.catalog}
      schema_name: ${var.schema}
      grants:
        - principal: account users
          privileges:
            - EXECUTE
```

### Volume Grants
```yaml
resources:
  volumes:
    shared_volume:
      name: shared_data
      catalog_name: ${var.catalog}
      schema_name: ${var.schema}
      volume_type: MANAGED
      grants:
        - principal: data_engineers
          privileges:
            - READ_VOLUME
            - WRITE_VOLUME
        - principal: analysts
          privileges:
            - READ_VOLUME
```

## Service Principal Execution

### Run As Service Principal
```yaml
targets:
  prod:
    mode: production
    run_as:
      service_principal_name: sp-prod-etl
    permissions:
      - user_name: deployer@company.com
        level: CAN_MANAGE
```

**Benefits:**
- More secure than user accounts
- Better for automation
- Consistent execution identity
- Easier credential management

### Setting Up Service Principal
1. Create service principal in Databricks
2. Grant necessary permissions
3. Configure in bundle
4. Service principal needs:
   - Workspace access
   - Unity Catalog permissions
   - Secret scope access (if using secrets)

## Secret Management

### Using Secrets in Jobs
```yaml
resources:
  jobs:
    secret_job:
      name: "Job with Secrets"
      tasks:
        - task_key: process
          spark_python_task:
            python_file: ./src/process.py
          spark_conf:
            spark.api_key: "{{secrets/my_scope/api_key}}"
            spark.api_secret: "{{secrets/my_scope/api_secret}}"
```

### Accessing Secrets in Python
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
api_key = w.dbutils.secrets.get(scope="my_scope", key="api_key")
```

### Secret Best Practices
1. **Never hardcode secrets** in bundle files
2. **Use Databricks secrets** for sensitive data
3. **Scope access properly** - grant only to needed principals
4. **Rotate secrets regularly**
5. **Use service principals** for secret access in prod

## Common Patterns

### Multi-Tier Access
```yaml
targets:
  prod:
    mode: production
    permissions:
      # Deployers - can manage
      - user_name: deployer@company.com
        level: CAN_MANAGE

      # Engineers - can run and modify
      - group_name: data_engineers
        level: CAN_MANAGE

      # Operators - can run only
      - group_name: data_operators
        level: CAN_RUN

      # Analysts - can view only
      - group_name: analysts
        level: CAN_VIEW
```

### Development Permissions
```yaml
targets:
  dev:
    mode: development  # Automatic per-user permissions
    default: true
    # No explicit permissions needed - each developer gets their own resources
```

### Least Privilege Principle
```yaml
resources:
  jobs:
    reporting_job:
      name: "Daily Report"
      permissions:
        - group_name: report_viewers
          level: CAN_VIEW  # Only view, not run
      # ...

  jobs:
    data_pipeline:
      name: "Data Pipeline"
      permissions:
        - group_name: data_engineers
          level: CAN_MANAGE  # Full control for engineers
        - group_name: sre_team
          level: CAN_RUN  # SRE can run but not modify
```

## Unity Catalog Privileges

**Schema/Catalog:**
- `USE CATALOG` - Access catalog
- `USE SCHEMA` - Access schema
- `CREATE` - Create objects
- `SELECT` - Read data
- `MODIFY` - Write data

**Models:**
- `EXECUTE` - Run model inference

**Volumes:**
- `READ_VOLUME` - Read files
- `WRITE_VOLUME` - Write files

## Security Checklist

- [ ] Production uses service principals for execution
- [ ] Explicit permissions in production target
- [ ] No hardcoded secrets in configuration
- [ ] Secrets accessed via Databricks secrets
- [ ] Least privilege access (CAN_VIEW < CAN_RUN < CAN_MANAGE)
- [ ] Groups used instead of individual users where possible
- [ ] Unity Catalog grants configured for shared resources
- [ ] Service principals have minimum necessary permissions

## Examples

```
User: "Set up permissions for prod with different access levels"

Steps:
1. Read knowledge_base examples
2. Configure prod target with mode: production
3. Add permissions with appropriate levels
4. Set up service principal for run_as
5. Explain permission levels
```

```
User: "Job needs to access API key from secrets"

Steps:
1. Read knowledge_base/job_read_secret/
2. Show {{secrets/scope/key}} syntax
3. Configure in spark_conf or parameters
4. Explain secret scope access
5. Show Python code to access secrets
```
