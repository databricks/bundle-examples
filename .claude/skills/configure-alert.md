---
name: configure-alert
description: Expert assistance for Alert resources. Use when users want to create SQL alerts, configure thresholds, set up monitoring, or configure alert notifications.
---

# Resource: Alert - SQL Alert Configuration

## Instructions

1. **Understand alert needs**
   - What metric to monitor?
   - Threshold values?
   - Notification requirements?

2. **Fetch documentation**
   - WebFetch: https://docs.databricks.com/aws/en/dev-tools/bundles/resources (alerts section)

3. **Find example**
   - knowledge_base/alerts/

4. **Provide configuration**
   - Alert resource with query
   - Evaluation criteria
   - Schedule configuration

## Key Patterns

### Basic Alert
```yaml
resources:
  alerts:
    revenue_alert:
      name: "Daily Revenue Alert"
      query_text: |
        SELECT SUM(revenue) as total_revenue
        FROM ${var.catalog}.${var.schema}.sales
        WHERE date = current_date()
      warehouse_id: ${var.warehouse_id}
      evaluation:
        comparison: GREATER_THAN
        threshold_value: 100000
        source: MAX  # MAX, MIN, AVG, SUM
      schedule:
        quartz_cron_schedule: "0 0 8 * * ?"
        timezone_id: "UTC"
```

### Alert with Retrigger
```yaml
resources:
  alerts:
    error_alert:
      name: "Error Rate Alert"
      query_text: |
        SELECT COUNT(*) as error_count
        FROM ${var.catalog}.${var.schema}.logs
        WHERE level = 'ERROR'
        AND timestamp > current_timestamp() - INTERVAL 1 HOUR
      warehouse_id: ${var.warehouse_id}
      evaluation:
        comparison: GREATER_THAN
        threshold_value: 10
      schedule:
        quartz_cron_schedule: "0 */15 * * * ?"  # Every 15 minutes
        timezone_id: "UTC"
      retrigger_interval_seconds: 3600  # Don't retrigger within 1 hour
```

### Alert with File Query
```yaml
resources:
  alerts:
    performance_alert:
      name: "Performance Alert"
      query_file: ./src/queries/performance_check.sql
      warehouse_id: ${var.warehouse_id}
      evaluation:
        comparison: LESS_THAN
        threshold_value: 95  # Alert if < 95%
        source: MIN
      schedule:
        quartz_cron_schedule: "0 0 * * * ?"
```

## Comparison Operators

- `GREATER_THAN`
- `GREATER_THAN_OR_EQUAL`
- `LESS_THAN`
- `LESS_THAN_OR_EQUAL`
- `EQUAL`
- `NOT_EQUAL`

## Source Aggregations

- `MAX` - Maximum value
- `MIN` - Minimum value
- `AVG` - Average value
- `SUM` - Sum of values

## Examples

```
User: "Create an alert when daily sales drop below threshold"

Steps:
1. Read knowledge_base/alerts/ example
2. Create alert with query_text
3. Configure LESS_THAN comparison
4. Set up daily schedule
5. Add notification configuration
```
