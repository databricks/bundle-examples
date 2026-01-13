---
name: configure-ml-resources
description: Expert assistance for ML resources (registered models, experiments). Use when users want to configure MLflow models, experiments, or set up ML workflows in bundles.
---

# Resource: ML - ML Resources Configuration

## Instructions

1. **Understand ML needs**
   - Model registration?
   - Experiment tracking?
   - Unity Catalog integration?

2. **Fetch documentation**
   - WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/resources (ML resources)

3. **Find example**
   - mlops_stacks/

4. **Provide configuration**
   - registered_models resource
   - experiments resource
   - Unity Catalog integration

## Key Patterns

### Registered Model (Unity Catalog)
```yaml
resources:
  registered_models:
    my_model:
      name: ${var.catalog}.${var.schema}.my_model
      catalog_name: ${var.catalog}
      schema_name: ${var.schema}
      comment: "Production ML model"
      grants:
        - principal: account users
          privileges:
            - EXECUTE
```

### Experiment
```yaml
resources:
  experiments:
    my_experiment:
      name: /Users/${workspace.current_user.userName}/experiments/my_model
      description: "Model training experiments"
```

### Model with Grants
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

## Examples

```
User: "Create resources for ML model deployment"

Steps:
1. Read mlops_stacks/ example
2. Create registered_model resource
3. Configure Unity Catalog integration
4. Set up grants for model access
```
