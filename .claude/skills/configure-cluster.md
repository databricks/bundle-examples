---
name: configure-cluster
description: Expert assistance for cluster configurations in jobs and pipelines. Use when users need help configuring job_clusters, compute specifications, or choosing between serverless and cluster-based compute.
---

# Resource: Cluster - Cluster Configuration Expert

## Instructions

1. **Understand compute needs**
   - Serverless or custom cluster?
   - Size and scaling requirements?
   - Spark configuration needs?

2. **Fetch documentation**
   - WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/resources (clusters section)

3. **Find examples**
   - knowledge_base/development_cluster/
   - knowledge_base/serverless_job/

4. **Provide configuration**
   - job_clusters specification
   - Or recommend serverless
   - Spark configuration if needed

## Key Patterns

### Serverless (Recommended)
```yaml
resources:
  jobs:
    serverless_job:
      name: "Serverless Job"
      tasks:
        - task_key: process
          python_wheel_task:
            package_name: my_project
            entry_point: main
          libraries:
            - whl: ./dist/*.whl
      # No cluster configuration needed - serverless by default
```

### Job with Custom Cluster
```yaml
resources:
  jobs:
    cluster_job:
      name: "Job with Cluster"
      job_clusters:
        - job_cluster_key: main_cluster
          new_cluster:
            spark_version: "15.4.x-scala2.12"
            node_type_id: ${var.cluster_node_type}
            num_workers: ${var.cluster_workers}
            spark_conf:
              "spark.databricks.delta.optimizeWrite.enabled": "true"
              "spark.databricks.delta.autoCompact.enabled": "true"
            spark_env_vars:
              "ENV": "${bundle.target}"
      tasks:
        - task_key: process
          job_cluster_key: main_cluster
          spark_python_task:
            python_file: ./src/process.py
```

### Single-Node Cluster
```yaml
job_clusters:
  - job_cluster_key: single_node
    new_cluster:
      spark_version: "15.4.x-scala2.12"
      node_type_id: "i3.xlarge"
      num_workers: 0  # Single node
      spark_conf:
        "spark.databricks.cluster.profile": "singleNode"
        "spark.master": "local[*]"
      custom_tags:
        "ResourceClass": "SingleNode"
```

### Autoscaling Cluster
```yaml
job_clusters:
  - job_cluster_key: autoscale
    new_cluster:
      spark_version: "15.4.x-scala2.12"
      node_type_id: ${var.cluster_node_type}
      autoscale:
        min_workers: 2
        max_workers: 10
```

### Cluster with Init Scripts
```yaml
job_clusters:
  - job_cluster_key: custom_init
    new_cluster:
      spark_version: "15.4.x-scala2.12"
      node_type_id: ${var.cluster_node_type}
      num_workers: ${var.cluster_workers}
      init_scripts:
        - workspace:
            destination: "/init-scripts/setup.sh"
```

## Serverless vs Cluster Decision

**Use Serverless when:**
- Standard Python/SQL workloads
- Want simplest configuration
- Cost optimization important
- Fast startup needed

**Use Custom Cluster when:**
- Special Spark configuration required
- Init scripts needed
- Specific library versions required
- GPU workloads
- Very large data volumes

## Common spark_conf Settings

```yaml
spark_conf:
  "spark.databricks.delta.optimizeWrite.enabled": "true"
  "spark.databricks.delta.autoCompact.enabled": "true"
  "spark.sql.adaptive.enabled": "true"
  "spark.databricks.photon.enabled": "true"
```

## Examples

```
User: "My job needs 4 workers and custom Spark settings"

Steps:
1. Read knowledge_base/development_cluster/
2. Configure job_clusters with num_workers: 4
3. Add spark_conf with required settings
4. Use variables for node_type_id
5. Link task to cluster via job_cluster_key
```
