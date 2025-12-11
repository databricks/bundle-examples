# SQL Alerts with Databricks Asset Bundles

This example shows how to define SQL alerts using Databricks Asset Bundles. The alert monitors daily NYC Taxi revenue and triggers when it exceeds a threshold.

For more information about SQL alerts, see the [Databricks documentation](https://docs.databricks.com/aws/en/sql/user/alerts/).

## Usage

1. Modify `databricks.yml`:
   - Update the `host` field to your Databricks workspace URL
   - Update the `warehouse` field to the name of your SQL warehouse

2. Modify `resources/nyc_taxi_daily_revenue.alert.yml`:
   - Update the `user_name` field under `permissions` to your email address

3. Deploy the alert:
   ```sh
   databricks bundle deploy
   ```

## Key Configuration

The alert configuration in `resources/nyc_taxi_daily_revenue.alert.yml` includes:

- **query_text**: SQL query that returns the metric to monitor
- **evaluation**: Defines how to evaluate the query results
  - `comparison_operator`: GREATER_THAN, LESS_THAN, EQUAL, etc.
  - `source.aggregation`: MAX, MIN, AVG, or SUM
  - `threshold.value`: The value to compare against
- **schedule**: Uses Quartz cron syntax (e.g., `"0 0 8 * * ?"` for daily at 8 AM)
- **warehouse_id**: The SQL warehouse to execute the query
