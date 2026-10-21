# Job notifications and health

## What this example shows

This example defines a serverless job with email notifications, webhook notifications, health rules, timeouts, and retries.

The Python task can sleep or fail. Use its job parameters to test notifications.

The `dev` target overrides all recipient lists with empty lists. The `prod` target adds the configured recipients.

## Prerequisites

- Install Databricks CLI 0.218.0 or later.
- Configure a Databricks CLI profile for the target workspace.
- Use a workspace that supports serverless jobs environment version `4`.
- Create a webhook notification destination in the workspace.
- Use an email address for an active workspace user.

## Configure

Set variables with `--var`, environment variables, or a target variable file.

| Variable | Required value | Example placeholder |
| --- | --- | --- |
| `notification_email` | An address that receives job email notifications | `replace-me@example.com` |
| `notification_destination_id` | The UUID of a workspace notification destination | `00000000-0000-0000-0000-000000000000` |

Do not put webhook credentials in this bundle. Store credentials in the workspace notification destination.

## Deploy and run

1. Validate the development target.

   ```bash
   databricks bundle validate -t dev
   ```

2. Deploy the development target.

   ```bash
   databricks bundle deploy -t dev
   ```

3. Run the development job without notifications.

   ```bash
   databricks bundle run -t dev notification_health_job
   ```

4. Validate the production target with production variable values.

   ```bash
   databricks bundle validate -t prod --var="notification_email=USER@example.com,notification_destination_id=DESTINATION_UUID"
   ```

5. Deploy the production target with the same values.

   ```bash
   databricks bundle deploy -t prod --var="notification_email=USER@example.com,notification_destination_id=DESTINATION_UUID"
   ```

6. Run the production job.

   ```bash
   databricks bundle run -t prod notification_health_job
   ```

## How notifications and health rules work

| Key | What it does | Dev value | Prod value |
| --- | --- | --- | --- |
| `email_notifications.on_failure` | Sends email after the final failed or timed-out run | Empty | `notification_email` |
| `email_notifications.on_duration_warning_threshold_exceeded` | Sends email when run duration exceeds 60 seconds | Empty | `notification_email` |
| `email_notifications.on_streaming_backlog_exceeded` | Sends email when a streaming backlog rule is exceeded | Empty | `notification_email` |
| `webhook_notifications.on_failure` | Calls the destination after the final failed or timed-out run | Empty | `notification_destination_id` |
| `webhook_notifications.on_duration_warning_threshold_exceeded` | Calls the destination when run duration exceeds 60 seconds | Empty | `notification_destination_id` |
| `webhook_notifications.on_streaming_backlog_exceeded` | Calls the destination when a streaming backlog rule is exceeded | Empty | `notification_destination_id` |
| `notification_settings.no_alert_for_skipped_runs` | Suppresses failure notifications for skipped runs | `true` | `true` |
| `notification_settings.no_alert_for_canceled_runs` | Suppresses failure notifications for canceled runs | `true` | `true` |
| `health.rules[0]` | Warns when `RUN_DURATION_SECONDS` is greater than 60 | 60 seconds | 60 seconds |
| `health.rules[1]` | Warns when `STREAMING_BACKLOG_RECORDS` is greater than 1,000 | 1,000 records | 1,000 records |
| `timeout_seconds` | Stops each task attempt after 120 seconds | 120 seconds | 120 seconds |
| `max_retries` | Retries one failed task attempt | 1 | 1 |
| `min_retry_interval_millis` | Waits at least 10 seconds before retrying | 10,000 ms | 10,000 ms |
| `retry_on_timeout` | Retries an attempt after a timeout | `true` | `true` |

## Test the alerts

Use the `prod` target for notification tests. The `dev` target suppresses all recipients.

### Force a duration warning

1. Run the task for more than 60 seconds.

   ```bash
   databricks bundle run -t prod notification_health_job --params sleep_seconds=90,fail=false
   ```

2. Check for a duration warning email and webhook call.

The notification identifies the job, run, workspace, and duration threshold event.

### Force a timeout

1. Run the task for more than 120 seconds.

   ```bash
   databricks bundle run -t prod notification_health_job --params sleep_seconds=180,fail=false
   ```

2. Wait for the retry and the final run result.

The task times out twice because `retry_on_timeout` is `true`. The final failure notification follows the last attempt.

### Force a failure

1. Request an intentional failure.

   ```bash
   databricks bundle run -t prod notification_health_job --params sleep_seconds=0,fail=true
   ```

2. Wait for the retry and the final run result.

The task fails twice because `max_retries` is `1`. The email and webhook report the final failed run.

Webhook payload fields can change by event type and workspace version. A representative payload has this form:

```json
{
  "event_type": "jobs.on_failure",
  "workspace_id": "WORKSPACE_ID",
  "run": {
    "run_id": "RUN_ID",
    "name": "Job notifications and health",
    "state": "FAILED",
    "url": "RUN_URL"
  }
}
```

## Edge cases and limits

- This example uses serverless compute. It does not configure classic job clusters.
- Serverless availability and environment versions can differ across AWS, Azure, GCP, and regions.
- This example uses no storage URI, node type, or cloud identity.
- Retries start only after an attempt fails or times out.
- Each retry receives a new 120-second timeout.
- Failure notifications occur after retries finish.
- Duration warnings can occur before a later timeout or failure.
- The streaming backlog rule is Public Preview and has no effect on this batch task.
- Use the rule with a streaming task to test streaming backlog notifications.
- Skipped and canceled runs do not send failure notifications in either target.
- Deployment is idempotent. You can safely repeat an interrupted deployment.
- Destruction removes only resources that this bundle owns.

## Clean up

1. Remove development resources.

   ```bash
   databricks bundle destroy -t dev
   ```

2. Remove production resources.

   ```bash
   databricks bundle destroy -t prod --var="notification_email=USER@example.com,notification_destination_id=DESTINATION_UUID"
   ```
