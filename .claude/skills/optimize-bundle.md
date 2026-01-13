---
name: optimize-bundle
description: Provide expert guidance on bundle design patterns, architectural decisions, and best practices for structuring Databricks Asset Bundles. Use when users ask about best ways to structure bundles, deployment strategies, or optimization.
---

# Bundle Best Practices - Design & Architecture Guidance

## Instructions

When providing bundle best practices guidance:

1. **Understand the context**
   - Learn about project complexity, team size, environments
   - Understand current pain points or goals

2. **Fetch best practices documentation**
   - Use WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/faqs
   - Use WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes
   - Use WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/sharing

3. **Find relevant patterns**
   - Use Glob to find examples demonstrating the pattern
   - knowledge_base/ has focused examples of specific patterns
   - mlops_stacks/ and contrib/databricks_ingestion_monitoring/ show production patterns

4. **Provide actionable recommendations**
   - Show specific code examples from repository
   - Explain trade-offs of different approaches
   - Give incremental improvement steps

## Key Best Practices

### 1. Deployment Mode Strategy

**Development mode** (for dev/testing):
```yaml
targets:
  dev:
    mode: development  # Auto-prefixes resources with [dev username]
    default: true
    variables:
      schema: ${workspace.current_user.short_name}  # User-specific
```

**Benefits:** Multiple developers can deploy simultaneously, schedules paused, isolated resources

**Production mode** (for staging/prod):
```yaml
targets:
  prod:
    mode: production  # Clean resource names, schedules active
    permissions:
      - user_name: deployer@company.com
        level: CAN_MANAGE
    run_as:
      service_principal_name: sp-prod-bundle
```

**Benefits:** No prefixing, explicit permissions, service principal execution

### 2. Variable Management

Use variables for environment-specific values:
```yaml
variables:
  catalog:
    description: "Unity Catalog catalog"
  cluster_size:
    description: "Cluster node type"

targets:
  dev:
    variables:
      catalog: dev_catalog
      cluster_size: i3.xlarge
  prod:
    variables:
      catalog: prod_catalog
      cluster_size: i3.4xlarge
```

### 3. Resource Organization

**Small projects (< 5 resources):**
```
project/
├── databricks.yml
├── resources/
│   ├── job.job.yml
│   └── pipeline.pipeline.yml
```

**Medium projects:**
```
project/
├── databricks.yml
├── resources/
│   ├── jobs/
│   ├── pipelines/
│   └── schemas/
```

**Large projects:**
```
project/
├── databricks.yml
├── resources/
│   ├── infrastructure/
│   ├── ingestion/
│   ├── transformation/
│   └── serving/
```

### 4. Naming Conventions

- **Bundles:** lowercase_with_underscores
- **Files:** resource_name.type.yml (e.g., etl_job.job.yml)
- **Variables:** Clear purpose (catalog, schema, warehouse_id)
- Let deployment mode handle prefixing

### 5. Permission Strategy

**Development:** Automatic via mode: development

**Production:**
```yaml
targets:
  prod:
    mode: production
    permissions:
      - group_name: data_engineers  # Use groups
        level: CAN_RUN
      - user_name: deployer@company.com
        level: CAN_MANAGE
    run_as:
      service_principal_name: sp-prod  # Service principal execution
```

### 6. Sharing Code Across Bundles

**Reference:** knowledge_base/share_files_across_bundles/

```yaml
# In bundle databricks.yml
include:
  - ../shared/config/common_variables.yml

sync:
  paths:
    - ../shared/lib  # Share Python libraries
```

### 7. Serverless-First Strategy

Prefer serverless for new workloads:
```yaml
resources:
  jobs:
    my_job:
      name: "Serverless Job"
      tasks:
        - task_key: process
          python_wheel_task:
            package_name: my_project
            entry_point: main
          libraries:
            - whl: ./dist/*.whl
```

**Benefits:** Lower cost, faster startup, no cluster management, auto-scaling

**Reference:** knowledge_base/serverless_job/

### 8. Secret Management

Never hardcode secrets:
```yaml
# WRONG
variables:
  api_key: "sk_live_123"  # Never!

# RIGHT - Use Databricks secrets
tasks:
  - task_key: process
    spark_conf:
      spark.api_key: "{{secrets/my_scope/api_key}}"
```

**Reference:** knowledge_base/job_read_secret/

### 9. Artifact Management

```yaml
artifacts:
  python_artifact:
    type: whl
    build: uv build --wheel  # Fast, modern package manager

# pyproject.toml
[project]
dependencies = [
    "databricks-sdk>=0.1.0,<1.0.0",  # Pin major versions
]
```

### 10. Target-Specific Resources

**Reference:** knowledge_base/target_includes/

```yaml
targets:
  staging:
    resources:
      include:
        - resources/staging_*.yml  # Staging-only resources
  prod:
    resources:
      include:
        - resources/prod_*.yml  # Production-only resources
```

## Common Anti-Patterns to Avoid

### ❌ Hardcoded Values
```yaml
# BAD
new_cluster:
  node_type_id: "i3.xlarge"  # Hardcoded

# GOOD
new_cluster:
  node_type_id: ${var.cluster_node_type}
```

### ❌ No UUID
```yaml
# BAD
bundle:
  name: my_bundle

# GOOD
bundle:
  name: my_bundle
  uuid: "550e8400-e29b-41d4-a716-446655440000"
```

### ❌ Production Without Permissions
```yaml
# BAD
targets:
  prod:
    mode: production

# GOOD
targets:
  prod:
    mode: production
    permissions:
      - user_name: deployer@company.com
        level: CAN_MANAGE
```

### ❌ Monolithic Files
Break large configurations into focused, modular files

## Architectural Patterns

### Multi-Bundle Architecture
**When:** Large organization, multiple teams, different deployment schedules
```
org/
├── infrastructure-bundle/
├── ingestion-bundle/
├── transformation-bundle/
└── serving-bundle/
```

### Monorepo Bundle
**When:** Single team, tightly coupled workflows
```
data-platform/
├── databricks.yml
├── resources/
│   ├── infrastructure/
│   ├── ingestion/
│   └── transformation/
```

### Environment Promotion
Deploy through: `dev` → `staging` → `prod`

Use same bundle, different targets with appropriate modes and permissions

## Quality Checklist

Guide users to verify:
- [ ] UUID present and unique
- [ ] Variables for environment-specific values
- [ ] Development mode for dev
- [ ] Production mode with permissions for prod
- [ ] Service principal for prod execution
- [ ] Secrets via Databricks secrets
- [ ] Resources organized logically
- [ ] Naming conventions followed
- [ ] Serverless considered
- [ ] Dependencies minimal and pinned

## Related Skills

- `bundle-create` - Initial setup with best practices
- `bundle-validate` - Ensure compliance
- `deployment-modes` - Deep dive on dev vs prod
- `variables-references` - Variable management
- `permissions-security` - Security patterns
- All resource skills - Resource-specific practices

## Examples

### Example 1: Improving Bundle Structure
```
User: "My bundle is getting messy with 20+ resources"

Guidance:
1. Show knowledge_base examples with good organization
2. Recommend grouping by function (infrastructure/, ingestion/, etc.)
3. Update include paths to match new structure
4. Use variables to reduce duplication
```

### Example 2: Preparing for Production
```
User: "Ready to deploy to production, what should I check?"

Checklist:
1. mode: production in prod target
2. Explicit permissions configured
3. Service principal for run_as
4. Secrets properly managed
5. Variables set for prod environment
6. Schedules configured appropriately
7. Error notifications set up
```
