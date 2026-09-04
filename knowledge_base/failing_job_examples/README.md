# Failing job examples

This bundle provides small Lakeflow Jobs that fail for known, deterministic reasons. Use them to test alerting, monitoring, troubleshooting, and automated remediation workflows without changing production jobs.

Every job is expected to finish in the `FAILED` state. The bundle has no schedules, configured retries, or persistent data writes.

The target workspace must support serverless Jobs compute.

## Included failures

| Resource key | Failure type | Expected error |
| --- | --- | --- |
| `schema_drift_failure` | An upstream `amount` column changed from numeric to string | `Schema drift detected: expected amount to be numeric, found string` |
| `data_quality_failure` | Duplicate IDs, a null customer, and a non-positive amount | `Data quality checks failed: duplicate_transaction_ids=1, null_customers=1, non_positive_amounts=1` |
| `missing_input_failure` | A required table does not exist | Spark `TABLE_OR_VIEW_NOT_FOUND` |
| `invalid_configuration_failure` | Invalid batch size and missing checkpoint path | `Invalid job configuration: batch_size must be greater than zero; checkpoint_path is required in incremental mode` |

## Run the examples

The default target uses development mode, so deployed job names are prefixed with your user name.

```bash
databricks bundle validate
databricks bundle deploy
```

Run each example separately:

```bash
databricks bundle run schema_drift_failure
databricks bundle run data_quality_failure
databricks bundle run missing_input_failure
databricks bundle run invalid_configuration_failure
```

Each `bundle run` command returns a non-zero exit code after the job reaches its intentional failure. Open the run URL printed by the CLI to inspect the task output and stack trace.

## Clean up

After testing, remove the deployed development resources:

```bash
databricks bundle destroy
```
