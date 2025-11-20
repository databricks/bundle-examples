# Third-Party Monitoring Integration

This document describes the configuration and architecture for integrating Databricks ingestion pipelines with
third-party observability platforms.

## Table of Contents
- [Overview](#overview)
- [Telemetry Data](#telemetry-data)
  - [Logs](#logs)
  - [Metrics](#metrics)
  - [Events](#events)
- [Setup](#setup)
  - [Storing Secrets](#storing-secrets)
  - [Datadog](#datadog)
  - [New Relic](#new-relic)
  - [Azure Monitor](#azure-monitor)
  - [Splunk Observability Cloud](#splunk-observability-cloud)
  - [Advanced Configuration](#advanced-configuration)
    - [Endpoint Overrides](#endpoint-overrides)
    - [HTTP Client Tuning](#http-client-tuning)
- [Important Considerations](#important-considerations)
- [Developer Docs](#developer-docs)
  - [Code Architecture](#code-architecture)
    - [Conversion Layer](#conversion-layer)
      - [Part 1: Inference - Extract Telemetry Data](#part-1-inference---extract-telemetry-data)
      - [Part 2: Destination Conversion - Transform to Platform Format](#part-2-destination-conversion---transform-to-platform-format)
    - [Transmission Layer](#transmission-layer)
  - [Flow](#flow)
  - [Adding New Telemetry](#adding-new-telemetry)

## Overview
Telemetry sinks for the monitoring ETL pipeline, enables  real-time observability of
Databricks ingestion pipelines through structured streaming based ingestion to third-party 
observability platforms.

The sinks automatically capture and forward pipeline execution data including errors,
performance metrics, and status events to provide comprehensive monitoring and alerting
capabilities for data ingestion workflows.

## Telemetry Data
The pipeline sends the following telemetry data to the observability platforms:

### Logs
- Error logs capturing pipeline failures, exceptions, and error states
- Tagged with `pipeline_id`, `pipeline_name`, `pipeline_run_id`, `table_name`, `flow_name`
- Includes `pipeline_run_link` and detailed error information as attributes

### Metrics
**Table Throughput Metrics:**
- `dlt.table.throughput.upserted_rows`: Count of upserted rows per table
- `dlt.table.throughput.deleted_rows`: Count of deleted rows per table
- `dlt.table.throughput.output_rows`: Total output rows per table

**Pipeline Performance Metrics:**
- `pipeline.run.starting_seconds`: Time from queue to start
- `pipeline.run.waiting_for_resources_seconds`: Resource allocation wait time
- `pipeline.run.initialization_seconds`: Pipeline initialization duration
- `pipeline.run.running_seconds`: Actual execution time
- `pipeline.run.total_seconds`: End-to-end pipeline duration

### Events
- Pipeline status change events (RUNNING, COMPLETED, FAILED, etc.)
- Includes `pipeline_link`, `pipeline_run_link`, completion status, timing, error messages

## Setup

Make sure Databricks has allowlisted the required outbound endpoints for the chosen observability platform.

### Storing Secrets

For API keys and other sensitive configuration, it is recommended to store them in Databricks secrets.
Instead of providing individual configuration keys in Spark config, create a Databricks secret scope containing all
required parameters and reference it using the 'secrets_scope' parameter. The secret key names in the scope must
exactly match the Spark configuration parameter names (e.g., secret key 'api_key' corresponds to Spark parameter
'api_key'). When both Spark config and secrets are provided, secrets will be automatically merged during execution and
will take precedence over Spark configuration values.

See: https://docs.databricks.com/aws/en/security/secrets/

### Datadog

**Configuration Parameters:**
- **destination** (str): Must be set to `datadog` to enable Datadog telemetry sink.
- **api_key** (str): Datadog API key for authentication. Must have permissions to send metrics, logs, and events.
                    Recommended to store in Databricks secrets for security. Please ensure the key has the necessary
                    scopes and permissions to ingest logs, metrics, and events.
                    Refer: https://docs.datadoghq.com/account_management/api-app-keys/
- **host_name** (str): Datadog site for the account. Example: 'datadoghq.com', 'datadoghq.eu', 'us5.datadoghq.com', 'ap2.datadoghq.com'.
                    Refer: https://docs.datadoghq.com/api/latest/using-the-api/

**Setup Steps:**

1. Create a Databricks secret scope and store the Datadog API key:
```bash
databricks secrets create-scope datadog-secrets
databricks secrets put-secret datadog-secrets api_key --string-value "<your-datadog-api-key>"
```

2. Update the pipeline configuration file `resources/monitoring_etl.pipeline.yml` to reference the variables:
```yaml
    resources:
    pipelines:
    cdc_connector_monitoring_etl:
    name: "Monitoring ETL for CDC Connector Pipelines"
    libraries:
    - glob:
    include: ../monitoring_etl/**
    - glob:
    include: ../../third_party_sinks/**
    serverless: ${var.serverless_monitoring_pipeline_enabled}
    development: true
    catalog: ${var.monitoring_catalog}
    schema: ${resources.schemas.monitoring_schema.name}
    root_path: ${workspace.file_path}/cdc_connector_monitoring_dab/monitoring_etl
    configuration:
    monitoring_catalog: ${var.monitoring_catalog}
    monitoring_schema: ${resources.schemas.monitoring_schema.name}
    directly_monitored_pipeline_ids: ${var.directly_monitored_pipeline_ids}
    imported_event_log_tables: ${var.imported_event_log_tables}

    # Third-party monitoring configuration
    destination: ${var.third_party_destination}
    secrets_scope: ${var.third_party_secrets_scope}
    host_name: ${var.third_party_host_name}
```

3. Define third-party monitoring variables in `databricks.yml`:
```yaml
targets:
  dev:
    default: true
    mode: development
    variables:
      # ... other variables ...

      # Third-party monitoring configuration. Replace with actual values.
      third_party_destination: "datadog"
      third_party_host_name: "us5.datadoghq.com"
      third_party_secrets_scope: "datadog-secrets"
```
### New Relic

**Configuration Parameters:**
- **destination** (str): Must be set to `newrelic` to enable New Relic telemetry sink.
- **api_key** (str): New Relic API key for authentication. Must have permissions to send metrics, logs, and events.
                    Recommended to store in Databricks secrets for security.
                    Refer: https://docs.newrelic.com/docs/apis/intro-apis/new-relic-api-keys/
- **host_name** (str): New Relic site for the account. Example: 'newrelic.com', 'eu.newrelic.com'.
                    Refer: https://docs.newrelic.com/docs/apis/ingest-apis/introduction-new-relic-ingest-apis/
- **account_id** (str): New Relic account ID. Required for auto-generating events endpoint. Can be found in the New Relic UI under Account Settings.
                    Refer: https://docs.newrelic.com/docs/accounts/accounts-billing/account-structure/account-id/

**Setup Steps:**

1. Create a Databricks secret scope and store the New Relic API key:
```bash
databricks secrets create-scope newrelic-secrets
databricks secrets put-secret newrelic-secrets api_key --string-value "<your-newrelic-api-key>"
```

2. Update the pipeline configuration file `resources/monitoring_etl.pipeline.yml` to reference the variables:
```yaml
    resources:
    pipelines:
    cdc_connector_monitoring_etl:
    name: "Monitoring ETL for CDC Connector Pipelines"
    libraries:
    - glob:
    include: ../monitoring_etl/**
    - glob:
    include: ../../third_party_sinks/**
    serverless: ${var.serverless_monitoring_pipeline_enabled}
    development: true
    catalog: ${var.monitoring_catalog}
    schema: ${resources.schemas.monitoring_schema.name}
    root_path: ${workspace.file_path}/cdc_connector_monitoring_dab/monitoring_etl
    configuration:
    monitoring_catalog: ${var.monitoring_catalog}
    monitoring_schema: ${resources.schemas.monitoring_schema.name}
    directly_monitored_pipeline_ids: ${var.directly_monitored_pipeline_ids}
    imported_event_log_tables: ${var.imported_event_log_tables}

    # Third-party monitoring configuration
    destination: ${var.third_party_destination}
    secrets_scope: ${var.third_party_secrets_scope}
    host_name: ${var.third_party_host_name}
    account_id: ${var.third_party_account_id}
```

3. Define third-party monitoring variables in `databricks.yml`:
```yaml
targets:
  dev:
    default: true
    mode: development
    variables:
      # ... other variables ...

      # Third-party monitoring configuration. Replace with actual values.
      third_party_destination: "newrelic"
      third_party_host_name: "newrelic.com"
      third_party_secrets_scope: "newrelic-secrets"
      third_party_account_id: "<your-newrelic-account-id>"
```

### Azure Monitor

Supports sending telemetry to Azure Monitor using the Data Collection Rule (DCR) API. All telemetry data will be sent
as logs to custom tables in a Log Analytics Workspace. 

**Configuration Parameters:**
- **destination**: Must be set to `azuremonitor` to enable Azure Monitor telemetry sink.
- **host_name**: Data Collection Endpoint (DCE) hostname for the Azure Monitor workspace.
    Format: `<dce-name>.<region>.ingest.monitor.azure.com`
    Example: `my-dce-abc123.eastus-1.ingest.monitor.azure.com`
    This is used to auto-generate the DCE endpoint URL.
- **azure_client_id**: Azure service principal client ID for authentication.
    Recommended to store in Databricks secrets for security.
- **azure_client_secret**: Azure service principal client secret for authentication.
    Recommended to store in Databricks secrets for security.
- **azure_dcr_immutable_id**: Immutable ID of the Data Collection Rule containing all three telemetry streams (metrics, logs, events).
    Example: `dcr-1234567890abcdef1234567890abcdef`
- **azure_tenant_id**: Azure AD tenant ID. Required for authorization endpoint.
    Example: `12345678-1234-1234-1234-123456789012`

**Azure Infrastructure Setup:**

Before we begin exporting telemetry to Azure Monitor, we need to set up the following Azure resources:
- **Service Principal**: Provides authentication credentials for secure API access to Azure Monitor
- **Log Analytics Workspace**: Central data repository where telemetry data is stored and queried
- **Data Collection Endpoint (DCE)**: Regional/Global ingestion endpoint for receiving telemetry data
- **Data Collection Rule (DCR)**: Defines data transformation rules and routing to destination tables

The data will be stored in the following custom tables:
- **Metrics**: `DatabricksMetrics_CL` - Pipeline performance metrics and table throughput data
- **Logs**: `DatabricksLogs_CL` - Error logs and failure information
- **Events**: `DatabricksEvents_CL` - Pipeline status change events

**Setup Steps:**

1. **[Optional] Create a resource group** (if you don't have one):
```bash
az group create --name databricks-monitoring-rg --location "East US"
```

2. **[Optional] Create a Log Analytics Workspace** (if you don't have one):
```bash
az monitor log-analytics workspace create \
    --resource-group databricks-monitoring-rg \
    --workspace-name databricks-monitoring-workspace \
    --location "East US"
```

3. **[Optional] Create a service principal and grant it access to the workspace** (if you don't have one):
```bash
# Create service principal
az ad sp create-for-rbac --name databricks-monitoring-sp --skip-assignment

# Assign Log Analytics Contributor role to the service principal
az role assignment create \
    --assignee "<service-principal-client-id>" \
    --role "Log Analytics Contributor" \
    --scope "<Log Analytics Workspace ID>"
```
Note down the `appId` (client ID), `password` (client secret), and `tenant` values from the service principal creation output.

4. **Run the setup script** to create Data Collection Endpoint (DCE), custom tables, and Data Collection Rule (DCR):
```bash
./third_party_sinks/azure_setup.sh \
    --resource-group databricks-monitoring-rg \
    --location "<Region E.g., East US" \
    --workspace-name "<Workspace Name>"
```
The script creates:
- Public data collection endpoint: `databricks-monitoring-dce`
- Custom tables: `DatabricksMetrics_CL`, `DatabricksLogs_CL`, `DatabricksEvents_CL`
- Data collection rule: `databricks-monitoring-dcr` (configured for all three telemetry streams)

The script outputs the following values needed for Databricks configuration:
- **Azure Host Name** (DCE hostname)
- **Azure DCR Immutable ID**

For more customization, see `azure_setup.sh`.


**Pipeline Configuration:**

1. Create a Databricks secret scope and store Azure credentials:
```bash
databricks secrets create-scope azuremonitor-secrets
databricks secrets put-secret azuremonitor-secrets azure_client_id --string-value "<SERVICE_PRINCIPAL_APP_ID>"
databricks secrets put-secret azuremonitor-secrets azure_client_secret --string-value "<SERVICE_PRINCIPAL_PASSWORD>"
```

2. Update the pipeline configuration file `resources/monitoring_etl.pipeline.yml` to reference the variables:
```yaml
    resources:
    pipelines:
    cdc_connector_monitoring_etl:
    name: "Monitoring ETL for CDC Connector Pipelines"
    libraries:
    - glob:
    include: ../monitoring_etl/**
    - glob:
    include: ../../third_party_sinks/**
    serverless: ${var.serverless_monitoring_pipeline_enabled}
    development: true
    catalog: ${var.monitoring_catalog}
    schema: ${resources.schemas.monitoring_schema.name}
    root_path: ${workspace.file_path}/cdc_connector_monitoring_dab/monitoring_etl
    configuration:
    monitoring_catalog: ${var.monitoring_catalog}
    monitoring_schema: ${resources.schemas.monitoring_schema.name}
    directly_monitored_pipeline_ids: ${var.directly_monitored_pipeline_ids}
    imported_event_log_tables: ${var.imported_event_log_tables}

    # Third-party monitoring configuration
    destination: ${var.third_party_destination}
    secrets_scope: ${var.third_party_secrets_scope}
    azure_tenant_id: ${var.azure_tenant_id}
    host_name: ${var.third_party_host_name}
    azure_dcr_immutable_id: ${var.azure_dcr_immutable_id}
```

3. Define third-party monitoring variables in `databricks.yml`:
```yaml
targets:
  dev:
    default: true
    mode: development
    variables:
      # ... other variables ...

      # Third-party monitoring configuration. Replace with actual values.
      third_party_destination: "azuremonitor"
      third_party_host_name: "my-dce-abc123.eastus-1.ingest.monitor.azure.com"
      third_party_secrets_scope: "azuremonitor-secrets"
      azure_tenant_id: "<TENANT_ID>"
      azure_dcr_immutable_id: "dcr-1234567890abcdef1234567890abcdef"
```

**Important Notes:**
- The OAuth2 access tokens are automatically refreshed when tokens get older than `azure_max_access_token_staleness` (default: 3300 seconds). Adjust this parameter if needed.
- If additional scope/parameters are required for fetching oauth2 tokens, please update the payload in dbx_ingestion_monitoring_pkg/third_party_sinks/azuremonitor_sink.py fetch_access_token() function.

### Splunk Observability Cloud

Supports sending telemetry to Splunk Observability Cloud (formerly SignalFx) using the SignalFx Ingest API. Since,
Splunk Observability Cloud does not support native log ingestion, logs are sent as events.

**Configuration Parameters:**
- **destination**: Must be set to `splunk_observability` to enable Splunk Observability Cloud telemetry sink.
- **host_name**: Splunk Observability Cloud ingest hostname for your realm.
  Format: `ingest.<realm>.signalfx.com`
  Example: `ingest.us0.signalfx.com`, `ingest.eu0.signalfx.com`
  Refer: https://dev.splunk.com/observability/docs/apibasics/api_list/
- **splunk_access_token**: Splunk Observability Cloud organization access token for metrics, events, and logs.
    Recommended to store in Databricks secrets for security.
    Refer: https://help.splunk.com/en/splunk-observability-cloud/administer/authentication-and-security/authentication-tokens/org-access-tokens

**Setup Steps:**

1. Create a Databricks secret scope and store Splunk credentials:
```bash
databricks secrets create-scope splunk-secrets
databricks secrets put-secret splunk-secrets splunk_access_token --string-value "<SPLUNK_ACCESS_TOKEN>"
```

2. Update the pipeline configuration file `resources/monitoring_etl.pipeline.yml` to reference the variables:

```yaml
    resources:
    pipelines:
    cdc_connector_monitoring_etl:
    name: "Monitoring ETL for CDC Connector Pipelines"
    libraries:
    - glob:
    include: ../monitoring_etl/**
    - glob:
    include: ../../third_party_sinks/**
    serverless: ${var.serverless_monitoring_pipeline_enabled}
    development: true
    catalog: ${var.monitoring_catalog}
    schema: ${resources.schemas.monitoring_schema.name}
    root_path: ${workspace.file_path}/cdc_connector_monitoring_dab/monitoring_etl
    configuration:
    monitoring_catalog: ${var.monitoring_catalog}
    monitoring_schema: ${resources.schemas.monitoring_schema.name}
    directly_monitored_pipeline_ids: ${var.directly_monitored_pipeline_ids}
    imported_event_log_tables: ${var.imported_event_log_tables}

    # Third-party monitoring configuration
    destination: ${var.third_party_destination}
    host_name: ${var.third_party_host_name}
    secrets_scope: ${var.third_party_secrets_scope}
```

3. Define third-party monitoring variables in `databricks.yml`:
```yaml
targets:
  dev:
    default: true
    mode: development
    variables:
      # ... other variables ...

      # Third-party monitoring configuration. Replace with actual values.
      third_party_destination: "splunk_observability"
      third_party_host_name: "ingest.us0.signalfx.com"
      third_party_secrets_scope: "splunk-secrets"
```

**Important Notes:**
- All telemetry (metrics, events, and logs) is sent to SignalFx APIs (Splunk Observability Cloud)
- Logs are sent as events to eliminate the need for HEC (HTTP Event Collector) setup
- Only a single access token is required for all telemetry types

### Advanced Configuration

The following optional parameters provide fine-grained control over the pipeline:

#### Endpoint Overrides
By default, API endpoints are automatically constructed from the `host_name` parameter using platform-specific URL patterns. These parameters allow explicit endpoint override for regionalization, compliance, or proxy routing requirements.:

- **endpoints.metrics** (str): Full URL for the metrics ingestion API endpoint. Overrides the auto-generated endpoint based on `host_name`.
- **endpoints.logs** (str): Full URL for the logs ingestion API endpoint. Overrides the auto-generated endpoint based on `host_name`.
- **endpoints.events** (str): Full URL for the events ingestion API endpoint. Overrides the auto-generated endpoint based on `host_name`.

#### HTTP Client Tuning

- **num_rows_per_batch** (int): Controls batching granularity for HTTP requests. Determines the number of telemetry records aggregated before transmission. Lower values reduce memory pressure and payload size but increase request frequency. Higher values improve throughput but risk exceeding API payload limits.
  - Default: 100
  - Note: Some observability platforms accept only a single event per API call. In such cases, this parameter is ignored.

- **max_retry_duration_sec** (int): Maximum time window for exponential backoff retry logic when HTTP requests fail due to transient errors (network issues, rate limiting, temporary service unavailability). The HTTP client will retry failed requests with exponentially increasing delays until this duration is exceeded.
  - Default: 300 seconds (5 minutes)

- **request_timeout_sec** (int): Socket-level timeout for individual HTTP POST requests. Applies to connection establishment, request transmission, and response reception. Does not include retry delays.
  - Default: 30 seconds


## Important Considerations

1. **Payload Size**: The code does not split large payloads. The `num_rows_per_batch` parameter should be set small to keep the overall payload size within acceptable limits.

2. **Data Staleness**: APIs might enforce a staleness limit on incoming data. The current code does not enforce such a
threshold, so the pipeline schedule must be configured to ensure data freshness. If stale data is rejected by the API, the pipeline will retry the request and eventually drop the call if it continues to fail.

3. **Formatting**: The code trims strings which are longer than the maximum allowed length as per the schema. Any date time is sent as ISO 8601 formatted string.


# Developer Docs

## Code Architecture

The sink implementations contains the following main components:

- **Streaming Source Tables**: Read from `event_logs_bronze` and `pipeline_runs_status` tables
- **Conversion Layer**: Two-part transformation process
  - **Part 1 - Inference**: Extract telemetry data from source rows (logs, events, metrics)
  - **Part 2 - Destination Conversion**: Transform to platform-specific JSON format with schema validation and batch into HTTP request DataFrames
- **Transmission Layer**: HTTP client with gzip compression, connection pooling, exponential backoff retry, and failure handling
- **Observability Platform API**: Final delivery to Datadog or New Relic endpoints

### Conversion Layer
**Purpose:** Extracts telemetry information from streaming table rows, transforms them into platform-specific payload formats, and batches them for HTTP delivery.

The conversion layer has two distinct parts:

#### Part 1: Inference - Extract Telemetry Data
The inference part reads streaming table rows and extracts meaningful telemetry data from them. These `convert_row_to_*` functions understand the structure of the source tables (event_logs_bronze, pipeline_runs_status) and extract relevant fields:

- `convert_row_to_error_log(row)`: Extracts error information from event logs and converts to log format
- `convert_row_to_pipeline_status_event(row)`: Extracts pipeline state changes and converts to event format
- `convert_row_to_pipeline_metrics(row)`: Calculates pipeline execution timing metrics from timestamps
- `convert_row_to_table_metrics(row)`: Extracts table-level throughput metrics from flow progress data

#### Part 2: Destination Conversion - Transform to Platform Format
The destination conversion part takes the extracted telemetry data and converts it into platform-specific JSON payloads that conform to each observability platform's API specifications. These converter classes handle the differences between destination formats:

- `MetricsConverter`:
  - `create_metric(metric_name, metric_value, tags, timestamp, additional_attributes)`: Converts extracted metric data into destination-specific JSON format with schema validation
  - `create_http_requests_spec(df, num_rows_per_batch, headers, endpoint)`: Batches metrics into HTTP request DataFrame

- `EventsConverter`:
  - `create_event(title, status, tags, timestamp, additional_attributes)`: Converts extracted event data into destination-specific JSON format with schema validation
  - `create_http_requests_spec(df, num_rows_per_batch, headers, endpoint)`: Batches events into HTTP request DataFrame

- `LogsConverter`:
  - `create_log(title, status, tags, timestamp, additional_attributes)`: Converts extracted log data into destination-specific JSON format with schema validation
  - `create_http_requests_spec(df, num_rows_per_batch, headers, endpoint)`: Batches logs into HTTP request DataFrame

**Schema Validation:**
All telemetry payloads are validated against predefined JSON schemas (METRICS_SCHEMA, LOGS_SCHEMA, EVENTS_SCHEMA) before transmission. The `enforce_schema()` function:
- Validates field types and required properties
- Trims strings exceeding maxLength constraints
- Converts datetime objects to appropriate formats (ISO 8601 strings or Unix timestamps)
- Note: Schema validation failures will cause the micro-batch to fail, ensuring data quality

### Transmission Layer
**Purpose:** Provides reliable HTTP delivery with retry mechanism and connection pooling.

**HTTPClient Class:**
- `post(http_request_specs_df)`: Sends HTTP POST requests for each row in the DataFrame
  - Input: DataFrame with columns: endpoint (str), header (JSON str), payloadBytes (binary)
  - Compresses payloads using gzip before transmission
  - Uses persistent session for connection pooling
  - Implements exponential backoff retry logic via tenacity library
  - Continues processing on failure (logs error and moves to next request)

**Retry Configuration:**
- `max_retry_duration_sec`: Maximum time window for retries (default: 300s)
- `request_timeout_sec`: Individual request timeout (default: 30s)
- Exponential backoff: multiplier=1, min=1s, max=10s

## Flow

1. **Configuration Validation** (at module load time):
   - Checks if `destination` parameter is set to "datadog" or "newrelic"
   - Calls `getThirdPartySinkConfigFromSparkConfig()` to build configuration:
     - Extracts required parameters: destination, api_key, host_name
     - Merges secrets from Databricks secret scope if provided
     - Auto-generates endpoints from host_name if not explicitly configured
     - Sets default values for optional parameters

2. **Global Initialization**:
   - `initialize_global_config()`: Stores validated config in `_global_config`
   - Instantiates converter objects: `_log_converter`, `_events_converter`, `_metrics_converter`

3. **Sink Registration**:
   - `register_sink_for_errors()`: Monitors event_logs_bronze for error logs
   - `register_sink_for_pipeline_events()`: Monitors pipeline_runs_status for state changes
   - `register_sink_for_pipeline_metrics()`: Monitors pipeline_runs_status for execution timing
   - `register_sink_for_table_metrics()`: Monitors event_logs_bronze for flow_progress metrics

Each sink registration creates:
- A `@dlt.foreach_batch_sink` function that processes each micro-batch
- A `@dlt.append_flow` function that defines the streaming source query

## Adding New Telemetry

Assume you have a streaming source table/view (`custom_log_source_table` or `custom_log_source_view`) with:
- `my_log_message`: The log message content
- `my_log_tags`: Additional tags (common tags: `pipeline_id`, `pipeline_name`, `pipeline_run_id`, `table_name`)
- `event_timestamp`: The log timestamp

To send the above data to third party observability platforms, follow these steps:

1. **Create a converter function** in the Inference Layer:
```python
def convert_row_to_custom_telemetry(row):
    params = {
        "title": getattr(row, "my_log_message", ""),
        "status": "info",
        "tags": {"custom_tag": getattr(row, "my_log_tags", "")}, # Add more tags as needed
        "timestamp": timestamp_in_unix_milliseconds(row.event_timestamp),
        "additional_attributes": {} # add any additional attributes if needed
    }
    return _log_converter.create_log(**params)
```
This function extracts the relevant fields and uses the converter to create a log/metric/event in the destination format.

2. **Create a sink registration function**:
```python
def register_sink_for_custom_telemetry():
    @dlt.foreach_batch_sink(name="send_custom_to_3p_monitoring")
    def send_custom_to_3p_monitoring(batch_df, batch_id):
        destination_format_udf = udf(convert_row_to_custom_telemetry, StringType())
        telemetry_df = batch_df.withColumn("logs", destination_format_udf(struct("*"))).select("logs").filter(col("logs").isNotNull())
        http_request_spec = _log_converter.create_http_requests_spec(
            telemetry_df,
            _global_config["num_rows_per_batch"],
            get_header(_global_config["api_key"]),  # Use the appropriate header function
            _global_config["endpoints"]["logs"]
        )
        getClient(_global_config).post(http_request_spec)

    @dlt.append_flow(target="send_custom_to_3p_monitoring")
    def send_custom_to_sink():
        return spark.sql("SELECT * FROM STREAM(`custom_log_source_table`)")
```

This function converts the micro-batch rows to the destination format and sends them using the HTTP client.

3. **Register the sink** in the initialization section:
```python
if spark.conf.get("destination", None) == "datadog":
    initialize_global_config(spark.conf)
    register_sink_for_custom_telemetry()  # Add this line
    register_sink_for_errors()
    # ... other registrations
```
