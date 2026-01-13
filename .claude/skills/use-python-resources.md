---
name: use-python-resources
description: Expert assistance for Python-based resource definitions using databricks-bundles library (pydabs pattern). Use when users want to define resources in Python code instead of YAML for dynamic configuration.
---

# Python Resources - Python-Based Bundle Configuration

## Instructions

1. **Understand use case**
   - Why Python over YAML? (dynamic generation, logic, etc.)
   - What resources need to be defined?

2. **Fetch documentation**
   - WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/python/

3. **Find example**
   - pydabs/ - Complete Python resources example

4. **Provide configuration**
   - databricks.yml with python.resources
   - resources/__init__.py structure
   - Python resource definitions

## Key Patterns

### databricks.yml Configuration
```yaml
bundle:
  name: my_python_bundle

python:
  venv_path: .venv
  resources:
    - "resources:load_resources"

targets:
  dev:
    mode: development
    default: true
```

### resources/__init__.py
```python
from databricks.bundles.resources import Resources
from .sample_job import sample_job
from .sample_pipeline import sample_pipeline

def load_resources() -> Resources:
    return Resources(
        jobs={
            "sample_job": sample_job,
        },
        pipelines={
            "sample_pipeline": sample_pipeline,
        }
    )
```

### resources/sample_job.py
```python
from databricks.bundles.jobs import Job

sample_job = Job.from_dict({
    "name": "Sample Job",
    "tasks": [
        {
            "task_key": "process",
            "python_wheel_task": {
                "package_name": "my_project",
                "entry_point": "main"
            },
            "libraries": [{"whl": "./dist/*.whl"}]
        }
    ],
    "schedule": {
        "quartz_cron_expression": "0 0 * * * ?",
        "timezone_id": "UTC"
    }
})
```

### Mixing YAML and Python
```yaml
bundle:
  name: hybrid_bundle

include:
  - resources/*.yml  # YAML resources

python:
  venv_path: .venv
  resources:
    - "resources:load_resources"  # Python resources
```

## When to Use Python Resources

**Use Python when:**
- Need dynamic resource generation based on logic
- Conditional resource creation
- Complex configuration with loops/conditions
- Team prefers code over config
- Building resource generation tools

**Use YAML when:**
- Standard static configurations
- Simpler, more declarative approach
- Team prefers config files
- Most cases (YAML is the default)

## Setup Requirements

```toml
# pyproject.toml
[dependency-groups]
dev = [
    "databricks-bundles>=0.279.0",
]
```

Install and create venv:
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Examples

```
User: "I need to generate 10 similar jobs programmatically"

Steps:
1. Read pydabs/ example structure
2. Set up python.resources in databricks.yml
3. Create resources/__init__.py
4. Show loop to generate jobs in Python
5. Explain load_resources() pattern
```
