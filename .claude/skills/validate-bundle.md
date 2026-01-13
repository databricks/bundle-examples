---
name: validate-bundle
description: Validate bundle configurations and troubleshoot errors. Use when users encounter validation errors, deployment failures, or want to check bundle health before deploying.
---

# Bundle Validate - Configuration Validation & Troubleshooting

## Instructions

When helping users validate or troubleshoot bundles:

1. **Understand the issue**
   - Ask user to share error message or describe the problem
   - Determine what they were trying to do when error occurred

2. **Fetch troubleshooting documentation**
   - Use WebFetch to get: https://docs.databricks.com/aws/en/dev-tools/bundles/faqs
   - This has common issues and solutions

3. **Read their configuration**
   - Use Read to examine their databricks.yml
   - Read any resource files mentioned in errors
   - Look for syntax issues, typos, missing fields

4. **Search for working patterns**
   - Use Grep to find correct syntax in repository examples
   - Compare their config against working examples

5. **Diagnose and fix**
   - Identify root cause (syntax, references, paths, permissions, etc.)
   - Provide specific fix with corrected code
   - Explain what was wrong and why

6. **Validate solution**
   - Guide user to run `databricks bundle validate`
   - Test incrementally if complex issue

## Common Error Patterns

### Variable Reference Errors
```
Error: variable "catalog" is not defined

Fix: Add to variables section:
variables:
  catalog:
    description: "Catalog to use"

And set value in target:
targets:
  dev:
    variables:
      catalog: dev_catalog
```

### Resource Not Found
```
Error: resource "jobs/my_job" is not defined

Fixes:
1. Check include path covers resource location
2. Verify file name: <name>.job.yml
3. Check resource defined correctly:
   resources:
     jobs:
       my_job:  # This name must match reference
```

### Invalid Interpolation Syntax
```
Correct: ${var.catalog}
Wrong: {var.catalog}
Wrong: $var.catalog
Wrong: var.catalog
```

### Circular Dependencies
```
Error: circular dependency detected

Fix: Map dependencies, break cycle
- Job A depends on Job B
- Job B depends on Job A
→ Remove one dependency
```

### Permission Denied
```
Error: permission denied

Fix for prod:
targets:
  prod:
    mode: production
    permissions:
      - user_name: deployer@company.com
        level: CAN_MANAGE
```

### Missing Workspace Host
```
Error: workspace host required

Fix:
targets:
  dev:
    workspace:
      host: https://workspace.databricks.com
```

## Validation Checklist

Guide users through:
- [ ] YAML syntax valid (no tabs, proper indentation)
- [ ] bundle.name and UUID present
- [ ] All targets have workspace.host
- [ ] Variables declared before use
- [ ] Variable syntax correct: ${var.name}
- [ ] Resource references correct: ${resources.jobs.name.id}
- [ ] Include paths relative to databricks.yml
- [ ] One target has default: true
- [ ] Dev target uses mode: development
- [ ] Prod target uses mode: production with permissions
- [ ] No circular dependencies
- [ ] Permission levels valid (CAN_MANAGE, CAN_VIEW, CAN_RUN)

## Interpolation Reference

**Correct syntax:**
- `${var.catalog}` - User variable
- `${bundle.name}` - Bundle name
- `${bundle.target}` - Current target
- `${workspace.current_user.short_name}` - Username
- `${resources.jobs.my_job.id}` - Job reference
- `${resources.pipelines.my_pipeline.id}` - Pipeline reference

## Related Skills

- `bundle-create` - If structure is fundamentally wrong
- `variables-references` - For variable issues
- `deployment-modes` - For target configuration
- `permissions-security` - For permission errors
- Resource skills - For specific resource configuration issues

## Examples

### Example 1: Variable Not Found
```
User: "Getting error: variable 'schema' not defined"

Steps:
1. Read their databricks.yml
2. Check variables section
3. Add missing variable:
   variables:
     schema:
       description: "Schema name"
4. Set in target:
   targets:
     dev:
       variables:
         schema: ${workspace.current_user.short_name}
```

### Example 2: Resource Reference Typo
```
User: "Pipeline task failing - resource not found"

Steps:
1. Read job file with pipeline_task
2. Find the typo: ${resources.pipelines.my_pipline.id}
3. Correct: ${resources.pipelines.my_pipeline.id}
4. Verify pipeline resource exists
```

## CLI Commands

- `databricks bundle validate` - Validate configuration
- `databricks bundle validate -t dev` - Validate specific target
- `databricks bundle deploy --dry-run` - Preview deployment
- `databricks bundle summary` - Show deployed resources
