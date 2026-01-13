# Databricks Asset Bundle Examples Reference

This document provides GitHub URLs for fetching bundle examples when the skills are used outside the bundle-examples repository.

## Base GitHub Repository
https://github.com/databricks/bundle-examples

## Core Bundle Examples

### Minimal Bundle
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/default_minimal/databricks.yml
- **Use for**: Simplest bundle structure, getting started

### Standard Python Project
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/default_python/databricks.yml
- **Job example**: https://raw.githubusercontent.com/databricks/bundle-examples/main/default_python/resources/sample_job.job.yml
- **Pipeline example**: https://raw.githubusercontent.com/databricks/bundle-examples/main/default_python/resources/default_python_etl.pipeline.yml
- **pyproject.toml**: https://raw.githubusercontent.com/databricks/bundle-examples/main/default_python/pyproject.toml
- **Use for**: Python projects with jobs and pipelines

### Python-Based Resources (pydabs)
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/pydabs/databricks.yml
- **resources/__init__.py**: https://raw.githubusercontent.com/databricks/bundle-examples/main/pydabs/resources/__init__.py
- **Job example**: https://raw.githubusercontent.com/databricks/bundle-examples/main/pydabs/resources/sample_job.py
- **Use for**: Python-defined resources, dynamic generation

### SQL Project
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/default_sql/databricks.yml
- **Use for**: SQL-focused analytics projects

### DLT Python Pipelines
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/lakeflow_pipelines_python/databricks.yml
- **Use for**: Delta Live Tables with Python

### DLT SQL Pipelines
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/lakeflow_pipelines_sql/databricks.yml
- **Use for**: Delta Live Tables with SQL

### MLOps Stack
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/mlops_stacks/databricks.yml
- **ML resources**: https://raw.githubusercontent.com/databricks/bundle-examples/main/mlops_stacks/mlops_stacks/resources/ml-artifacts-resource.yml
- **Use for**: Full ML lifecycle workflows

## Knowledge Base Examples

### Serverless Job
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/serverless_job/databricks.yml
- **Use for**: Serverless compute patterns

### Job with Multiple Wheels
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/job_with_multiple_wheels/databricks.yml
- **Use for**: Multiple library dependencies

### Job with Run Job Tasks
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/job_with_run_job_tasks/databricks.yml
- **Use for**: Job orchestration patterns

### Job with SQL Notebook
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/job_with_sql_notebook/databricks.yml
- **Use for**: SQL notebook tasks

### Job Read Secret
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/job_read_secret/databricks.yml
- **Use for**: Secret management patterns

### Pipeline with Schema
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/pipeline_with_schema/databricks.yml
- **Use for**: Pipelines with Unity Catalog integration

### Development Cluster
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/development_cluster/databricks.yml
- **Use for**: Custom cluster configurations

### Alerts
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/alerts/databricks.yml
- **Alert example**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/alerts/resources/nyc_taxi_daily_revenue.alert.yml
- **Use for**: SQL alert configurations

### Databricks App
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/databricks_app/databricks.yml
- **Use for**: App deployment

### App with Database
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/app_with_database/databricks.yml
- **App resource**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/app_with_database/resources/myapp.app.yml
- **Use for**: Apps with database connections

### Dashboard
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/dashboard_nyc_taxi/databricks.yml
- **Dashboard resource**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/dashboard_nyc_taxi/resources/nyc_taxi_trip_analysis.dashboard.yml
- **Use for**: AI/BI Dashboard deployment

### Database with Catalog
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/database_with_catalog/databricks.yml
- **Use for**: Database instances and catalogs

### Write from Job to Volume
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/write_from_job_to_volume/databricks.yml
- **Schema**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/write_from_job_to_volume/resources/hello_world.schema.yml
- **Volume**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/write_from_job_to_volume/resources/my_volume.volume.yml
- **Use for**: Volume management patterns

### Share Files Across Bundles
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/share_files_across_bundles/databricks.yml
- **Use for**: Code sharing patterns

### Target Includes
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/target_includes/databricks.yml
- **Use for**: Environment-specific resource inclusion

### Private Wheel Packages
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/private_wheel_packages/databricks.yml
- **Use for**: Private package repositories

### Python Wheel with Poetry
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/python_wheel_poetry/databricks.yml
- **Use for**: Poetry-based wheel building

### Spark JAR Task
- **URL**: https://raw.githubusercontent.com/databricks/bundle-examples/main/knowledge_base/spark_jar_task/databricks.yml
- **Use for**: JAR artifacts and Scala/Java jobs

## Usage Pattern in Skills

Skills follow a three-tier approach for maximum portability:

### Tier 1: Try Local Files First
```
Use Glob to search: Glob("**/databricks.yml") or Glob("**/*.job.yml")
If found, use Read to examine local examples
```

### Tier 2: Fetch from GitHub
```
If no local files, use WebFetch with URLs from this document
Example: WebFetch(url="https://raw.githubusercontent.com/databricks/bundle-examples/main/default_python/databricks.yml",
                   prompt="Extract the configuration pattern")
```

### Tier 3: Use Inline Templates
```
All skills contain comprehensive inline YAML/Python templates
Works even without local files or network access
```

## Example Usage in Skill

```markdown
## Instructions

1. **Try local examples first**
   - Use `Glob("**/*.job.yml")` to find local job files
   - If found, use Read to examine them

2. **Fetch from GitHub if needed**
   - Use WebFetch with URL: https://raw.githubusercontent.com/databricks/bundle-examples/main/default_python/resources/sample_job.job.yml
   - Extract relevant patterns for user's needs

3. **Provide inline templates**
   - Show comprehensive example from skill templates
   - Customize based on user requirements
```

This three-tier approach ensures skills work everywhere:
- ✅ In the bundle-examples repo (local files)
- ✅ In any other repo (GitHub fetch)
- ✅ Offline (inline templates)
