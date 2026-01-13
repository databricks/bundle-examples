---
name: configure-job
description: Expert assistance for configuring Databricks Job resources in bundles. Use when users want to create/modify jobs, configure tasks, set up schedules, or work with job orchestration.
---

# Resource: Job - Job Configuration Expert

## Instructions

When helping users with job resources:

1. **Understand requirements**
   - Determine task types needed (notebook, Python wheel, SQL, dbt, pipeline, etc.)
   - Identify dependencies between tasks
   - Check if schedule/trigger needed
   - Determine compute needs (serverless vs cluster)

2. **Fetch documentation**
   - Use WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/job-task-types
   - This covers all task types and configurations

3. **Find relevant examples**
   - Use Glob to find job examples: `Glob("**/*.job.yml")`
   - Key examples:
     - default_python/resources/sample_job.job.yml - Comprehensive
     - knowledge_base/serverless_job/ - Serverless pattern
     - knowledge_base/job_with_multiple_wheels/ - Multiple libraries
     - knowledge_base/job_with_run_job_tasks/ - Job orchestration
     - pydabs/resources/sample_job.py - Python-defined

4. **Read examples**
   - Use Read to examine 2-3 relevant job files
   - Show patterns matching user's needs

5. **Provide configuration**
   - Generate complete job YAML or Python code
   - Include task dependencies if multi-task
   - Configure schedule if needed
   - Set up notifications

## Key Patterns

### Basic Serverless Job
```yaml
resources:
  jobs:
    my_job:
      name: "ETL Job"
      tasks:
        - task_key: process
          python_wheel_task:
            package_name: my_project
            entry_point: main
          libraries:
            - whl: ./dist/*.whl
```

### Multi-Task with Dependencies
```yaml
resources:
  jobs:
    pipeline_job:
      name: "Data Pipeline"
      tasks:
        - task_key: extract
          notebook_task:
            notebook_path: ./src/notebooks/extract.py

        - task_key: transform
          depends_on:
            - task_key: extract
          python_wheel_task:
            package_name: my_project
            entry_point: transform
          libraries:
            - whl: ./dist/*.whl

        - task_key: load
          depends_on:
            - task_key: transform
          spark_python_task:
            python_file: ./src/load.py
```

### Job with Schedule
```yaml
resources:
  jobs:
    daily_job:
      name: "Daily ETL"
      schedule:
        quartz_cron_expression: "0 0 2 * * ?"  # 2 AM daily
        timezone_id: "America/Los_Angeles"
        pause_status: UNPAUSED
      email_notifications:
        on_failure:
          - team@company.com
      tasks:
        - task_key: run
          python_wheel_task:
            package_name: my_project
            entry_point: main
          libraries:
            - whl: ./dist/*.whl
```

### Pipeline Refresh Task
```yaml
resources:
  jobs:
    orchestrator:
      name: "Pipeline Orchestrator"
      tasks:
        - task_key: refresh_pipeline
          pipeline_task:
            pipeline_id: ${resources.pipelines.my_pipeline.id}
```

### SQL Task
```yaml
resources:
  jobs:
    sql_job:
      name: "SQL Job"
      tasks:
        - task_key: query
          sql_task:
            warehouse_id: ${var.warehouse_id}
            file:
              path: ./src/queries/report.sql
```

### dbt Task
```yaml
resources:
  jobs:
    dbt_job:
      name: "dbt Transformation"
      tasks:
        - task_key: dbt_run
          dbt_task:
            project_directory: dbt_project
            commands:
              - "dbt run"
              - "dbt test"
            warehouse_id: ${var.warehouse_id}
```

### Job with Custom Cluster
```yaml
resources:
  jobs:
    cluster_job:
      name: "Job with Cluster"
      job_clusters:
        - job_cluster_key: main
          new_cluster:
            spark_version: "15.4.x-scala2.12"
            node_type_id: ${var.cluster_node_type}
            num_workers: ${var.cluster_workers}
      tasks:
        - task_key: process
          job_cluster_key: main
          spark_python_task:
            python_file: ./src/process.py
```

## Task Types Quick Reference

| Task Type | Use When | Example |
|-----------|----------|---------|
| `notebook_task` | Running notebooks | Exploratory work, parameterized notebooks |
| `python_wheel_task` | Running packaged Python | Production Python code |
| `spark_python_task` | Running Python files | Simple scripts without packaging |
| `sql_task` | Running SQL queries | SQL analytics |
| `dbt_task` | Running dbt | dbt transformations |
| `pipeline_task` | Triggering DLT | Refreshing pipelines |
| `run_job_task` | Orchestrating jobs | Master orchestrator pattern |

## Common Issues

- **Missing libraries**: Add to libraries section
- **Task dependency cycle**: Check depends_on doesn't create loop
- **Schedule not running**: Verify pause_status: UNPAUSED and production mode
- **Serverless not available**: Some tasks require clusters (check docs)
- **Permission errors**: Add permissions in prod target

## Related Skills

- `resource-pipeline` - For pipeline_task configuration
- `resource-cluster` - For job_clusters setup
- `artifacts-dependencies` - For library management
- `permissions-security` - For job permissions
- `variables-references` - For parameterization

## Examples

### Example 1: Simple Python Job
```
User: "Create a job that runs my Python wheel daily at 2 AM"

Steps:
1. Read default_python/resources/sample_job.job.yml
2. Generate job with:
   - python_wheel_task
   - schedule with quartz_cron_expression
   - email_notifications
3. Explain how to reference wheel artifact
```

### Example 2: Multi-Stage Pipeline
```
User: "Job with extract, transform, load tasks in sequence"

Steps:
1. Show multi-task pattern with depends_on
2. Configure each task appropriate type
3. Set up task dependencies
4. Add error notifications
```

## CLI Commands

- `databricks bundle validate` - Validate job config
- `databricks bundle deploy` - Deploy job
- `databricks bundle run my_job` - Run job manually
