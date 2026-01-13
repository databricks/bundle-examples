---
name: configure-dashboard
description: Expert assistance for AI/BI Dashboard resources. Use when users want to deploy dashboards, configure dashboard snapshots, or integrate dashboards with jobs.
---

# Resource: Dashboard - AI/BI Dashboard Configuration

## Instructions

1. **Understand dashboard needs**
   - Existing dashboard or new?
   - Warehouse requirements
   - Snapshot needs?

2. **Fetch documentation**
   - WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/resources (dashboards section)

3. **Find example**
   - knowledge_base/dashboard_nyc_taxi/

4. **Provide configuration**
   - Dashboard resource YAML
   - file_path to .lvdash.json
   - Warehouse ID reference

## Key Patterns

### Basic Dashboard
```yaml
resources:
  dashboards:
    my_dashboard:
      name: "Analytics Dashboard"
      file_path: ./dashboards/analytics.lvdash.json
      warehouse_id: ${var.warehouse_id}
```

### Dashboard with Snapshots in Job
```yaml
resources:
  dashboards:
    report_dashboard:
      name: "Daily Report"
      file_path: ./dashboards/report.lvdash.json
      warehouse_id: ${var.warehouse_id}

  jobs:
    snapshot_job:
      name: "Dashboard Snapshot Job"
      schedule:
        quartz_cron_expression: "0 0 6 * * ?"
      tasks:
        - task_key: create_snapshot
          dashboard_task:
            dashboard_id: ${resources.dashboards.report_dashboard.id}
            warehouse_id: ${var.warehouse_id}
```

### Dashboard with embed_credentials
```yaml
resources:
  dashboards:
    embedded_dashboard:
      name: "Embedded Dashboard"
      file_path: ./dashboards/embed.lvdash.json
      warehouse_id: ${var.warehouse_id}
      embed_credentials: true
```

## Commands

Generate dashboard file:
```
databricks bundle generate dashboard --resource my_dashboard
```

## Examples

```
User: "Deploy a dashboard that snapshots daily"

Steps:
1. Read knowledge_base/dashboard_nyc_taxi/
2. Create dashboard resource
3. Add job with dashboard_task for snapshots
4. Explain .lvdash.json file generation
```
