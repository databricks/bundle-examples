# Job notifications and health

This Declarative Automation Bundles example defines a serverless job with notifications, health rules, timeouts, and retries.

The Python task can sleep or fail. Use its job parameters to test alerts.

For configuration details, see the [job notifications documentation](https://docs.databricks.com/aws/en/jobs/notifications).

## Prerequisites

- Databricks CLI v1.20.0 or above
- Configure a Databricks CLI profile for the target workspace.
- Use a workspace that supports serverless jobs environment version `4`.
- Create a webhook notification destination in the workspace.
- Use an email address that can receive notifications.

## Usage

1. Set the notification variables.

   Replace both placeholder values with real production values.

   ```bash
   export BUNDLE_VAR_notification_email=USER@example.com
   export BUNDLE_VAR_notification_destination_id=DESTINATION_UUID
   ```

2. Deploy the development target without notifications.

   ```bash
   databricks bundle deploy -t dev
   ```

3. Deploy and run the production target.

   ```bash
   databricks bundle deploy -t prod
   databricks bundle run -t prod notification_health_job
   ```

4. Test a duration alert by running the task for 90 seconds.

   ```bash
   databricks bundle run -t prod notification_health_job --params sleep_seconds=90,fail=false
   ```

5. Remove the deployed resources after testing.

   ```bash
   databricks bundle destroy -t dev
   databricks bundle destroy -t prod
   ```

## Notes

- The base job has empty recipient lists. Target lists add to base lists and do not replace them.
- The `prod` target adds `notification_email` and `notification_destination_id` recipients.
- `max_retries: 1` starts one retry after a failed attempt. The final failure notification follows that retry.
- The streaming backlog rule needs a streaming task and is Public Preview.
- The bundle deploys under `/Workspace/bundle-examples`. Secure that folder, or change `root_path`.
