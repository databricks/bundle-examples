# Common Configuration Guide

This document describes common configuration parameters shared among monitoring DABs (Databricks Asset Bundles).

Configuration is done through variables in a DAB deployment target.


## Required: Specify Monitoring Catalog and Schema

Configure `monitoring_catalog` and `monitoring_schema` to specify where the monitoring tables will be created. The catalog must already exist, but the schema will be created automatically if it doesn't exist.


## Required: Specify Pipelines to Monitor

Configuring which pipelines to monitor involves two steps:
1. Choose the method to extract pipeline event logs
2. Identify which pipelines to monitor

### Event Log Extraction Methods

There are two methods to extract a pipeline's event logs:

**Ingesting (Preferred)**
- Extracts event logs directly from a Delta table where the pipeline writes its logs
- Available for pipelines configured with the `event_log` field ([see documentation](https://docs.databricks.com/api/workspace/pipelines/update#event_log))
- Any UC-enabled pipeline using `catalog` and `schema` fields can be configured to store its event log in a Delta table
- Lower cost and better performance than importing

**Importing (Alternative)**
- First imports the pipeline's event log into a Delta table, then extracts from there
- More expensive operation compared to ingesting
- Use only for UC pipelines that use the legacy `catalog`/`target` configuration style
- Requires configuring dedicated import jobs (see ["Optional: Configure Event Log Import Job(s)"](#optional-configure-event-log-import-jobs))

### Pipeline Identification Methods

For both ingested and imported event logs, you can identify pipelines using:

**1. Direct Pipeline IDs**
- Use `directly_monitored_pipeline_ids` for ingested event logs
- Use `imported_pipeline_ids` for imported event logs
- Format: Comma-separated list of pipeline IDs

**2. Pipeline Tags**
- Use `directly_monitored_pipeline_tags` for ingested event logs
- Use `imported_pipeline_tags` for imported event logs
- Format: Semi-colon-separated lists of comma-separated `tag[:value]` pairs
  - **Semicolons (`;`)** = OR logic - pipelines matching ANY list will be selected
  - **Commas (`,`)** = AND logic - pipelines matching ALL tags in the list will be selected
  - `tag` without a value is equivalent to `tag:` (empty value)
  
**Example:**
```
directly_monitored_pipeline_tags: "tier:T0;team:data,tier:T1"
```
This selects pipelines with either:
- Tag `tier:T0`, OR
- Tags `team:data` AND `tier:T1`

**Combining Methods:**
All pipeline identification methods can be used together. Pipelines matching any criteria will be included.

> **Performance Tip:** For workspaces with hundreds or thousands of pipelines, enable pipeline tags indexing to significantly speed up tag-based discovery. See ["Optional: Configure Pipelines Tags Indexing Job"](#optional-configure-pipelines-tags-indexing-job) for more information.


## Optional: Monitoring ETL Pipeline Configuration

**Schedule Configuration:**
- Customize the monitoring ETL pipeline schedule using the `monitoring_etl_cron_schedule` variable
- Default: Runs hourly
- Trade-off: Higher frequency increases data freshness but also increases DBU costs

For additional configuration options, refer to the `variables` section in the `databricks.yml` file for the DAB containing the monitoring ETL pipeline.


## Optional: Configure Event Log Import Job(s)

> **Note:** Only needed if you're using the "Importing" event log extraction method.

**Basic Configuration:**
1. Set `import_event_log_schedule_state` to `UNPAUSED`
   - Default schedule: Hourly (configurable via `import_event_log_cron_schedule`)

2. Configure the `imported_event_log_tables` variable in the monitoring ETL pipeline
   - Specify the table name(s) where imported logs are stored
   - You can reference `${var.imported_event_logs_table_name}`
   - Multiple tables can be specified as a comma-separated list

**Handling Pipeline Ownership:**
- If monitored pipelines have a different owner than the DAB owner:
  - Edit `common/resources/import_event_logs.job.yml`
  - Uncomment the `run_as` principal lines
  - Specify the appropriate principal

- If multiple sets of pipelines have different owners:
  - Duplicate the job definition in `common/resources/import_event_logs.job.yml`
  - Give each job a unique name
  - Configure the `run_as` principal for each job as needed
  - All jobs can share the same target table (`imported_event_logs_table_name`)

See [common/vars/import_event_logs.vars.yml](common/vars/import_event_logs.vars.yml) for detailed configuration variable descriptions.


## Optional: Configure Pipelines Tags Indexing Job

> **When to use:** For large-scale deployments with hundreds or thousands of pipelines using tag-based identification.

**Why indexing matters:**
Tag-based pipeline discovery requires fetching metadata for every pipeline via the Databricks API on each event log import and monitoring ETL execution. For large deployments, this can be slow and expensive. The tags index caches this information to significantly improve performance.

**Configuration Steps:**

1. **Enable the index:**
   - Set `pipeline_tags_index_enabled` to `true`

2. **Enable the index refresh job:**
   - Set `pipeline_tags_index_schedule_state` to `UNPAUSED`
   - This job periodically refreshes the index to keep it up-to-date

3. **Optional: Customize refresh schedule**
   - Configure `pipeline_tags_index_cron_schedule` (default: daily)
   - If you change the schedule, consider adjusting `pipeline_tags_index_max_age_hours` (default: 48 hours)
   - When the index is older than the max age threshold, the system falls back to API-based discovery

See [common/vars/pipeline_tags_index.vars.yml](common/vars/pipeline_tags_index.vars.yml) for detailed configuration variable descriptions.

> **Notes:** 
1. The system gracefully falls back to API-based discovery if the index is disabled, unavailable, or stale.
2. If a recently created or tagged pipeline is missing from the monitoring ETL output, this can be due to the staleness of the index. Run the corresponding `Build *** pipeline tags index` job to refresh the index and re-run the monitoring ETL pipeline.


## Optional: Configure Third-Party Monitoring Integration

You can export monitoring data to third-party monitoring platforms such as Datadog, Splunk, New Relic, or Azure Monitor.

See [README-third-party-monitoring.md](README-third-party-monitoring.md) for detailed configuration instructions.

