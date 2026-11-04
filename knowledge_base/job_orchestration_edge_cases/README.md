# Job orchestration edge cases

This Declarative Automation Bundles example defines a serverless job with `run_if` conditions, task retries, run queueing, and `for_each` tasks.

One `for_each` iteration fails on purpose, so the run ends in a controlled partial failure.

For configuration details, see the [run if documentation](https://docs.databricks.com/aws/en/jobs/run-if).

## Prerequisites

- Databricks CLI v1.20.0 or above
- Configure a Databricks CLI profile for the target workspace.
- Use a workspace that supports serverless jobs environment version `6`.

## Usage

1. Deploy the job. The deploy stops if the job has an active run.

   ```bash
   databricks bundle deploy --fail-on-active-runs
   ```

2. Run the job.

   ```bash
   databricks bundle run orchestration_edge_cases
   ```

3. Examine the run result. The command fails because the run result is `FAILED`. The tasks have these results:

   | Task | `run_if` | Result |
   | --- | --- | --- |
   | `process_items` | `ALL_SUCCESS` | `FAILED`: item `beta` fails twice, with one retry |
   | `process_no_items` | `ALL_SUCCESS` | `SUCCESS`: zero iterations |
   | `publish` | `ALL_SUCCESS` | `UPSTREAM_FAILED` |
   | `cleanup` | `ALL_DONE` | `SUCCESS` |
   | `alert_on_failure` | `AT_LEAST_ONE_FAILED` | `SUCCESS` |

4. Show the result of each task. Replace `RUN_ID` with the run ID from the run URL.

   ```bash
   databricks jobs get-run RUN_ID
   ```

5. Remove the deployed resources.

   ```bash
   databricks bundle destroy
   ```
