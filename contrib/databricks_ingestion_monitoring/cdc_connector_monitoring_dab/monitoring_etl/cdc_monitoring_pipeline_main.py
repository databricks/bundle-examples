import dlt
import sys
import logging

from pyspark.sql import SparkSession

sys.path.append("../../common/lib")

from databricks_ingestion_monitoring.common_ldp import (
    Configuration,
    Constants,
    MonitoringEtlPipeline,
)
from databricks_ingestion_monitoring.standard_tables import (
    EVENTS_TABLE_METRICS,
    TABLE_STATUS,
    TABLE_STATUS_PER_PIPELINE_RUN,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.info("Starting CDC Connector Monitoring ETL Pipeline")

# Pipeline parameters

conf = Configuration(spark.conf)


class CdcConstants:
    CDC_FLOW_TYPE = "cdc"
    SNAPSHOT_FLOW_TYPE = "snapshot"
    CDC_STAGING_TABLE_FLOW_TYPE = "cdc_staging"
    TABLE_STATUS_PER_PIPELINE_RUN = "table_status_per_pipeline_run"
    CDC_STAGING_TABLE = "cdc_staging_table"


class CdcConnectorMonitoringEtlPipeline(MonitoringEtlPipeline):
    def __init__(self, conf: Configuration, spark: SparkSession):
        super().__init__(conf, spark)

    def _get_event_logs_bronze_sql(self, event_log_source: str):
        """
        Override base definition for append flows from the event log sources into `event_logs_bronze` table. It adds
        CDC Connector-specific fields
        """
        sql = super()._get_event_logs_bronze_sql(event_log_source)
        sql = sql.replace(
            Constants.sql_fields_def_extension_point,
            f""", (CASE WHEN endswith(flow_name, "_snapshot_flow") THEN 'snapshot'
                    WHEN details:operation_progress.cdc_snapshot.table_name::string is not null THEN '{CdcConstants.SNAPSHOT_FLOW_TYPE}'
                    WHEN endswith(flow_name, "_cdc_flow") THEN '{CdcConstants.CDC_FLOW_TYPE}'
                    WHEN endswith(flow_name, ".{CdcConstants.CDC_STAGING_TABLE}") THEN '{CdcConstants.CDC_STAGING_TABLE_FLOW_TYPE}'
                    END) flow_type{Constants.sql_fields_def_extension_point}
                """,
        )
        return sql

    def _get_events_errors_sql(self):
        sql = super()._get_events_errors_sql()
        sql = sql.replace(
            Constants.sql_fields_def_extension_point,
            f", flow_type{Constants.sql_fields_def_extension_point}",
        )
        return sql

    def _get_events_warnings_sql(self):
        sql = super()._get_events_warnings_sql()
        sql = sql.replace(
            Constants.sql_fields_def_extension_point,
            f", flow_type{Constants.sql_fields_def_extension_point}",
        )
        return sql

    def _get_events_table_metrics_sql(self):
        sql = super()._get_events_table_metrics_sql()
        return sql.replace(
            Constants.sql_fields_def_extension_point,
            f", flow_type{Constants.sql_fields_def_extension_point}",
        )

    def register_base_tables_and_views(self, spark: SparkSession):
        super().register_base_tables_and_views(spark)

    def _get_table_run_processing_state_sql(self):
        sql = super()._get_table_run_processing_state_sql()
        sql = sql.replace(
            Constants.where_clause_extension_point,
            f"AND (table_name not LIKE '%.{CdcConstants.CDC_STAGING_TABLE}') {Constants.where_clause_extension_point}",
        )
        sql = sql.replace(
            Constants.sql_fields_def_extension_point,
            f", flow_type{Constants.sql_fields_def_extension_point}",
        )
        return sql

    def register_table_status(self, spark: SparkSession):
        table_status_per_pipeline_run_cdf = f"{TABLE_STATUS_PER_PIPELINE_RUN.name}_cdf"

        @dlt.view(name=table_status_per_pipeline_run_cdf)
        def table_run_processing_state_cdf():
            return (
                spark.readStream.option("readChangeFeed", "true")
                .table(TABLE_STATUS_PER_PIPELINE_RUN.name)
                .filter("_change_type IN ('insert', 'update_postimage')")
            )

        silver_table_name = f"{TABLE_STATUS.name}_silver"
        dlt.create_streaming_table(
            name=silver_table_name,
            comment="Capture information about the latest state, ingested data and errors for target tables",
            cluster_by=["pipeline_id", "table_name"],
            table_properties={"delta.enableRowTracking": "true"},
        )

        silver_latest_source_view_name = f"{silver_table_name}_latest_source"

        @dlt.view(name=silver_latest_source_view_name)
        def table_latest_run_processing_state_source():
            return spark.sql(f"""
          SELECT pipeline_id,
                 table_name,
                 pipeline_run_id AS latest_pipeline_run_id,
                 pipeline_run_link AS latest_pipeline_run_link,
                 latest_state,
                 latest_state_level,
                 latest_state_color,
                 latest_state_with_color,
                 table_schema_json AS latest_table_schema_json,
                 table_schema AS latest_table_schema,
                 null AS latest_cdc_changes_time,
                 null AS latest_snapshot_changes_time,
                 (CASE WHEN latest_error_time IS NOT NULL THEN pipeline_run_id END) AS latest_error_pipeline_run_id,
                 (CASE WHEN latest_error_time IS NOT NULL THEN pipeline_run_link END) AS latest_error_pipeline_run_link,
                 latest_error_time,
                 latest_error_log_message,
                 latest_error_message,
                 latest_error_code,
                 latest_error_full,
                 (CASE WHEN latest_error_time IS NOT NULL THEN flow_type END) AS latest_error_flow_type,
                 updated_at
          FROM STREAM(`{table_status_per_pipeline_run_cdf}`)
          WHERE table_name NOT LIKE '%.{CdcConstants.CDC_STAGING_TABLE}'
            """)

        dlt.create_auto_cdc_flow(
            name=f"{silver_table_name}_apply_latest",
            source=silver_latest_source_view_name,
            target=silver_table_name,
            keys=["pipeline_id", "table_name"],
            sequence_by="updated_at",
            ignore_null_updates=True,
        )

        silver_latest_cdc_changes_source_view_name = (
            f"{silver_table_name}_latest_cdc_changes_source"
        )

        @dlt.view(name=silver_latest_cdc_changes_source_view_name)
        def table_latest_run_processing_state_source():
            return spark.sql(f"""
          SELECT pipeline_id,
                 table_name,
                 null AS latest_pipeline_run_id,
                 null AS latest_pipeline_run_link,
                 null AS latest_state,
                 null AS latest_state_level,
                 null AS latest_state_color,
                 null AS latest_state_with_color,
                 null AS latest_table_schema_json,
                 null AS latest_table_schema,
                 event_timestamp AS latest_cdc_changes_time,
                 null AS latest_snapshot_changes_time,
                 null AS latest_error_pipeline_run_id,
                 null AS latest_error_pipeline_run_link,
                 null AS latest_error_time,
                 null AS latest_error_log_message,
                 null AS latest_error_message,
                 null AS latest_error_code,
                 null AS latest_error_full,
                 null AS latest_error_flow_type,
                 event_timestamp AS updated_at
          FROM STREAM(`{EVENTS_TABLE_METRICS.name}`)
          WHERE table_name IS NOT null 
                AND num_written_rows > 0
                AND flow_type='cdc'
            """)

        dlt.create_auto_cdc_flow(
            name=f"{silver_table_name}_apply_latest_cdc_changes",
            source=silver_latest_cdc_changes_source_view_name,
            target=silver_table_name,
            keys=["pipeline_id", "table_name"],
            sequence_by="updated_at",
            ignore_null_updates=True,
        )

        silver_latest_snapshot_changes_source_view_name = (
            f"{silver_table_name}_latest_snapshot_changes_source"
        )

        @dlt.view(name=silver_latest_snapshot_changes_source_view_name)
        def table_latest_run_processing_state_source():
            return spark.sql(f"""
          SELECT pipeline_id,
                 table_name,
                 null AS latest_pipeline_run_id,
                 null AS latest_pipeline_run_link,
                 null AS latest_state,
                 null AS latest_state_level,
                 null AS latest_state_color,
                 null AS latest_state_with_color,
                 null AS latest_table_schema_json,
                 null AS latest_table_schema,
                 null AS latest_cdc_changes_time,
                 event_timestamp AS latest_snapshot_changes_time,
                 null AS latest_error_pipeline_run_id,
                 null AS latest_error_pipeline_run_link,
                 null AS latest_error_time,
                 null AS latest_error_log_message,
                 null AS latest_error_message,
                 null AS latest_error_code,
                 null AS latest_error_full,
                 null AS latest_error_flow_type,
                 event_timestamp AS updated_at
          FROM STREAM(`{EVENTS_TABLE_METRICS.name}`)
          WHERE table_name IS NOT null 
                AND num_written_rows > 0
                AND flow_type='snapshot'
            """)

        dlt.create_auto_cdc_flow(
            name=f"{silver_table_name}_apply_latest_snapshot_changes",
            source=silver_latest_snapshot_changes_source_view_name,
            target=silver_table_name,
            keys=["pipeline_id", "table_name"],
            sequence_by="updated_at",
            ignore_null_updates=True,
        )

        @dlt.table(
            name=TABLE_STATUS.name,
            comment=TABLE_STATUS.table_comment,
            cluster_by=["pipeline_id", "table_name"],
            table_properties={"delta.enableRowTracking": "true"},
        )
        def table_status():
            return spark.sql(f"""
          SELECT s.*,
                 latest_pipeline_run_num_written_cdc_changes,
                 latest_pipeline_run_num_written_snapshot_changes
          FROM {silver_table_name} s
               LEFT JOIN (
                    SELECT pipeline_id,
                           pipeline_run_id,
                           table_name,
                           sum(ifnull(num_written_rows, 0)) FILTER (WHERE flow_type='{CdcConstants.CDC_FLOW_TYPE}') AS latest_pipeline_run_num_written_cdc_changes,
                           sum(ifnull(num_written_rows, 0)) FILTER (WHERE flow_type='{CdcConstants.SNAPSHOT_FLOW_TYPE}') AS latest_pipeline_run_num_written_snapshot_changes
                    FROM {EVENTS_TABLE_METRICS.name}
                    GROUP BY 1, 2, 3
                  ) AS etm 
                  ON s.pipeline_id = etm.pipeline_id 
                     AND s.latest_pipeline_run_id = etm.pipeline_run_id
                     AND s.table_name = etm.table_name
          """)


pipeline = CdcConnectorMonitoringEtlPipeline(conf, spark)
pipeline.register_base_tables_and_views(spark)
