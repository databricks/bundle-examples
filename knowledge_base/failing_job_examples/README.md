# Failing job examples

This bundle provides small Lakeflow Jobs that fail for known, deterministic reasons. Use them to test alerting, monitoring, troubleshooting, and automated remediation workflows without changing production jobs.

With the checked-in defaults, every job is expected to finish in the `FAILED` state. The bundle has no schedules, configured retries, or persistent data writes.

The included job resources use serverless Jobs compute. The notebooks also run on classic Databricks compute and require no catalog or table setup.

## Included failures

| Resource key | Failure type | Expected error |
| --- | --- | --- |
| `schema_drift_failure` | A simulated source schema defines `amount` as string while the contract requires a numeric type | `Schema contract violation in simulated source schema (no source table): expected amount to be numeric, found string` |
| `missing_input_failure` | The configured `input_view` job parameter is misspelled | Spark `TABLE_OR_VIEW_NOT_FOUND` |
| `invalid_configuration_failure` | A non-positive batch size | `Invalid job configuration: batch_size must be greater than zero, found 0` |

The schema-drift example does not read a table. To verify the remediation, import `DoubleType` and change the `amount` field from `StringType()` to `DoubleType()`. The notebook then completes successfully.

## Run the examples

The default target uses development mode, so deployed job names are prefixed with your user name.

```bash
databricks bundle validate
databricks bundle deploy
```

Run each example separately:

```bash
databricks bundle run schema_drift_failure
databricks bundle run missing_input_failure
databricks bundle run invalid_configuration_failure
```

Each `bundle run` command returns a non-zero exit code after the job reaches its intentional failure. Open the run URL printed by the CLI to inspect the task output and stack trace.

## Clean up

After testing, remove the deployed development resources:

```bash
databricks bundle destroy
```
