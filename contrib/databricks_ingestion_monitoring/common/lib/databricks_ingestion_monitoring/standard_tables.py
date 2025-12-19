from enum import Enum
import logging
from typing import Dict, Optional

from pyspark.sql import SparkSession, DataFrame


class TableType(Enum):
    STREAMING_TABLE = 1
    MATERIALIZED_VIEW = 2
    DELTA_TABLE = 3


class MonitoringTable:
    """
    A helper class that encapsulates logic to generate a monitoring table. All tables are generated within the
    default catalog and schema for the pipeline.
    """

    def __init__(
        self,
        name: str,
        table_type: TableType,
        table_comment: str,
        column_comments: Optional[Dict[str, str]] = None,
    ):
        """
        Constructor
        :param name: the name of the table
        :param type: 'st' or 'mv'
        """
        self.name = name
        self.table_type = table_type
        self.table_comment = table_comment
        self.column_comments = column_comments
        self.log = logging.getLogger(
            f"databricks_ingestion_monitoring.MonitoringTable.{self.name}"
        )

    def add_column_comments(
        self, monitoring_catalog: str, monitoring_schema: str, spark: SparkSession
    ):
        """
        Add comments to the columns of the table. This is a workaround because SDP currently does not support
        adding those as part of the table definition. This method will use ALTER TABLE ALTER COLUMN ... COMMENT ...
        to set the comments on the intersection of the keys of `self.column_comments` and the columns from the
        table schema.
        """
        if self.column_comments is None or len(self.column_comments) == 0:
            return  # Nothing to do

        self.log.info(f"Adding column comments to table {self.name}")
        fq_name = f"`{monitoring_catalog}`.`{monitoring_schema}`.`{self.name}`"

        if not spark.catalog.tableExists(fq_name):
            self.log.warn(f"Table {fq_name} does not exist. Skipping column comments.")
            return

        table_schema = spark.table(fq_name).schema
        table_column_names = set(table_schema.fieldNames())

        if TableType.STREAMING_TABLE == self.table_type:
            alter_type = "STREAMING TABLE"
        elif TableType.MATERIALIZED_VIEW == self.table_type:
            alter_type = "MATERIALIZED VIEW"
        elif TableType.DELTA_TABLE == self.table_type:
            alter_type = "TABLE"
        else:
            raise AssertionError(f"Unexpected table_type: {self.table_type}")

        for column_name, column_comment in self.column_comments.items():
            if column_name in table_column_names:
                column_comment_parts = column_comment.splitlines()
                comment_sql = " ".join(
                    [p.replace("'", "''") for p in column_comment_parts]
                )
                sql = f"ALTER {alter_type} {fq_name} ALTER COLUMN `{column_name}` COMMENT '{comment_sql}'"
                self.log.debug(f"Running {sql} ...")
                spark.sql(sql)
            else:
                self.log.warn(f"Column {column_name} not found in table {self.name}")


STANDARD_COLUMN_COMMENTS = {
    "error_full": "Contains full details about the error that happened (if any)",
    "error_message": "Short human-readable message describing the error (if any)",
    "event_timestamp": "When this event occurred",
    "flow_name": "The name of the flow (if any) that triggered this event",
    "level": "The severity level of this event, one of: INFO, WARN, ERROR",
    "message": "A human-readable message about the contents of this event",
    "pipeline_id": "The unique identifier of the monitored pipeline",
    "pipeline_link": "An HTML-formated link to the pipeline in the current workspace. Useful in dashboards.",
    "pipeline_name": "The name of the monitored pipeline",
    "pipeline_run_id": "The unique identifier of a specific pipeline run (update)",
    "pipeline_run_link": "An HTML-formated link to the pipeline run in the current workspace. Useful in dashboards.",
    "table_name": "Fully qualified replication target table name",
    "latest_state": """The latest known state of the %s pipeline run. Can be one of: 
        QUEUED, CREATED, WAITING_FOR_RESOURCES, INITIALIZING, RESETTING, SETTING_UP_TABLES, 
        RUNNING, STOPPING, COMPLETED, FAILED, CANCELED""",
    "state_color": "A helper color associated with the current state of the %s pipeline run",
    "latest_state_with_color": "An HTML-formated string for %s pipeline run state. Useful in dashboards.",
    "latest_state_level": """An integer that represents higher level of the %s pipeline run state progress 
        or severity if the pipeline run has finished.""",
    "create_time": "Time when the %s pipeline run was created",
    "end_time": "Time when the %s pipeline run finished its execution (entered COMPLETED, FAILED, CANCELED state)",
    "is_complete": "If the %s pipeline run state is a final state -- COMPLETED, FAILED, CANCELED",
    "latest_error_log_message": "Latest event log message in the %s pipeline run with ERROR level",
    "latest_error_message": "Short description of the latest error (exception) message in the %s pipeline run",
    "latest_error_code": "The error code (if any) of the latest error (exception) in the %s pipeline run",
    "flow_type": "The logical type of the flow in the CDC Connector: 'cdc', 'snapshot', 'cdc_staging'",
    "latest_table_state": """The latest state of a flow (writing to the target table). Can be: 
          QUEUED, STARTING, RUNNING, COMPLETED, FAILED, SKIPPED, STOPPED, IDLE, EXCLUDED""",
    "latest_table_state_level": """An integer that represents higher level of the table state progress 
          or severity if the table processing has finished.""",
    "latest_table_state_color": "A color associated with the latest state",
    "latest_table_state_with_color": "An HTML-formated string with the latest state; useful in dashboards.",
    "table_schema_json": "The schema of the target table in %s pipeline run as a JSON string",
    "table_schema": "A list of schema information for each column in the target table in %s pipeline run",
    "latest_table_error_time": "The time of the latest observed error in %s pipeline run for this table (if any)",
    "latest_table_error_log_message": "The message in the event log for an error for this target table in %s pipeline run (if any)",
    "latest_table_error_message": "The latest error message for the target table in %s pipeline run (if any)",
    "latest_table_error_full": "Error details for the latest error for the target table in %s pipeline run (if any)",
}


MONITORED_PIPELINES = MonitoringTable(
    name="monitored_pipelines",
    table_type=TableType.MATERIALIZED_VIEW,
    table_comment="Contains metadata about all monitored pipelines.",
    column_comments={
        "pipeline_id": STANDARD_COLUMN_COMMENTS["pipeline_id"],
        "pipeline_name": STANDARD_COLUMN_COMMENTS["pipeline_name"],
        "pipeline_link": STANDARD_COLUMN_COMMENTS["pipeline_link"],
        "pipeline_type": """One of: 'gateway' for CDC Connector gateways, 'ingestion' for other ingestion pipelines,
          'etl' for all other pipelines""",
        "default_catalog": "The default catalog for the pipeline",
        "default_schema": "The default schema for the pipeline",
        "event_log_source": """The fully qualified name to a Delta table containing the event log for this pipeline.
          This could be the Delta table explicitly configured in the 'event_log' property of the pipeline spec or
          a table where that log has been imported using the import_event_logs job.""",
        "tags_map": "A map of tag keys to tag values for this pipeline. Useful for filtering and grouping pipelines by tags.",
        "tags_array": """An array of 'tag:value' strings for this pipeline. Designed for easy filtering in AI/BI dashboards
          where you can select a single value as a filtering expression.""",
    },
)

MONITORED_TABLES = MonitoringTable(
    name="monitored_tables",
    table_type=TableType.MATERIALIZED_VIEW,
    table_comment="Contains a list of all tables detected in monitored pipelines. Used in the observability dashboard for filtering by table.",
    column_comments={
        "pipeline_id": STANDARD_COLUMN_COMMENTS["pipeline_id"],
        "table_name": STANDARD_COLUMN_COMMENTS["table_name"],
    },
)

EVENT_LOGS_BRONZE = MonitoringTable(
    name="event_logs_bronze",
    table_type=TableType.STREAMING_TABLE,
    table_comment="Initial filtering and transformations of the input event logs that are shared by most observability tables",
    column_comments={
        "id": "This event's unique identifier",
        "seq_num": "Contains information about the position of this event in the event log",
        "pipeline_id": "The unique identifier of the pipeline for which this event is",
        "pipeline_run_id": STANDARD_COLUMN_COMMENTS["pipeline_run_id"],
        "pipeline_run_link": STANDARD_COLUMN_COMMENTS["pipeline_run_link"],
        "table_name": STANDARD_COLUMN_COMMENTS["table_name"],
        "flow_name": STANDARD_COLUMN_COMMENTS["flow_name"],
        "batch_id": "The micro-batch id that triggered this event (typically used in metric events)",
        "event_timestamp": STANDARD_COLUMN_COMMENTS["event_timestamp"],
        "message": STANDARD_COLUMN_COMMENTS["message"],
        "level": STANDARD_COLUMN_COMMENTS["level"],
        "error_message": STANDARD_COLUMN_COMMENTS["error_message"],
        "error_full": STANDARD_COLUMN_COMMENTS["error_full"],
        "event_type": """The type of the event. For example 'update_progress' captures state transitions for the current
        pipeline run, 'flow_progress' captures state transition in the evaluation of a specific flow, etc. Look for
        more information in   `details`:<event_type>
        """,
        "details": "Contains `event_type`-specific information in the <event_type> field.",
    },
)

PIPELINE_RUNS_STATUS = MonitoringTable(
    name="pipeline_runs_status",
    table_type=TableType.STREAMING_TABLE,
    table_comment="Contains the latest status of monitored pipelines runs",
    column_comments={
        "pipeline_id": STANDARD_COLUMN_COMMENTS["pipeline_id"],
        "pipeline_run_id": STANDARD_COLUMN_COMMENTS["pipeline_run_id"],
        "pipeline_run_link": STANDARD_COLUMN_COMMENTS["pipeline_run_link"],
        "latest_state": STANDARD_COLUMN_COMMENTS["latest_state"] % (""),
        "state_color": STANDARD_COLUMN_COMMENTS["state_color"] % (""),
        "latest_state_with_color": STANDARD_COLUMN_COMMENTS["latest_state_with_color"]
        % (""),
        "latest_state_level": STANDARD_COLUMN_COMMENTS["latest_state_level"] % (""),
        "create_time": STANDARD_COLUMN_COMMENTS["create_time"] % (""),
        "queued_time": "Time when the pipeline run was queued for compute resources (entered WAITING_FOR_RESOURCES state)",
        "initialization_start_time": "Time when the pipeline run started initialization (entered INITIALIZING state)",
        "running_start_time": "Time when the pipeline starting its execution (entered RUNNING state)",
        "end_time": STANDARD_COLUMN_COMMENTS["end_time"] % (""),
        "is_complete": STANDARD_COLUMN_COMMENTS["is_complete"] % (""),
        "latest_error_log_message": STANDARD_COLUMN_COMMENTS["latest_error_log_message"]
        % (""),
        "latest_error_message": STANDARD_COLUMN_COMMENTS["latest_error_message"] % (""),
        "latest_error_code": STANDARD_COLUMN_COMMENTS["latest_error_code"] % (""),
        "latest_error_full": "Full stack trace of the latest error in the log",
        "updated_at": "Timestamp of latest update (based on the event log timestamp) applied to this row",
    },
)

EVENTS_ERRORS = MonitoringTable(
    name="events_errors",
    table_type=TableType.STREAMING_TABLE,
    table_comment="The stream of all errors in pipeline runs",
    column_comments={
        "pipeline_id": STANDARD_COLUMN_COMMENTS["pipeline_id"],
        "pipeline_run_id": STANDARD_COLUMN_COMMENTS["pipeline_run_id"],
        "pipeline_run_link": STANDARD_COLUMN_COMMENTS["pipeline_run_link"],
        "table_name": STANDARD_COLUMN_COMMENTS["table_name"]
        + " affected by the error (if any)",
        "flow_name": STANDARD_COLUMN_COMMENTS["flow_name"],
        "event_timestamp": STANDARD_COLUMN_COMMENTS["event_timestamp"],
        "error_log_message": STANDARD_COLUMN_COMMENTS["message"],
        "error_message": STANDARD_COLUMN_COMMENTS["error_message"],
        "error_full": STANDARD_COLUMN_COMMENTS["error_full"],
        "flow_type": STANDARD_COLUMN_COMMENTS["flow_type"],
    },
)

EVENTS_WARNINGS = MonitoringTable(
    name="events_warnings",
    table_type=TableType.STREAMING_TABLE,
    table_comment="The stream of all warnings in pipeline runs",
    column_comments={
        "pipeline_id": STANDARD_COLUMN_COMMENTS["pipeline_id"],
        "pipeline_run_id": STANDARD_COLUMN_COMMENTS["pipeline_run_id"],
        "pipeline_run_link": STANDARD_COLUMN_COMMENTS["pipeline_run_link"],
        "table_name": STANDARD_COLUMN_COMMENTS["table_name"]
        + " affected by the warning (if any)",
        "flow_name": STANDARD_COLUMN_COMMENTS["flow_name"],
        "event_timestamp": STANDARD_COLUMN_COMMENTS["event_timestamp"],
        "warning_log_message": STANDARD_COLUMN_COMMENTS["message"],
        "flow_type": STANDARD_COLUMN_COMMENTS["flow_type"],
    },
)

METRIC_PIPELINE_HOURLY_ERROR_RATE = MonitoringTable(
    name="metric_pipeline_error_rate",
    table_type=TableType.MATERIALIZED_VIEW,
    table_comment="Error rate per hour for all monitored pipelines",
    column_comments={
        "pipeline_id": STANDARD_COLUMN_COMMENTS["pipeline_id"],
        "hour": "The hour for which the error rate is calculated",
        "error_rate": "The number of errors per hour for the pipeline",
    },
)

PIPELINES_STATUS_SILVER = MonitoringTable(
    name="pipelines_status_silver",
    table_type=TableType.STREAMING_TABLE,
    table_comment="Keeps track of the latest pipeline run, latest successful run and latest failed run for each pipeline",
    column_comments={},
)

PIPELINES_STATUS = MonitoringTable(
    name="pipelines_status",
    table_type=TableType.MATERIALIZED_VIEW,
    table_comment="Keeps track of the latests status for each monitored pipeline",
    column_comments={
        "pipeline_id": STANDARD_COLUMN_COMMENTS["pipeline_id"],
        "latest_pipeline_run_id": f"Latest {STANDARD_COLUMN_COMMENTS['pipeline_run_id']}",
        "latest_pipeline_run_link": f"Latest {STANDARD_COLUMN_COMMENTS['pipeline_run_link']}",
        "latest_pipeline_run_state": STANDARD_COLUMN_COMMENTS["latest_state"]
        % ("latest"),
        "latest_pipeline_run_state_color": STANDARD_COLUMN_COMMENTS["state_color"]
        % ("latest"),
        "latest_pipeline_run_state_with_color": STANDARD_COLUMN_COMMENTS[
            "latest_state_with_color"
        ]
        % ("latest"),
        "latest_pipeline_run_state_level": STANDARD_COLUMN_COMMENTS[
            "latest_state_level"
        ]
        % ("latest"),
        "latest_pipeline_run_create_time": STANDARD_COLUMN_COMMENTS["create_time"]
        % ("latest"),
        "latest_pipeline_run_end_time": STANDARD_COLUMN_COMMENTS["end_time"]
        % ("latest"),
        "latest_pipeline_run_is_complete": STANDARD_COLUMN_COMMENTS["is_complete"]
        % ("latest"),
        "latest_error_log_message": STANDARD_COLUMN_COMMENTS["latest_error_log_message"]
        % ("latest"),
        "latest_error_message": STANDARD_COLUMN_COMMENTS["latest_error_message"]
        % ("latest"),
        "latest_error_code": STANDARD_COLUMN_COMMENTS["latest_error_code"] % ("latest"),
        "latest_error_time": "The time of the latest error (event)",
        "latest_successful_run_id": f"Latest successful {STANDARD_COLUMN_COMMENTS['pipeline_run_id']}",
        "latest_successful_run_link": f"Latest successful {STANDARD_COLUMN_COMMENTS['pipeline_run_link']}",
        "latest_successful_run_create_time": STANDARD_COLUMN_COMMENTS["create_time"]
        % ("successful"),
        "latest_successful_run_end_time": STANDARD_COLUMN_COMMENTS["end_time"]
        % ("successful"),
        "latest_failed_run_id": f"Latest failed {STANDARD_COLUMN_COMMENTS['pipeline_run_id']}",
        "latest_failed_run_link": f"Latest failed {STANDARD_COLUMN_COMMENTS['pipeline_run_link']}",
        "latest_failed_run_create_time": STANDARD_COLUMN_COMMENTS["create_time"]
        % ("failed"),
        "latest_failed_run_end_time": STANDARD_COLUMN_COMMENTS["end_time"] % ("failed"),
        "latest_failed_run_error_log_message": STANDARD_COLUMN_COMMENTS[
            "latest_error_log_message"
        ]
        % ("failed"),
        "latest_failed_run_error_message": STANDARD_COLUMN_COMMENTS[
            "latest_error_message"
        ]
        % ("failed"),
        "latest_failed_run_error_code": STANDARD_COLUMN_COMMENTS["latest_error_code"]
        % ("failed"),
        "updated_at": "Timestamp of latest update (based on the event log timestamp) applied to this row",
        "latest_pipeline_run_num_errors": "The number of errors in the latest pipeline run",
        "latest_pipeline_run_num_warnings": "The number of warnings in the latest pipeline run",
    },
)

EVENTS_TABLE_METRICS = MonitoringTable(
    name="events_table_metrics",
    table_type=TableType.STREAMING_TABLE,
    table_comment="The stream of metric events to target tables",
    column_comments={
        "pipeline_id": STANDARD_COLUMN_COMMENTS["pipeline_id"],
        "pipeline_run_id": STANDARD_COLUMN_COMMENTS["pipeline_run_id"],
        "pipeline_run_link": STANDARD_COLUMN_COMMENTS["pipeline_run_link"],
        "table_name": STANDARD_COLUMN_COMMENTS["table_name"],
        "flow_name": STANDARD_COLUMN_COMMENTS["flow_name"],
        "event_timestamp": STANDARD_COLUMN_COMMENTS["event_timestamp"],
        "num_output_rows": "Number of output rows appended to the target table.",
        "backlog_bytes": "Total backlog as bytes across all input sources in the flow.",
        "backlog_records": "Total backlog records across all input sources in the flow.",
        "backlog_files": "Total backlog files across all input sources in the flow.",
        "backlog_seconds": "Maximum backlog seconds across all input sources in the flow.",
        "executor_time_ms": "Sum of all task execution times in milliseconds of this flow over the reporting period.",
        "executor_cpu_time_ms": "Sum of all task execution CPU times in milliseconds of this flow over the reporting period.",
        "num_upserted_rows": "Number of output rows upserted into the dataset by an update of this flow.",
        "num_deleted_rows": "Number of existing output rows deleted from the dataset by an update of this flow.",
        "num_output_bytes": "Number of output bytes written by an update of this flow.",
        "num_written_rows": "Total number of rows written to the target table -- combines num_output_rows, num_upserted_rows, num_deleted_rows",
        "min_event_time": "The minimum event/commit time of a row processed in the specific micro-batch",
        "max_event_time": "The maximum event/commit time of a row processed in the specific micro-batch",
        "flow_type": STANDARD_COLUMN_COMMENTS["flow_type"],
        "num_expectation_dropped_records": "The number of rows/records that were dropped due to failed DROP expectations.",
    },
)

TABLE_STATUS_PER_PIPELINE_RUN = MonitoringTable(
    name="table_status_per_pipeline_run",
    table_type=TableType.STREAMING_TABLE,
    table_comment="Keeps track of the progress of processing a specific target table in pipeline runs",
    column_comments={
        "pipeline_id": STANDARD_COLUMN_COMMENTS["pipeline_id"],
        "pipeline_run_id": STANDARD_COLUMN_COMMENTS["pipeline_run_id"],
        "pipeline_run_link": STANDARD_COLUMN_COMMENTS["pipeline_run_link"],
        "table_name": STANDARD_COLUMN_COMMENTS["table_name"],
        "updated_at": "Timestamp of latest update (based on the event log timestamp) applied to this row",
        "latest_state": STANDARD_COLUMN_COMMENTS["latest_table_state"],
        "table_schema_json": STANDARD_COLUMN_COMMENTS["table_schema_json"] % ("this"),
        "table_schema": STANDARD_COLUMN_COMMENTS["table_schema"] % ("this"),
        "latest_error_time": STANDARD_COLUMN_COMMENTS["latest_table_error_time"]
        % ("this"),
        "latest_error_log_message": STANDARD_COLUMN_COMMENTS[
            "latest_table_error_log_message"
        ]
        % ("this"),
        "latest_error_message": STANDARD_COLUMN_COMMENTS["latest_table_error_message"]
        % ("this"),
        "latest_error_full": STANDARD_COLUMN_COMMENTS["latest_table_error_full"]
        % ("this"),
        "flow_type": STANDARD_COLUMN_COMMENTS["flow_type"],
        "latest_state_level": STANDARD_COLUMN_COMMENTS["latest_table_state_level"],
        "latest_state_color": STANDARD_COLUMN_COMMENTS["latest_table_state_color"],
        "latest_state_with_color": STANDARD_COLUMN_COMMENTS[
            "latest_table_state_with_color"
        ],
    },
)

TABLE_STATUS = MonitoringTable(
    name="table_status",
    table_type=TableType.MATERIALIZED_VIEW,
    table_comment="Keeps track of the latest progress of processing a specific target table",
    column_comments={
        "pipeline_id": STANDARD_COLUMN_COMMENTS["pipeline_id"],
        "table_name": STANDARD_COLUMN_COMMENTS["table_name"],
        "latest_pipeline_run_id": f"Latest {STANDARD_COLUMN_COMMENTS['pipeline_run_id']}",
        "latest_pipeline_run_link": f"Latest {STANDARD_COLUMN_COMMENTS['pipeline_run_link']}",
        "latest_state": STANDARD_COLUMN_COMMENTS["latest_table_state"],
        "latest_state_level": STANDARD_COLUMN_COMMENTS["latest_table_state_level"],
        "latest_state_color": STANDARD_COLUMN_COMMENTS["latest_table_state_color"],
        "latest_state_with_color": STANDARD_COLUMN_COMMENTS[
            "latest_table_state_with_color"
        ],
        "latest_table_schema_json": STANDARD_COLUMN_COMMENTS["table_schema_json"]
        % ("the latest"),
        "latest_table_schema": STANDARD_COLUMN_COMMENTS["table_schema"]
        % ("the latest"),
        "latest_cdc_changes_time": "The latest time when the CDC changes were applied to the target table",
        "latest_snapshot_changes_time": "The latest time when the snapshot changes were applied to the target table",
        "latest_error_pipeline_run_id": "The pipeline run id with the latest error for the target table",
        "latest_error_pipeline_run_link": """An HTML-formatted link for the pipeline run with the latest error 
          for the target table; useful in dashboards""",
        "latest_error_time": STANDARD_COLUMN_COMMENTS["latest_table_error_time"]
        % ("a"),
        "latest_error_log_message": STANDARD_COLUMN_COMMENTS[
            "latest_table_error_log_message"
        ]
        % ("a"),
        "latest_error_message": STANDARD_COLUMN_COMMENTS["latest_table_error_message"]
        % ("a"),
        "latest_error_full": STANDARD_COLUMN_COMMENTS["latest_table_error_full"]
        % ("a"),
        "latest_error_flow_type": "The flow type ('cdc', 'snapshot') where the latest error occurred for this target table",
    },
)

TABLE_EVENTS_EXPECTATION_CHECKS = MonitoringTable(
    name="table_events_expectation_checks",
    table_type=TableType.STREAMING_TABLE,
    table_comment="Keeps track of the results of expectation checks for each pipeline run",
    column_comments={
        "pipeline_id": STANDARD_COLUMN_COMMENTS["pipeline_id"],
        "pipeline_run_id": STANDARD_COLUMN_COMMENTS["pipeline_run_id"],
        "pipeline_run_link": STANDARD_COLUMN_COMMENTS["pipeline_run_link"],
        "table_name": STANDARD_COLUMN_COMMENTS["table_name"],
        "flow_name": STANDARD_COLUMN_COMMENTS["flow_name"],
        "event_timestamp": STANDARD_COLUMN_COMMENTS["event_timestamp"],
        "expectation_name": "The name of the expectation",
        "num_passed": "The number of rows/records that passed the expectation check",
        "num_failed": "The number of rows/records that failed the expectation check",
        "failure_pct": "The percentage of rows/records that failed the expectation check",
    },
)

PIPELINE_TAGS_INDEX = MonitoringTable(
    name="pipeline_tags_index",
    table_type=TableType.DELTA_TABLE,
    table_comment="""Inverted index mapping pipeline tags to pipeline IDs for efficient tag-based pipeline discovery.
      Built and maintained by the 'Build pipeline tags index' job. Used to optimize performance when discovering
      pipelines by tags instead of querying the Databricks API for every pipeline.""",
    column_comments={
        "tag_key": "The tag key (e.g., 'env', 'team', 'critical')",
        "tag_value": "The tag value (e.g., 'prod', 'data', 'true')",
        "pipeline_ids": """Array of pipeline IDs that have this tag:value pair. Used for efficient lookup when
          discovering pipelines by tags without expensive API calls.""",
        "index_build_time": "Timestamp when this index was last built. Used to determine if the index is stale.",
    },
)


def set_all_table_column_comments(
    monitoring_catalog: str, monitoring_schema: str, spark: SparkSession
):
    for st in [
        MONITORED_PIPELINES,
        MONITORED_TABLES,
        EVENT_LOGS_BRONZE,
        PIPELINE_RUNS_STATUS,
        EVENTS_ERRORS,
        EVENTS_WARNINGS,
        METRIC_PIPELINE_HOURLY_ERROR_RATE,
        PIPELINES_STATUS_SILVER,
        PIPELINES_STATUS,
        EVENTS_TABLE_METRICS,
        TABLE_STATUS_PER_PIPELINE_RUN,
        TABLE_STATUS,
        TABLE_EVENTS_EXPECTATION_CHECKS,
        PIPELINE_TAGS_INDEX,
    ]:
        st.add_column_comments(monitoring_catalog, monitoring_schema, spark)
