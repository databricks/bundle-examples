---
name: configure-environments
description: Expert guidance on deployment modes and target configurations. Use when users need help with dev/prod environments, target setup, or environment-specific configuration.
---

# Deployment Modes - Target Configuration Expert

## Instructions

1. **Understand environment needs**
   - How many environments? (dev, staging, prod)
   - Multiple developers?
   - Deployment strategy?

2. **Fetch documentation**
   - WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes

3. **Find examples**
   - All databricks.yml files show target patterns
   - Look for development vs production mode usage

4. **Provide guidance**
   - Target configurations
   - Mode selection (development vs production)
   - Variable overrides per target
   - Permission strategies

## Key Concepts

### Development Mode
```yaml
targets:
  dev:
    mode: development
    default: true
    workspace:
      host: https://workspace.databricks.com
    variables:
      catalog: dev_catalog
      schema: ${workspace.current_user.short_name}
```

**Behavior:**
- Auto-prefixes resources: `[dev username] Job Name`
- Pauses job schedules automatically
- Multiple developers can deploy simultaneously
- Each user gets isolated resources
- Default permission is deploying user

### Production Mode
```yaml
targets:
  prod:
    mode: production
    workspace:
      host: https://workspace.databricks.com
      root_path: /Workspace/Users/user@company.com/.bundle/${bundle.name}/${bundle.target}
    variables:
      catalog: prod_catalog
      schema: prod
    permissions:
      - user_name: deployer@company.com
        level: CAN_MANAGE
      - group_name: data_engineers
        level: CAN_RUN
    run_as:
      service_principal_name: sp-prod-bundle
```

**Behavior:**
- No resource prefixing (clean names)
- Schedules run as configured
- Requires explicit permissions
- Should use service principal for execution
- Single deployment (not per-user)

## Multi-Environment Setup

### Standard Pattern
```yaml
targets:
  dev:
    mode: development
    default: true
    workspace:
      host: https://dev-workspace.databricks.com

  staging:
    mode: production  # Treat staging like prod
    workspace:
      host: https://staging-workspace.databricks.com
    permissions:
      - user_name: deployer@company.com
        level: CAN_MANAGE

  prod:
    mode: production
    workspace:
      host: https://prod-workspace.databricks.com
    permissions:
      - user_name: deployer@company.com
        level: CAN_MANAGE
    run_as:
      service_principal_name: sp-prod
```

### Target-Specific Variables
```yaml
variables:
  catalog:
    description: "Catalog name"
  cluster_size:
    description: "Cluster node type"

targets:
  dev:
    mode: development
    variables:
      catalog: dev
      cluster_size: i3.xlarge

  prod:
    mode: production
    variables:
      catalog: prod
      cluster_size: i3.4xlarge
```

### Target-Specific Resources
```yaml
targets:
  dev:
    mode: development
    resources:
      include:
        - resources/dev_*.yml

  prod:
    mode: production
    resources:
      include:
        - resources/prod_*.yml
```

## Best Practices

1. **Always use development mode for dev target**
   - Enables safe multi-developer workflows
   - Automatic resource isolation

2. **Production mode requires explicit permissions**
   - Never deploy to prod without permissions
   - Use service principals for execution

3. **Use variables for environment differences**
   - Catalog names
   - Schema names
   - Cluster sizes
   - Warehouse IDs

4. **Set default: true on one target**
   - Usually dev target
   - Allows `databricks bundle deploy` without `-t` flag

5. **Use service principals in production**
   - More secure than user accounts
   - Better for automation

## Deployment Commands

```bash
# Deploy to default target (dev)
databricks bundle deploy

# Deploy to specific target
databricks bundle deploy -t staging
databricks bundle deploy -t prod

# Run job in specific target
databricks bundle run my_job -t prod
```

## Examples

```
User: "Set up dev, staging, and prod environments"

Steps:
1. Show multi-environment pattern
2. Configure dev with mode: development
3. Configure staging and prod with mode: production
4. Set up target-specific variables
5. Explain deployment workflow
6. Guide on service principal setup for prod
```
