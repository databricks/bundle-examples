---
name: create-bundle
description: Guide users through creating new Databricks Asset Bundles from scratch. Use when the user wants to create a new bundle, initialize a DAB project, or needs help setting up bundle structure and configuration.
---

# Bundle Create - Databricks Asset Bundle Creation

## Instructions

When helping users create a Databricks Asset Bundle:

1. **Fetch latest documentation**
   - Use WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/
   - This ensures up-to-date bundle configuration guidance

2. **Understand project requirements**
   - Ask what type of project (Python ETL, SQL, DLT pipelines, MLOps, Apps)
   - Determine if they need YAML-based or Python-based resources
   - Identify environment needs (dev, staging, prod)

3. **Find relevant examples**
   - First try `Glob("**/databricks.yml")` to find local examples in current repo
   - If local examples exist, use Read to examine them
   - If no local examples, use WebFetch to get from official Databricks GitHub:
     - Simple: https://raw.githubusercontent.com/databricks/bundle-examples/main/default_minimal/databricks.yml
     - Python: https://raw.githubusercontent.com/databricks/bundle-examples/main/default_python/databricks.yml
     - Python resources: https://raw.githubusercontent.com/databricks/bundle-examples/main/pydabs/databricks.yml
     - SQL: https://raw.githubusercontent.com/databricks/bundle-examples/main/default_sql/databricks.yml
     - DLT Python: https://raw.githubusercontent.com/databricks/bundle-examples/main/lakeflow_pipelines_python/databricks.yml
     - MLOps: https://raw.githubusercontent.com/databricks/bundle-examples/main/mlops_stacks/databricks.yml
   - Always include inline templates as fallback

4. **Provide complete configuration**
   - Generate databricks.yml with:
     - bundle name and UUID
     - include paths for resources
     - variables section (if needed)
     - dev target with `mode: development`
     - prod target with `mode: production` and permissions
   - Explain directory structure to create
   - Guide on pyproject.toml if Python project

6. **Guide on next steps**
   - Run `databricks bundle validate` to check configuration
   - Create first resources (jobs, pipelines, etc.)
   - Deploy to dev: `databricks bundle deploy -t dev`

## Key Patterns

### Minimal Bundle
```yaml
bundle:
  name: my_bundle
  uuid: <generate-with-uuidgen>

include:
  - resources/*.yml

targets:
  dev:
    mode: development
    default: true
    workspace:
      host: https://workspace.databricks.com
```

### Standard Python Project
```yaml
bundle:
  name: my_project
  uuid: <uuid>

include:
  - resources/*.yml

artifacts:
  python_artifact:
    type: whl
    build: uv build --wheel

variables:
  catalog:
    description: "Unity Catalog catalog"
  schema:
    description: "Schema for tables"

targets:
  dev:
    mode: development
    default: true
    workspace:
      host: https://workspace.databricks.com
    variables:
      catalog: dev
      schema: ${workspace.current_user.short_name}

  prod:
    mode: production
    workspace:
      host: https://workspace.databricks.com
    variables:
      catalog: prod
      schema: prod
    permissions:
      - user_name: user@company.com
        level: CAN_MANAGE
```

### Python-Based Resources (pydabs)
```yaml
bundle:
  name: my_bundle

python:
  venv_path: .venv
  resources:
    - "resources:load_resources"

targets:
  dev:
    mode: development
    default: true
```

### Directory Structure
```
my_project/
├── databricks.yml      # Main configuration
├── resources/          # Resource definitions
│   ├── *.job.yml
│   └── *.pipeline.yml
├── src/                # Source code
│   ├── my_project/     # Python package
│   └── notebooks/      # Notebooks
├── tests/              # Tests
├── pyproject.toml      # Python dependencies
└── README.md
```

## Decision Guide

**Project Type Selection:**
| Type | Use Example | Key Feature |
|------|-------------|-------------|
| Simple | default_minimal | Minimal config |
| Python ETL | default_python | Jobs + pipelines + wheel |
| SQL | default_sql | SQL queries & dashboards |
| DLT Python | lakeflow_pipelines_python | Delta Live Tables |
| DLT SQL | lakeflow_pipelines_sql | SQL pipelines |
| MLOps | mlops_stacks | Full ML lifecycle |
| Python Resources | pydabs | Code-defined resources |

**YAML vs Python Resources:**
- YAML: Standard approach, declarative, use for most projects
- Python (pydabs): When you need dynamic resource generation or complex logic

## Related Skills

Suggest these skills after bundle creation:
- `resource-job` - To add job resources
- `resource-pipeline` - To add pipeline resources
- `deployment-modes` - For target configuration
- `variables-references` - For variable setup
- `artifacts-dependencies` - For Python wheel configuration
- `bundle-validate` - To validate configuration

## Examples

### Example 1: Creating a Simple Python ETL Bundle
```
User: "I want to create a new bundle for Python ETL jobs"

Steps:
1. Fetch https://docs.databricks.com/aws/en/dev-tools/bundles/
2. Read default_python/databricks.yml
3. Generate configuration based on pattern
4. Explain directory structure
5. Guide on creating first job resource
```

### Example 2: Creating a DLT Pipeline Bundle
```
User: "Help me set up a bundle for Delta Live Tables pipelines"

Steps:
1. Fetch bundle documentation
2. Read lakeflow_pipelines_python/databricks.yml
3. Show configuration for DLT
4. Explain pipeline resource structure
5. Guide on catalog/schema variables
```

## CLI Commands

- `databricks bundle init` - Initialize from template
- `databricks bundle validate` - Validate configuration
- `databricks bundle deploy` - Deploy bundle
- `databricks bundle deploy -t prod` - Deploy to production
