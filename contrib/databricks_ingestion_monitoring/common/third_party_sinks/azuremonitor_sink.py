"""
Azure Monitor Sink for Monitoring ETL Pipeline.

For configuration details, refer to README-third-party-monitoring.md
"""

import json
import requests
import gzip
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_delay, wait_exponential
from datetime import datetime, timezone
from pyspark.sql import SparkSession
from pyspark.sql.types import StringType, ArrayType
from pyspark.sql.functions import lit, col, collect_list, concat, expr, udf, struct, explode, regexp_replace
import dlt
import threading

# Global Configuration.
SERVICE_NAME = "databricks-lakeflow-connect"
SOURCE_NAME = "databricks"
_global_config = None
_log_converter = None
_events_converter = None
_metrics_converter = None

# Schemas to validate dictionaries returned by converter create_* methods
# Only validates required fields with exact case-sensitive field names used in the functions

METRICS_SCHEMA = {
    "type": "object",
    "required": ["TimeGenerated", "metric_name", "metric_value", "timestamp"],
    "properties": {
        "TimeGenerated": {"type": "string", "format": "date-time"},
        "metric_name": {"type": "string"},
        "metric_value": {"type": "number"},
        "timestamp": {"type": "integer"},
        "tags": {"type": "object", "additionalProperties": True},
        "additional_attributes": {"type": "object", "additionalProperties": True}
    }
}

LOGS_SCHEMA = {
    "type": "object",
    "required": ["TimeGenerated", "message", "status", "timestamp"],
    "properties": {
        "TimeGenerated": {"type": "string", "format": "date-time"},
        "message": {"type": "string"},
        "status": {"type": "string"},
        "timestamp": {"type": "integer"},
        "tags": {"type": "object", "additionalProperties": True},
        "additional_attributes": {"type": "object", "additionalProperties": True}
    }
}

EVENTS_SCHEMA = {
    "type": "object",
    "required": ["TimeGenerated", "message", "status", "timestamp"],
    "properties": {
        "TimeGenerated": {"type": "string", "format": "date-time"},
        "message": {"type": "string"},
        "status": {"type": "string"},
        "timestamp": {"type": "integer"},
        "tags": {"type": "object", "additionalProperties": True},
        "additional_attributes": {"type": "object", "additionalProperties": True}
    }
}

# ================================================================================
#  UTILITIES
# ================================================================================

def get_azure_header(access_token: str = None):
    """Get headers for the Azure Monitor API."""
    return {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}

def fetch_access_token(config):
    """
    Fetches an access token for a service principal to write to Azure Monitor.

    Args:
        config (dict):
            - client_id: Service principal client ID
            - client_secret: Service principal client secret
            - access_token_url: Azure AD token endpoint
            - request_timeout_sec: HTTP request timeout

    Returns:
        dict: {
            "access_token": <str>,
            "last_load_timestamp": <epoch_seconds>
        }
    """
    payload = {
        "grant_type": "client_credentials",
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "scope": "https://monitor.azure.com//.default"
    }

    now = int(datetime.now(timezone.utc).timestamp())
    token_url = config['access_token_url']

    try:
        response = requests.post(token_url, data=payload, timeout=config['request_timeout_sec'])
        response.raise_for_status()

        token_json = response.json()
        if "access_token" not in token_json:
            raise RuntimeError(f"Token response missing 'access_token': {token_json}")

        return {
            "access_token": token_json["access_token"],
            "last_load_timestamp": now
        }

    except requests.RequestException as e:
        error_message = (
            f"Failed to fetch Azure access token.\n"
            f"Request URL: {token_url}\n"
            f"Request payload: {payload}\n"
            f"Response status: {getattr(e.response, 'status_code', 'N/A')}\n"
            f"Response body: {getattr(e.response, 'text', 'N/A')}\n"
            f"Original exception: {str(e)}"
        )
        raise RuntimeError(error_message) from e



def initialize_global_config(spark_conf):
    """Initialize global configuration from Spark configuration."""
    global _global_config, _log_converter, _events_converter, _metrics_converter

    _global_config = getThirdPartySinkConfigFromSparkConfig(spark_conf)
    _log_converter = AzureMonitorLogsConverter()
    _events_converter = AzureMonitorEventsConverter()
    _metrics_converter = AzureMonitorMetricsConverter()

def getParam(spark_conf, key: str, default=None):
    value = spark_conf.get(key, default)
    if value == "" or value is None:
        return None
    return value

def getThirdPartySinkConfigFromSparkConfig(spark_conf):
    """
    Extract and merge configuration from Spark configuration and secret scope.

    This function extracts configuration variables from Spark configuration and merges
    them with key-value pairs from a secret scope (if provided) to build common_params.
    Secret store values take precedence over Spark configuration values when both exist.

    Args:
        spark_conf: Spark configuration object containing required parameters

    Returns:
        dict: Merged configuration parameters with secrets taking precedence

    The function looks for a 'secrets_scope' parameter in Spark config. If found,
    it will retrieve all secrets from that scope and merge them with the base
    configuration, giving preference to secret values.
    """
    destination = getParam(spark_conf, "destination")
    if destination is None:
        raise ValueError("Destination must be provided for third party sinks.")

    common_params = {
        "destination": destination,
        "num_rows_per_batch": int(spark_conf.get("num_rows_per_batch", "100")),
        "max_retry_duration_sec": int(spark_conf.get("max_retry_duration_sec", "300")),
        "request_timeout_sec": int(spark_conf.get("request_timeout_sec", "30")),
        "max_access_token_staleness": int(spark_conf.get("azure_max_access_token_staleness", "3300")),
        "client_id": getParam(spark_conf, "azure_client_id"),
        "client_secret": getParam(spark_conf, "azure_client_secret"),
        "tenant_id": getParam(spark_conf, "azure_tenant_id"),
        "host_name": getParam(spark_conf, "host_name"),
        "dcr_immutable_id": getParam(spark_conf, "azure_dcr_immutable_id")
    }

    scope = getParam(spark_conf, "secrets_scope")
    if scope is not None:
        secrets = {
            s.key: dbutils.secrets.get(scope=scope, key=s.key)
            for s in dbutils.secrets.list(scope)
        }
        common_params.update(secrets)

    # Get endpoints (allow override)
    metrics_endpoint = getParam(spark_conf, "endpoints.metrics")
    logs_endpoint = getParam(spark_conf, "endpoints.logs")
    events_endpoint = getParam(spark_conf, "endpoints.events")
    authorization_endpoint = getParam(spark_conf, "azure_authorization_endpoint")

    # Auto-generate authorization endpoint if not provided
    if authorization_endpoint is None:
        if common_params['tenant_id'] is None:
            raise ValueError(
                "Either 'azure_tenant_id' must be provided to auto-generate authorization endpoint, "
                "or 'azure_authorization_endpoint' must be explicitly configured."
            )
        authorization_endpoint = f"https://login.microsoftonline.com/{common_params['tenant_id']}/oauth2/v2.0/token"

    common_params["access_token_url"] = authorization_endpoint

    # Auto-generate data ingestion endpoints if not provided
    if not all([metrics_endpoint, logs_endpoint, events_endpoint]):
        if common_params['host_name'] is None:
            raise ValueError(
                "Either 'host_name' must be provided to auto-generate DCE endpoint, "
                "or all three endpoints (endpoints.metrics, endpoints.logs, endpoints.events) "
                "must be explicitly configured."
            )
        dce_endpoint = f"https://{common_params['host_name']}"

        if common_params['dcr_immutable_id'] is None:
            raise ValueError(
                "Either 'dcr_immutable_id' must be provided to auto-generate DCE endpoint, "
                "or all three endpoints (endpoints.metrics, endpoints.logs, endpoints.events) "
                "must be explicitly configured."
            )

        metrics_endpoint = f"{dce_endpoint}/dataCollectionRules/{common_params['dcr_immutable_id']}/streams/Custom-DatabricksMetrics_CL?api-version=2023-01-01"
        logs_endpoint = f"{dce_endpoint}/dataCollectionRules/{common_params['dcr_immutable_id']}/streams/Custom-DatabricksLogs_CL?api-version=2023-01-01"
        events_endpoint = f"{dce_endpoint}/dataCollectionRules/{common_params['dcr_immutable_id']}/streams/Custom-DatabricksEvents_CL?api-version=2023-01-01"

    common_params["endpoints"] = {
        "metrics": metrics_endpoint,
        "logs": logs_endpoint,
        "events": events_endpoint
    }

    return common_params


def unix_to_iso(timestamp: int) -> str:
    """Convert Unix timestamp in milliseconds/seconds to ISO format string."""
    ts = float(timestamp)
    # If timestamp is unusually large, assume milliseconds
    if ts > 1e12:
        ts /= 1000
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")

def timestamp_in_unix_milliseconds(timestamp) -> int:
    """Convert datetime to Unix timestamp in milliseconds."""
    if isinstance(timestamp, datetime):
        return int(timestamp.timestamp() * 1000)
    return int(timestamp)

def get_status(status_display: str) -> str:
    """Map pipeline status to appropriate status level."""
    status_lower = status_display.lower()
    if status_lower in ['failed', 'error']:
        return 'error'
    elif status_lower in ['running', 'starting']:
        return 'info'
    elif status_lower in ['completed', 'success']:
        return 'ok'
    else:
        return 'warn'

def serialize_datetime(data):
    if isinstance(data, dict):
        return {
            key: serialize_datetime(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [serialize_datetime(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data

def filter_null_fields(data):
    if isinstance(data, dict):
        return {
            key: filter_null_fields(value)
            for key, value in data.items()
            if value is not None
        }
    elif isinstance(data, list):
        return [filter_null_fields(item) for item in data if item is not None]
    else:
        return data

def enforce_schema(data, schema, path = "root"):
    # Nothing to enforce.
    if schema is None or data is None:
        return data


    schema_type = schema.get("type")
    if not schema_type:
        raise ValueError(f"Failed to get type of the object at {path}.")

    # Validate dictionary
    if isinstance(data, dict):
        if schema_type != "object":
            raise ValueError(f"Expected object at {path}, got {type(data).__name__}")
        props = schema.get("properties", {})
        required_keys = schema.get("required", [])
        additional_properties = schema.get("additionalProperties", False)

        # Validate defined properties
        for k, v in props.items():
            if k in data:
                data[k] = enforce_schema(data[k], v, f"{path}.{k}")
            elif k in required_keys:
                raise ValueError(f"Missing required field '{k}' at {path}")

        # Handle additional properties
        for k, v in data.items():
            if k not in props:  # This is an additional property
                if additional_properties is False:
                    raise ValueError(f"Additional property '{k}' not allowed at {path}")
                elif additional_properties is True:
                    # Allow any additional property, no validation
                    pass
                elif isinstance(additional_properties, dict):
                    # Handle oneOf for additional properties
                    if "oneOf" in additional_properties:
                        type_map = {
                            "string": str,
                            "number": (int, float),
                            "integer": int,
                            "boolean": bool,
                        }

                        for sub_schema in additional_properties["oneOf"]:
                            expected_type = type_map.get(sub_schema.get("type"))
                            if expected_type and isinstance(v, expected_type):
                                data[k] = enforce_schema(v, sub_schema, f"{path}.{k}")
                                break
                        else:
                            raise ValueError(
                                f"Additional property '{k}' at {path} does not match any oneOf schema"
                            )
                    else:
                        data[k] = enforce_schema(v, additional_properties, f"{path}.{k}")

        return data

    # Validate list
    elif isinstance(data, list):
        if schema_type != "array":
            raise ValueError(f"Expected array at {path}, got {type(data).__name__}")
        items_schema = schema.get("items", {})
        return [enforce_schema(item, items_schema, f"{path}[{i}]") for i, item in enumerate(data)]

    # Handle string
    elif isinstance(data, str):
        if schema_type != "string":
            raise ValueError(f"Expected string at {path}, got {type(data).__name__}")
        acceptable_values = schema.get("enum", [])
        if acceptable_values and data not in acceptable_values:
            raise ValueError(f"Invalid value at {path}: {data}. Allowed: {acceptable_values}")
        max_length = schema.get("maxLength")
        if max_length and len(data) > max_length:
            return data[:max_length]
        return data

    # Handle datetime
    elif isinstance(data, datetime):
        if schema_type == "string":
            return data.isoformat()
        elif schema_type == "integer":
            return data.timestamp()
        else:
            raise ValueError(f"Cannot convert datetime to {schema_type}")

    # Handle integer
    elif isinstance(data, int):
        if schema_type == "integer":
            return data
        elif schema_type == "number":
            return float(data)
        elif schema_type == "string" and schema.get("format") == "date-time":
            return unix_to_iso(data)
        else:
            raise ValueError(f"Cannot convert integer to {schema_type}")

    elif isinstance(data, float):
        if schema_type != "number":
            raise ValueError(f"Expected number at {path}, got {type(data).__name__}")
        return data
    elif isinstance(data, bool):
        if schema_type != "boolean":
            raise ValueError(f"Expected boolean at {path}, got {type(data).__name__}")
        return data
    return data

def create_valid_json_or_fail_with_error(data, schema):
    data = serialize_datetime(data)
    data = filter_null_fields(data)
    data = enforce_schema(data, schema)
    return json.dumps(data)

# ================================================================================
#  HTTP Layer
# ================================================================================

# Global session for connection pooling
session: Optional[requests.Session] = None

class HTTPClient:
    """
    HTTP client for batched POST requests using a persistent session.

    Input: Spark DataFrame with columns:
        - endpoint (StringType): Target URL.
        - header (StringType, JSON-encoded): HTTP headers.
        - payload (binary data): Serialized request body.
    """

    def __init__(self, max_retry_duration_sec: int = 300, request_timeout_sec: int = 30):
        """
        Initialize the HTTP client.

        Args:
            max_retry_duration_sec: Maximum time in seconds to retry requests with exponential backoff
            request_timeout_sec: Timeout in seconds for a single request
        """
        self.max_retry_duration_sec = max_retry_duration_sec
        self.request_timeout_sec = request_timeout_sec


    def get_session(self) -> requests.Session:
        """
        Get the global session instance. If not present, create a new one.

        Returns:
            session: The global session instance
        """
        global session
        if session is None:
            session = requests.Session()
        return session

    def _make_request_with_retry(self, url: str, headers: Dict[str, str], payload: bytes):
        """
        Make a POST request to the provided url.

        Args:
            url: The endpoint URL
            headers: Request headers
            payload: Request payload

        Throws:
            Exception: If the request fails and the retries are exhausted.
        """
        # Compress payload
        compressed_payload = gzip.compress(payload)
        headers['Content-Encoding'] = 'gzip'

        response = None
        try:
            response = self.get_session().post(
                url,
                headers=headers,
                data=compressed_payload,
                timeout=self.request_timeout_sec
            )
            response.raise_for_status()
            print(f"Successfully sent request to URL: {url}, Payload: {payload.decode('utf-8')}, Response: {response.text}")
        except Exception as e:
            response_text = "No response"
            if response is not None:
                try:
                    response_text = str(response.json())
                except:
                    response_text = response.text if hasattr(response, 'text') else "Unable to read response"
            print(f"Request failed for URL: {url}, headers: {str(headers)}, Payload: {payload.decode('utf-8')}, Error: {str(e)}, Response: {response_text}")
            raise type(e)(f"Request failed for URL: {url}, headers: {str(headers)}, Payload: {payload.decode('utf-8')}, Error: {str(e)}, Response: {response_text}") from e

    def post(self, http_request_specs_df) -> None:
        """
        Make POST requests for each row in the DataFrame.
        Serially makes requests for each row in the DataFrame.

        Args:
            http_request_specs_df: Spark DataFrame with columns 'endpoint', 'header', 'payloadBytes'
        """

        for row in http_request_specs_df.collect():
            try:
                headers = json.loads(getattr(row, 'header', '{}'))
                retry_wrapper = retry(
                    stop=stop_after_delay(self.max_retry_duration_sec),
                    wait=wait_exponential(multiplier=1, min=1, max=10),
                    reraise=True
                )
                retry_wrapper(self._make_request_with_retry)(row.endpoint, headers, row.payloadBytes)
            except Exception as e:
                print(f"ERROR: {str(e)}")
                continue # Continue with other requests regardless of success/failure


# ================================================================================
#  CONVERSION LAYER
# ================================================================================

class AzureMonitorMetricsConverter:
    """Converter class to convert metrics to Azure Monitor format."""

    def create_metric(
        self,
        metric_name: str,
        metric_value: float,
        tags: Dict[str, str],
        timestamp: int,
        additional_attributes: Optional[Dict[str, Any]] = None) -> str:
        """Create an Azure Monitor metric in the proper format.

        Args:
            metric_name: Name of the metric (e.g., "pipeline.run.execution_time_seconds")
            metric_value: Numeric value for the gauge metric
            tags: Dictionary of tags (e.g., {"pipeline_id": "123", "phase": "execution"})
            timestamp: Unix timestamp in milliseconds for the metric
            additional_attributes: Optional additional attributes to include

        Returns:
            JSON string representing the Azure Monitor metric

        Raises:
            ValueError if the fields are of unsupported types.
        """
        # Enforce the schema
        return create_valid_json_or_fail_with_error({
            "TimeGenerated": unix_to_iso(timestamp),
            "metric_name": metric_name,
            "metric_value": metric_value,
            "tags": tags,
            "timestamp": timestamp,
            "additional_attributes": additional_attributes
        }, METRICS_SCHEMA)

    def create_http_requests_spec(self, df, num_rows_per_batch: int, headers: dict, endpoint: str):
        """Create HTTP request spec DataFrame for metrics."""
        df_with_batch_id = df.withColumn("batch_id",
                                       expr(f"int((row_number() over (order by 1) - 1) / {num_rows_per_batch})")) \
            .withColumn("metrics", regexp_replace(col("metrics"), "\n", ""))
        return df_with_batch_id.groupBy("batch_id") \
            .agg(collect_list("metrics").alias("batch_metrics")) \
            .withColumn("payload", concat(lit('['),
                                        expr("concat_ws(',', batch_metrics)"),
                                        lit(']'))) \
            .withColumn("payloadBytes", col("payload").cast("binary")) \
            .withColumn("endpoint", lit(endpoint)) \
            .withColumn("header", lit(json.dumps(headers))) \
            .select("endpoint", "header", "payloadBytes")


class AzureMonitorEventsConverter:
    """Converter class to convert events to Azure Monitor format."""

    def create_event(
        self,
        message: str,
        status: str,
        tags: Dict[str, str],
        timestamp: int,
        additional_attributes: Optional[Dict[str, Any]] = None) -> str:
        """
        Create an Azure Monitor event in the proper format.

        Args:
            message: The event message
            status: The status of the event (e.g., "success", "error", "warning")
            tags: Dictionary of tags
            timestamp: Unix timestamp in milliseconds for the event
            additional_attributes: Optional additional attributes to include

        Returns:
            JSON string representing the Azure Monitor event

        Raises:
            ValueError if the fields are of unsupported types.
        """
        return create_valid_json_or_fail_with_error({
            "TimeGenerated": unix_to_iso(timestamp),
            "message": message,
            "status": status,
            "tags": tags,
            "timestamp": timestamp,
            "additional_attributes": additional_attributes,
        }, EVENTS_SCHEMA)

    def create_http_requests_spec(self, df, num_rows_per_batch: int, headers: dict, endpoint: str):
        """Create HTTP request spec DataFrame for events."""
        df_with_batch_id = df.withColumn("batch_id",
                                       expr(f"int((row_number() over (order by 1) - 1) / {num_rows_per_batch})")) \
            .withColumn("events", regexp_replace(col("events"), "\n", ""))
        return df_with_batch_id.groupBy("batch_id") \
            .agg(collect_list("events").alias("batch_events")) \
            .withColumn("payload", concat(lit('['),
                                        expr("concat_ws(',', batch_events)"),
                                        lit(']'))) \
            .withColumn("payloadBytes", col("payload").cast("binary")) \
            .withColumn("endpoint", lit(endpoint)) \
            .withColumn("header", lit(json.dumps(headers))) \
            .select("endpoint", "header", "payloadBytes")

class AzureMonitorLogsConverter:
    """Converter class to convert logs to Azure Monitor format."""

    def create_log(
        self,
        message: str,
        status: str,
        tags: Dict[str, str],
        timestamp: int,
        additional_attributes: Optional[Dict[str, Any]] = None) -> str:
        """
        Create an Azure Monitor log in the proper format.

        Args:
            message: The log message
            status: The status of the log (e.g., "error", "info", "warning")
            tags: Dictionary of tags
            timestamp: Unix timestamp in milliseconds for the log
            additional_attributes: Optional additional attributes to include

        Returns:
            JSON string representing the Azure Monitor log

        Raises:
            ValueError if the fields are of unsupported types.
        """
        return create_valid_json_or_fail_with_error({
            "TimeGenerated": unix_to_iso(timestamp),
            "message": message,
            "status": status,
            "tags": tags,
            "timestamp": timestamp,
            "additional_attributes": additional_attributes,
        }, LOGS_SCHEMA)

    def create_http_requests_spec(self, df, num_rows_per_batch: int, headers: dict, endpoint: str):
        """Create HTTP request spec DataFrame for logs."""
        df_with_batch_id = df.withColumn("batch_id",
                                       expr(f"int((row_number() over (order by 1) - 1) / {num_rows_per_batch})")) \
            .withColumn("logs", regexp_replace(col("logs"), "\n", ""))
        return df_with_batch_id.groupBy("batch_id") \
            .agg(collect_list("logs").alias("batch_logs")) \
            .withColumn("payload", concat(lit('['),
                                        expr("concat_ws(',', batch_logs)"),
                                        lit(']'))) \
            .withColumn("payloadBytes", col("payload").cast("binary")) \
            .withColumn("endpoint", lit(endpoint)) \
            .withColumn("header", lit(json.dumps(headers))) \
            .select("endpoint", "header", "payloadBytes")

# ================================================================================
#  INFERENCE LAYER
# ================================================================================

def convert_row_to_error_log(row):
    """Convert a row to error log format."""
    params = {
        "message": str(getattr(row, "message", "")),
        "status": "error",
        "tags": {
            "pipeline_id": getattr(row, 'pipeline_id', ''),
            "pipeline_run_id": getattr(row, 'pipeline_run_id', ''),
            "table_name": getattr(row, 'table_name', ''),
            "flow_name": getattr(row, 'flow_name', ''),
            "level": "error"
        },
        "timestamp": timestamp_in_unix_milliseconds(row.event_timestamp),
        "additional_attributes": {
            "pipeline_run_link": getattr(row, "pipeline_run_link", None),
            "error": getattr(row, "error", None),
        }
    }
    return _log_converter.create_log(**params)

def convert_row_to_table_metrics(row):
    """Convert a row to table metrics format."""
    # Base tags for all metrics
    base_tags = {
        "pipeline_id": getattr(row, "pipeline_id", ""),
        "pipeline_run_id": getattr(row, "pipeline_run_id", ""),
        "table_name": getattr(row, "table_name", ""),
        "flow_name": getattr(row, "flow_name", ""),
        "source": SOURCE_NAME
    }

    # Timestamp for all metrics
    timestamp = timestamp_in_unix_milliseconds(row.event_timestamp)

    return [
        _metrics_converter.create_metric(
            metric_name="dlt.table.throughput.upserted_rows",
            metric_value=getattr(row, "num_upserted_rows", 0) or 0,
            tags={**base_tags, "metric_type": "count"},
            timestamp=timestamp,
            additional_attributes={}
        ),
        _metrics_converter.create_metric(
            metric_name="dlt.table.throughput.deleted_rows",
            metric_value=getattr(row, "num_deleted_rows", 0) or 0,
            tags={**base_tags, "metric_type": "count"},
            timestamp=timestamp,
            additional_attributes={}
        ),
        _metrics_converter.create_metric(
            metric_name="dlt.table.throughput.output_rows",
            metric_value=getattr(row, "num_output_rows", 0) or 0,
            tags={**base_tags, "metric_type": "count"},
            timestamp=timestamp,
            additional_attributes={}
        ),
    ]

def convert_row_to_pipeline_status_event(row):
    """Convert a row to pipeline status event format."""
    # Determine pipeline status for message
    status_display = row.latest_state.upper() if row.latest_state else 'UNKNOWN'
    pipeline_id = getattr(row, "pipeline_id", "")

    params = {
        "message": f"Pipeline {pipeline_id} {status_display}",
        "status": get_status(status_display),
        "tags": {
            "pipeline_id": pipeline_id,
            "latest_run_id": getattr(row, "pipeline_run_id", ""),
            "status": status_display.lower(),
            "source": SOURCE_NAME,
            "service": SERVICE_NAME
        },
        "timestamp": timestamp_in_unix_milliseconds(row.updated_at),
        "additional_attributes": {
            "pipeline_link": getattr(row, "pipeline_link", None),
            "pipeline_run_link": getattr(row, "pipeline_run_link", None),
            "is_complete": getattr(row, "is_complete", None),
            "running_start_time": getattr(row, "running_start_time", None),
            "end_time": getattr(row, "end_time", None),
            "updated_at": getattr(row, "updated_at", None) ,
            "latest_error_log_message": getattr(row, "latest_error_log_message", None),
            "latest_error_message": getattr(row, "latest_error_message", None),
        }
    }
    return _events_converter.create_event(**params)

def convert_row_to_pipeline_metrics(row):
    """Convert a row to pipeline metrics format."""
    def has_attr(obj, attr):
        return hasattr(obj, attr) and getattr(obj, attr) is not None

    if not has_attr(row, "queued_time") or not has_attr(row, "create_time"):
        return []

    base_tags = {
        "pipeline_id": getattr(row, "pipeline_id", ""),
        "pipeline_run_id": getattr(row, "pipeline_run_id", ""),
        "source": SOURCE_NAME
    }
    metrics = []
    timestamp = timestamp_in_unix_milliseconds(getattr(row, "create_time", None))

    end_time = getattr(row, "end_time", None) or datetime.now(timezone.utc)

    # Starting seconds: queued_time - create_time
    starting_seconds = (row.queued_time - row.create_time).total_seconds()
    metrics.append(_metrics_converter.create_metric(
        metric_name="pipeline.run.starting_seconds",
        metric_value=starting_seconds,
        tags={**base_tags, "metric_type": "duration", "phase": "starting"},
        timestamp=timestamp
    ))

    # Seconds waiting for resources: initialization_start_time - queued_time
    if not has_attr(row, "initialization_start_time"):
        return metrics
    waiting_seconds = (row.initialization_start_time - row.queued_time).total_seconds()
    metrics.append(_metrics_converter.create_metric(
        metric_name="pipeline.run.waiting_for_resources_seconds",
        metric_value=waiting_seconds,
        tags={**base_tags, "metric_type": "duration", "phase": "waiting"},
        timestamp=timestamp
    ))

    # Initialization seconds: running_start_time - initialization_start_time
    if not has_attr(row, "running_start_time"):
        return metrics
    initialization_seconds = (row.running_start_time - row.initialization_start_time).total_seconds()
    metrics.append(_metrics_converter.create_metric(
        metric_name="pipeline.run.initialization_seconds",
        metric_value=initialization_seconds,
        tags={**base_tags, "metric_type": "duration", "phase": "initialization"},
        timestamp=timestamp
    ))

    # Running seconds: end_time - running_start_time
    running_seconds = (end_time - row.running_start_time).total_seconds()
    metrics.append(_metrics_converter.create_metric(
        metric_name="pipeline.run.running_seconds",
        metric_value=running_seconds,
        tags={**base_tags, "metric_type": "duration", "phase": "running"},
        timestamp=timestamp
    ))

    # Total seconds: end_time - create_time
    total_seconds = (end_time - row.create_time).total_seconds()
    metrics.append(_metrics_converter.create_metric(
        metric_name="pipeline.run.total_seconds",
        metric_value=total_seconds,
        tags={**base_tags, "metric_type": "duration", "phase": "total"},
        timestamp=timestamp
    ))

    return metrics

# ================================================================================
#  MAIN
# ================================================================================

# Source streams
event_logs_bronze = "event_logs_bronze"
pipeline_runs_status = "pipeline_runs_status"


http_client = None
def getClient(config):
    """Global HTTP client getter."""
    global http_client
    if http_client is None:
        http_client = HTTPClient(
            max_retry_duration_sec=config["max_retry_duration_sec"],
            request_timeout_sec=config["request_timeout_sec"]
        )
    return http_client



token_details = {
    "access_token": None,
    "last_load_timestamp": 0
}
token_lock = threading.Lock()

def get_access_token(config):
    global token_details
    now = int(datetime.now(timezone.utc).timestamp())
    if ((now - token_details["last_load_timestamp"]) < config["max_access_token_staleness"]):
        return token_details["access_token"]

    # Token does not exist or is stale, fetch a new one.
    with token_lock:
        if token_details["access_token"] is None or (now - token_details["last_load_timestamp"]) >= config["max_access_token_staleness"]:
            token_details = fetch_access_token(config)
    return token_details["access_token"]


def register_sink_for_pipeline_events():
    @dlt.foreach_batch_sink(name="send_pipeline_status_to_3p_monitoring")
    def send_pipeline_status_to_3p_monitoring(batch_df, batch_id):
        destination_format_udf = udf(convert_row_to_pipeline_status_event, StringType())
        events_df = batch_df.withColumn("events", destination_format_udf(struct("*"))).select("events").filter(col("events").isNotNull())
        http_request_spec = _events_converter.create_http_requests_spec(
            events_df,
            _global_config["num_rows_per_batch"],
            get_azure_header(get_access_token(_global_config)),
            _global_config["endpoints"]["events"]
        )
        getClient(_global_config).post(http_request_spec)

    @dlt.append_flow(target="send_pipeline_status_to_3p_monitoring")
    def send_pipeline_status_to_sink():
        return spark.readStream.table(f"{pipeline_runs_status}_cdf")


def register_sink_for_errors():
    @dlt.foreach_batch_sink(name="send_errors_to_3p_monitoring")
    def send_errors_to_3p_monitoring(batch_df, batch_id):
        destination_format_udf = udf(convert_row_to_error_log, StringType())
        logs_df = batch_df.withColumn("logs", destination_format_udf(struct("*"))).select("logs").filter(col("logs").isNotNull())
        http_request_spec = _log_converter.create_http_requests_spec(
            logs_df,
            _global_config["num_rows_per_batch"],
            get_azure_header(get_access_token(_global_config)),
            _global_config["endpoints"]["logs"]
        )
        getClient(_global_config).post(http_request_spec)

    @dlt.append_flow(target="send_errors_to_3p_monitoring")
    def send_errors_to_sink():
        return spark.readStream.option("skipChangeCommits", "true").table(event_logs_bronze).filter("error IS NOT NULL OR level = 'ERROR'")

def register_sink_for_pipeline_metrics():
    @dlt.foreach_batch_sink(name="send_pipeline_metrics_to_3p_monitoring")
    def send_pipeline_metrics_to_3p_monitoring(batch_df, batch_id):
        destination_format_udf = udf(convert_row_to_pipeline_metrics, ArrayType(StringType()))
        metrics_df = batch_df.withColumn("metrics_array", destination_format_udf(struct("*"))).select(explode("metrics_array").alias("metrics")).filter(col("metrics").isNotNull())
        http_request_spec = _metrics_converter.create_http_requests_spec(
            metrics_df,
            _global_config["num_rows_per_batch"],
            get_azure_header(get_access_token(_global_config)),
            _global_config["endpoints"]["metrics"]
        )
        getClient(_global_config).post(http_request_spec)

    @dlt.append_flow(target="send_pipeline_metrics_to_3p_monitoring")
    def send_pipeline_metrics_to_sink():
        return spark.readStream.table(f"{pipeline_runs_status}_cdf")

def register_sink_for_table_metrics():
    @dlt.foreach_batch_sink(name="send_table_metrics_to_3p_monitoring")
    def send_table_metrics_to_3p_monitoring(batch_df, batch_id):
        destination_format_udf = udf(convert_row_to_table_metrics, ArrayType(StringType()))
        metrics_df = batch_df.withColumn("metrics_array", destination_format_udf(struct("*"))).select(explode("metrics_array").alias("metrics")).filter(col("metrics").isNotNull())
        http_request_spec = _metrics_converter.create_http_requests_spec(
            metrics_df,
            _global_config["num_rows_per_batch"],
            get_azure_header(get_access_token(_global_config)),
            _global_config["endpoints"]["metrics"]
        )
        getClient(_global_config).post(http_request_spec)

    @dlt.append_flow(target="send_table_metrics_to_3p_monitoring")
    def send_table_metrics_to_sink():
        return spark.readStream.option("skipChangeCommits", "true").table(event_logs_bronze) \
            .filter("table_name is not null AND details:flow_progress.metrics is not null AND event_type = 'flow_progress'") \
            .selectExpr(
            "pipeline_id",
            "pipeline_run_id",
            "table_name",
            "flow_name",
            "event_timestamp",
            "details:flow_progress.metrics.num_upserted_rows::bigint as num_upserted_rows",
            "details:flow_progress.metrics.num_deleted_rows::bigint as num_deleted_rows",
            "(details:flow_progress.metrics.num_upserted_rows::bigint + details:flow_progress.metrics.num_deleted_rows::bigint) as num_output_rows"
        ) \
            .filter("num_upserted_rows is not null OR num_deleted_rows is not null OR num_output_rows is not null")


# ================================================================================
#  MAIN INITIALIZATION
# ================================================================================

# Initialize global configuration and register sinks.
if getParam(spark.conf, "destination") == "azuremonitor":
    initialize_global_config(spark.conf)
    register_sink_for_errors()
    register_sink_for_pipeline_events()
    register_sink_for_table_metrics()
    register_sink_for_pipeline_metrics()