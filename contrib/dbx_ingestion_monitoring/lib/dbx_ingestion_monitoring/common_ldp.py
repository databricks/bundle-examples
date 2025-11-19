"""
Common observability functions to be used within SDP pipelines.
"""

from collections import namedtuple
import logging
from typing import Callable, Dict, Iterable, List, Optional, Set

import dlt
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors.platform import ResourceDoesNotExist
from pyspark.sql import SparkSession, DataFrame

from .common import parse_comma_separated_list
from .standard_tables import *

def sanitize_string_for_dlt_name(s: str) -> str:
  res = ""
  for c in s:
    if c == '.' or c == '-':
      res += '_'
    elif c != '`':
      res += c
  return res


class Constants:
  """
  Shared names and other constants
  """
  # Shared table names
  created_pipeline_runs="created_pipeline_runs"
  standard_pipeline_runs="standard_pipeline_runs"

  # Miscellaneous
  sql_fields_def_extension_point = "-- fields def extension point"
  where_clause_extension_point = "-- where clause extension point"


class Configuration:
  """
  Base monitoring ETL pipeline configuration
  """
  def __init__(self, conf: Dict[str, str]):
    self.monitoring_catalog = self._required_string_param(conf, "monitoring_catalog")
    self.monitoring_schema = self._required_string_param(conf, "monitoring_schema")
    self.directly_monitored_pipeline_ids=conf.get("directly_monitored_pipeline_ids", "")
    self.directly_monitored_pipeline_tags=conf.get("directly_monitored_pipeline_tags", "")
    self.imported_event_log_tables = conf.get("imported_event_log_tables", "")

    # Pipeline tags index configuration
    self.pipeline_tags_index_table_name = conf.get("pipeline_tags_index_table_name", "pipeline_tags_index")
    self.pipeline_tags_index_enabled = conf.get("pipeline_tags_index_enabled", "true").lower() == "true"
    self.pipeline_tags_index_max_age_hours = int(conf.get("pipeline_tags_index_max_age_hours", "24"))
    self.pipeline_tags_index_api_fallback_enabled = conf.get("pipeline_tags_index_api_fallback_enabled", "true").lower() == "true"
  
  @staticmethod
  def _required_string_param(conf: Dict[str, str], param_name: str):
    val = conf.get(param_name)
    if val is None or len(val.strip())  == 0:
      raise ValueError(f"Missing required parameter '{param_name}'")
    return val


# A helper class to capture metadata about monitored pipelines
PipelineInfo = namedtuple(
    'PipelineInfo',
    field_names=[
      "pipeline_id",
      "pipeline_name",
      "pipeline_link",
      "pipeline_type",
      "default_catalog",
      "default_schema",
      "event_log_source",
      "tags_map",
      "tags_array"
    ]
)


class MonitoringEtlPipeline:
  """
  A helper class to keep track of monitored pipelines.
  """

  def __init__(self, conf: Configuration, spark: SparkSession):
    self.conf = conf
    self.spark = spark
    self.monitored_pipeline_ids = []
    self.imported_event_log_tables = []
    # a dict from a pipeline id to a imported event log table for pipelines detected in these tables
    self.other_pipeline_event_logs: Dict[str, str] = {}
    # a dict from a monitored pipeline id to all metadata about this pipeline
    self.pipeline_infos: Dict[str, PipelineInfo] = {}
    # The set of all unique sources of event logs; this includes both tables with imported logs and also Delta event logs
    self.event_log_sources: Set[str] = set()
    self.wc = WorkspaceClient()
    self.log = logging.getLogger("MonitoredPipelines")
    self.event_log_source_views_mapping = {}

    # Automatically register pipelines in configuration
    self.register_delta_event_logs_from_pipelines_comma_list(self.conf.directly_monitored_pipeline_ids)
    self.register_delta_event_logs_from_pipelines_by_tags(self.conf.directly_monitored_pipeline_tags)
    self.register_imported_logs_tables_from_comma_list(self.conf.imported_event_log_tables, spark)


  def register_delta_event_logs_for_one_pipeline(self, pipeline_id: str):
    """
    Registers a pipeline that is being monitored. This method will extract all necessary metadata.
    """

    self.log.info(f"Detecting configuration for pipeline {pipeline_id} ...")
    try:
      spec = self.wc.api_client.do("GET", f"/api/2.0/pipelines/{pipeline_id}").get('spec', {})
    except ResourceDoesNotExist:
      self.log.warn(f"Skipping pipeline {pipeline_id} that no longer exists...")
      return

    event_log_info = spec.get("event_log", {})
    if ('name' not in event_log_info) and (pipeline_id not in self.other_pipeline_event_logs):
      raise Exception(f"""Pipeline {spec.get('name')} ({pipeline_id}) is not configured for Delta table event log and is not imported. 
                      Either configure the event log to be written to a Delta table or imported it using the import_event_logs job: {spec}""")
    
    if spec.get('gateway_definition') is not None:
      pipeline_type = 'gateway'
    elif spec.get('ingestion_definition') is not None:
      pipeline_type = 'ingestion'
    else:
      pipeline_type = 'etl'

    event_log_source = (
      f"`{event_log_info['catalog']}`.`{event_log_info['schema']}`.`{event_log_info['name']}`" if 'name' in event_log_info
          else self.other_pipeline_event_logs[pipeline_id]
    )

    # Extract tags from pipeline spec
    tags = spec.get('tags', {})
    # Create a map representation of tags
    tags_map = tags if tags else None
    # Create an array of "tag:value" strings for AI/BI dashboard filtering
    tags_array = [f"{k}:{v}" for k, v in tags.items()] if tags else None

    self.pipeline_infos[pipeline_id] = PipelineInfo(pipeline_id=pipeline_id,
                                pipeline_name=spec['name'],
                                pipeline_link=f"<a href='/pipelines/{pipeline_id}'>{spec['name']}</a>",
                                pipeline_type=pipeline_type,
                                default_catalog = spec['catalog'],
                                default_schema = spec.get('schema', spec.get('target')),
                                event_log_source=event_log_source,
                                tags_map=tags_map,
                                tags_array=tags_array)
    self.event_log_sources.add(event_log_source)
    self.log.info(f"Registered pipeline {spec.get('name')} ({pipeline_id}) ...")


  def register_delta_event_logs_for_pipelines(self, pipeline_ids: Iterable[str]):
    """
    Registers a collection of pipelines that are being monitored. This method will extract all necessary metadata.
    """
    for pipeline_id in pipeline_ids:
      self.register_delta_event_logs_for_one_pipeline(pipeline_id=pipeline_id)


  def register_delta_event_logs_from_pipelines_comma_list(self, pipelines_comma_list: str):
    """
    Registers a list of pipelines that are being monitored as a comma-separted list. This is primarily to be
    used with spark configuration and notebook parameters
    """
    self.register_delta_event_logs_for_pipelines(parse_comma_separated_list(pipelines_comma_list))


  def register_delta_event_logs_from_pipelines_by_tags(self, tags_str: str):
    """
    Registers pipelines that match ANY of the specified tag:value pairs for monitoring.
    :param tags_str: Comma-separated list of tag:value pairs (e.g., "env:prod,team:data")
    """
    from .common import parse_tag_value_pairs, get_pipeline_ids_by_tags

    tag_groups = parse_tag_value_pairs(tags_str)
    if not tag_groups:
      self.log.info("No tags specified for pipeline filtering")
      return

    self.log.info(f"Fetching pipelines matching tags: {tags_str}")

    # Construct fully qualified table name for the index
    index_table_fqn = f"`{self.conf.monitoring_catalog}`.`{self.conf.monitoring_schema}`.`{self.conf.pipeline_tags_index_table_name}`"

    pipeline_ids = get_pipeline_ids_by_tags(
        wc=self.wc,
        tag_groups=tag_groups,
        spark=self.spark,
        index_table_fqn=index_table_fqn,
        index_enabled=self.conf.pipeline_tags_index_enabled,
        index_max_age_hours=self.conf.pipeline_tags_index_max_age_hours,
        api_fallback_enabled=self.conf.pipeline_tags_index_api_fallback_enabled,
        log=self.log
    )

    if not pipeline_ids:
      self.log.warning(f"No pipelines found matching any of the tags: {tags_str}")
    else:
      self.log.info(f"Found {len(pipeline_ids)} pipeline(s) matching tags, registering for monitoring")
      self.register_delta_event_logs_for_pipelines(pipeline_ids)

  def register_one_imported_logs_table(self, imported_logs_table: str, spark: SparkSession):
    """
    Detects all pipelines in an imported logs table
    """
    if len(imported_logs_table.split('.')) < 3:
      # Create a fully qualified name if it is not already
      imported_logs_table = (
          f"`{self.conf.monitoring_catalog}`.`{self.conf.monitoring_schema}`.`{imported_logs_table}`" if imported_logs_table[0] != '`'
          else f"`{self.conf.monitoring_catalog}`.`{self.conf.monitoring_schema}`.{imported_logs_table}"
          )

    self.log.info(f"Detecting pipelines in imported logs table log {imported_logs_table} ...")
    self.imported_event_log_tables.append(imported_logs_table)
    other_pipeline_ids = [ r.pipeline_id for r in spark.sql(f"SELECT DISTINCT origin.pipeline_id FROM {imported_logs_table}").collect()]
    for pid in other_pipeline_ids:
      self.other_pipeline_event_logs[pid] = imported_logs_table
      self.register_delta_event_logs_for_one_pipeline(pipeline_id=pid)


  def register_base_tables_and_views(self, spark: SparkSession):
    """
    Registers a set of standard views and tables
    """
    self.register_monitored_pipelines(spark)
    self.register_event_log_source_views(spark)
    self.register_created_pipeline_runs(spark)
    self.register_event_logs_bronze(spark)
    self.register_monitored_tables(spark)
    self.register_pipeline_run_status(spark)
    self.register_events_errors(spark)
    self.register_events_warnings(spark)
    self.register_metric_pipeline_hourly_error_rate(spark)
    self.register_pipeline_status(spark)
    self.register_events_table_metrics(spark)
    self.register_table_status_per_pipeline_run(spark)
    self.register_table_status(spark)
    self.register_table_expectation_checks(spark)

  def register_imported_logs_tables(self, imported_logs_tables: Iterable[str], spark: SparkSession):
    """
    Detects all pipelines in a collection of imported logs tables
    """
    for imported_logs_table in imported_logs_tables:
      self.register_one_imported_logs_table(imported_logs_table, spark)


  def register_imported_logs_tables_from_comma_list(self, imported_logs_tables_comma_list: str, spark: SparkSession):
    """
    Detects all pipelines in a comma-separated of imported logs table
    """
    self.register_imported_logs_tables(parse_comma_separated_list(imported_logs_tables_comma_list), spark)


  def register_monitored_pipelines(self, spark: SparkSession):
    @dlt.table(name=MONITORED_PIPELINES.name,
              cluster_by=['pipeline_id'],
              comment=MONITORED_PIPELINES.table_comment,
              table_properties={
                "delta.enableRowTracking": "true"
              })
    def monitored_pipelines():
      return spark.createDataFrame(
          self.pipeline_infos.values(),
          schema="pipeline_id STRING, pipeline_name STRING, pipeline_link STRING, pipeline_type STRING, default_catalog STRING, default_schema STRING, event_log_source STRING, tags_map MAP<STRING, STRING>, tags_array ARRAY<STRING>"
          )


  def register_event_log_source_views(self, spark: SparkSession) -> Dict[str, str]:
    """
    Generates a view for each event log table. We need to ensure that "skipChangeCommits" is set to true
    so we don't break if modification or deletions are done in those tables.

    :return: A mapping from event logs source table to its corresponding view
    """
    def create_event_log_source_view(event_log_source: str) -> str:
      view_name = f"source_{sanitize_string_for_dlt_name(event_log_source)}"
      print(f"Defining source view {view_name} for event log source {event_log_source}")

      @dlt.view(name=view_name)
      def event_logs_source_view():
        return spark.readStream.option("skipChangeCommits", "true").table(event_log_source)
      
      return view_name
    
    self.event_log_source_views_mapping = {
          event_log_source: create_event_log_source_view(event_log_source) 
          for event_log_source in self.event_log_sources}

    return self.event_log_source_views_mapping
  

  def transfom_and_append_event_log_sources(self,
                                            target: str, 
                                            flow_prefix: str, 
                                            append_def: Callable[[str], DataFrame]):
    """
    Creates append flows per event log source into a target table or sink

    :param target: the name of the target table or sink
    :param flow_prefix: the string to prepend to the name of each flow into the target
    :param append_def: a function that defines the append flow; it takes the name of the event log 
                stream source as a parameter
    """

    def process_el_source(el_source: str):
      flow_name = f"{flow_prefix}_{sanitize_string_for_dlt_name(el_source)}"
      log_source = f"STREAM(`{self.event_log_source_views_mapping[el_source]}`)"
      print(f"Defining event log flow {flow_name} from {log_source} into {target}")

      @dlt.append_flow(name=flow_name, target=target)
      def el_append_flow():
        return append_def(log_source)

    for el_source in self.event_log_sources:
      process_el_source(el_source)


  def register_created_pipeline_runs(self, spark: SparkSession):
    """
    Creates a table and a view of all basic metadata about all pipeline runs detected in event logs of monitored
    pipelines. This allows to easily filter out runs that are not part of the normal data processing.
    """

    dlt.create_streaming_table(name=Constants.created_pipeline_runs, 
                              cluster_by=['pipeline_id', 'pipeline_run_id'],
                              comment="""
                                  A table to keep track of created pipeline runs with some metadata about each one.
                                  It is used  filter out runs that are not part of the normal data processing.
                                  """,
                              table_properties={
                                  "delta.enableRowTracking": "true"
                              })

    # Definition for flows from event log sources into `created_pipeline_runs`
    def append_to_created_pipeline_runs(event_log_source: str):
      details_partial_schema="STRUCT<create_update STRUCT<validate_only BOOLEAN, explore_only BOOLEAN>>"
      return spark.sql(f"""
          SELECT pipeline_id,
                pipeline_run_id,
                create_time,
                create_update_details.validate_only,
                create_update_details.explore_only,
                (create_update_details.explore_only
                    OR maintenance_id IS NOT NULL) AS is_internal_run -- used to filter out internal runs
          FROM (SELECT origin.pipeline_id, 
                      origin.update_id AS pipeline_run_id, 
                      origin.maintenance_id,
                      `timestamp` AS create_time,
                      from_json(details, '{details_partial_schema}').create_update AS create_update_details
                FROM {event_log_source}
                WHERE event_type == 'create_update')
      """)

    @dlt.view(name=Constants.standard_pipeline_runs)
    def generate_standard_pipeline_runs():
      return spark.sql(f"""
          SELECT pipeline_id, pipeline_run_id
          FROM `{Constants.created_pipeline_runs}`
          WHERE NOT is_internal_run 
          """)

    self.transfom_and_append_event_log_sources(
        target=Constants.created_pipeline_runs, 
        flow_prefix='cpr', 
        append_def=append_to_created_pipeline_runs)
    

  def _get_event_logs_bronze_sql(self, event_log_source: str):
    """
    Base definition for append flows from the event log sources into `event_logs_bronze` table. Subclasses can override
    this and replace {Constants.sql_fields_def_extension_point} with additional fiels they want to include
    """
    return f"""
        SELECT id, 
              seq_num, 
              pipeline_id, 
              pipeline_run_id, 
              ('<a href="/pipelines/' || pipeline_id || '/updates/' || pipeline_run_id || '">' || pipeline_run_id || '</a>') AS pipeline_run_link,
              
              coalesce(CASE WHEN els.table_name IS NULL 
                               OR mp.default_catalog IS NULL 
                               OR INSTR(els.table_name, '.') > 0 
                          THEN els.table_name
                      ELSE CONCAT(mp.default_catalog, '.', mp.default_schema, '.', els.table_name)
                      END,
                      CASE WHEN dataset_name IS NULL 
                               OR mp.default_catalog IS NULL 
                               OR INSTR(dataset_name, '.') > 0 
                          THEN dataset_name
                      ELSE CONCAT(mp.default_catalog, '.', mp.default_schema, '.', dataset_name)
                      END,
                        details:operation_progress.cdc_snapshot.table_name::string,
                        ft.table_name) AS table_name, 
              flow_name, 
              batch_id, 
              event_timestamp, 
              message, 
              level, 
              error_message,
              regexp_extract(error_message, r'^\\[([a-zA-Z.:0-9_]+)\\]', 1) as error_code,
              event_type,
              error_full,
              details{Constants.sql_fields_def_extension_point}
        FROM (SELECT id, 
                    sequence.data_plane_id.seq_no as seq_num,
                    origin.pipeline_id, 
                    origin.pipeline_name, 
                    origin.update_id as pipeline_run_id,
                    origin.table_name,
                    origin.dataset_name,
                    origin.flow_name,
                    origin.batch_id, 
                    `timestamp` as event_timestamp, 
                    message,
                    level,
                    error.exceptions[0].message as error_message,
                    (CASE WHEN error.exceptions IS NOT NULL THEN error ELSE NULL END) AS error_full,
                    event_type,
                    parse_json(details) as details -- TODO: Should we parse with a fixed schema
              FROM {event_log_source}) AS els
              JOIN `{Constants.standard_pipeline_runs}` USING (pipeline_id, pipeline_run_id)
              LEFT JOIN flow_targets AS ft USING (pipeline_id, pipeline_run_id, flow_name)
              LEFT JOIN {MONITORED_PIPELINES.name} AS mp USING (pipeline_id)
        WHERE event_type in ('create_update',    
                            'update_progress',     -- Pipeline update start and progress events
                            'flow_definition',     -- Flow initialization
                            'dataset_definition',  -- Table initialization
                            'flow_progress', -- metric and data-quality related events, errors
                            'operation_progress' -- Snapshot progress
                            )
        """


  def register_event_logs_bronze(self, spark: SparkSession):
    """
    Registers tables and views for the bronze layer of the event logs that contains basic common event log
    filters and transformations. This is the root source for most of observability tables.
    """

    def qualify_table_name_if_needed(table_name: str, default_catalog: str, default_schema: str) -> str:
      """
      Event logs sometimes contain a fully qualified table name and sometimes just the base name. This
      helper UDF uses the pipeline's default catalog and schema and would include those to unqualified
      table names.
      """
      if table_name is None or default_catalog is None or table_name.find('.') >= 0:
        return table_name
      return f"{default_catalog}.{default_schema}.{table_name}"
    # Comment out due to ES-1633439
    # spark.udf.register("qualify_table_name_if_needed", qualify_table_name_if_needed)

    # Create a helper table to map flows to target table as the target table names are currently not included
    # in the event log consistently
    dlt.create_streaming_table(
        name="flow_targets", 
        cluster_by=["pipeline_id", "pipeline_run_id", "flow_name"],
        comment="""Keeps track of the target tables for each flow so we can attribute flow_progress events to 
            specific tables.
            """,
        table_properties={
            "delta.enableRowTracking": "true"
        })
    
    # The common transformation of event log sources going into the `flow_targets` table
    def append_to_flow_targets(event_log_source: str):
      partial_flow_definition_details_schema = """STRUCT<flow_definition: STRUCT<
          output_dataset: STRING,
          schema: ARRAY<STRUCT<data_type: STRING, name: STRING, path: ARRAY<STRING>>>,
          schema_json: STRING,
          spark_conf: ARRAY<STRUCT<key: STRING, value: STRING>> > >"""
      return spark.sql(f"""
              SELECT pipeline_id,
                    pipeline_run_id,
                    flow_name,
                    (CASE WHEN details.output_dataset IS NULL 
                               OR mp.default_catalog IS NULL 
                               OR INSTR(details.output_dataset, '.') > 0 
                          THEN details.output_dataset
                      ELSE CONCAT(mp.default_catalog, '.', mp.default_schema, '.', details.output_dataset)
                      END) AS table_name,
                    details.schema,
                    details.schema_json,
                    details.spark_conf
              FROM (SELECT origin.pipeline_id, 
                        origin.pipeline_name, 
                        origin.update_id as pipeline_run_id,
                        origin.flow_name,
                        from_json(details, '{partial_flow_definition_details_schema}').flow_definition as details
                    FROM {event_log_source}
                    WHERE event_type='flow_definition') AS fd
                    LEFT JOIN {MONITORED_PIPELINES.name} as mp USING (pipeline_id)
            """)
      
    self.transfom_and_append_event_log_sources(
        target="flow_targets", 
        flow_prefix='ft', 
        append_def=append_to_flow_targets)

    dlt.create_streaming_table(name=EVENT_LOGS_BRONZE.name, 
              cluster_by=['pipeline_id', 'pipeline_run_id', 'table_name'],
              comment=EVENT_LOGS_BRONZE.table_comment,
              table_properties={
                  "delta.enableRowTracking": "true",
                  'delta.feature.variantType-preview': 'supported'
              })

    # Definition of the transformations from the event logs sources into `event_logs_bronze`
    def append_to_event_logs_bronze(event_log_source: str):
      return spark.sql(self._get_event_logs_bronze_sql(event_log_source))

    self.transfom_and_append_event_log_sources(
      target=EVENT_LOGS_BRONZE.name, 
      flow_prefix="elb", 
      append_def=append_to_event_logs_bronze)
  
  def register_monitored_tables(self, spark: SparkSession):
    @dlt.table(
        name=MONITORED_TABLES.name,
        comment=MONITORED_TABLES.table_comment,
        table_properties={
            "delta.enableRowTracking": "true"
        })
    def monitored_tables():
      return spark.sql(f"""
            SELECT DISTINCT pipeline_id, table_name
            FROM `{EVENT_LOGS_BRONZE.name}`
            WHERE table_name is not null
            """)
      
  def register_pipeline_run_status(self, spark: SparkSession):
    """
    Register the flows and tables needed to maintain the latest status of runs of monitored pipelines.
    """
    # We filter update_progress event from pipeline runs and use apply_changes() to maintain the latest status of each pipeline run
    source_view_name = f"{PIPELINE_RUNS_STATUS.name}_source"

    @dlt.view(name=source_view_name)
    def pipeline_runs_status_source():
      """
      Generates an apply_changes() stream for pipeline_updates_agg
      """
      return spark.sql(f"""
        SELECT *,
               ('<span style=''color:' || state_color || '''>' || latest_state || '</span>') AS latest_state_with_color
        FROM (SELECT  pipeline_id, 
                  pipeline_run_id, 
                  pipeline_run_link,
                  latest_state,
                  (CASE WHEN latest_state = 'FAILED' THEN 'red'
                        WHEN latest_state = 'COMPLETED' THEN 'green'
                        WHEN latest_state = 'RUNNING' THEN 'blue'
                        WHEN latest_state = 'CANCELED' THEN 'gray'
                        ELSE 'black'
                        END) AS state_color,
                   (CASE WHEN latest_state = 'FAILED' THEN 100 
                         WHEN latest_state = 'CANCELED' THEN 11 
                         WHEN latest_state = 'COMPLETED' THEN 10 
                         WHEN latest_state = 'STOPPING' THEN 8
                         WHEN latest_state = 'RUNNING' THEN 7
                         WHEN latest_state = 'SETTING_UP_TABLES' THEN 6
                         WHEN latest_state = 'RESETTING' THEN 5
                         WHEN latest_state = 'INITIALIZING' THEN 4
                         WHEN latest_state = 'WAITING_FOR_RESOURCES' THEN 3
                         WHEN latest_state = 'QUEUED' THEN 2 
                         WHEN latest_state = 'CREATED' THEN 1 
                         ELSE 0 END) AS latest_state_level,
                  (CASE WHEN event_type = 'create_update' THEN event_timestamp END) AS create_time,
                  (CASE WHEN event_type = 'update_progress' AND latest_state = 'WAITING_FOR_RESOURCES' THEN event_timestamp END) AS queued_time,
                  (CASE WHEN event_type = 'update_progress' AND latest_state = 'INITIALIZING' THEN event_timestamp END) AS initialization_start_time,
                  (CASE WHEN event_type = 'update_progress' AND latest_state = 'RUNNING' THEN event_timestamp END) AS running_start_time,
                  (CASE WHEN event_type = 'update_progress' AND latest_state in ('COMPLETED', 'CANCELED', 'FAILED') THEN event_timestamp END) AS end_time,
                  (CASE WHEN event_type = 'update_progress' AND latest_state in ('COMPLETED', 'CANCELED', 'FAILED') THEN true END) AS is_complete,
                  latest_error_log_message,
                  latest_error_message,
                  latest_error_code,
                  latest_error_full,
                  event_timestamp AS updated_at,
                  seq_num
            FROM (SELECT pipeline_id,
                        pipeline_run_id, 
                        pipeline_run_link,
                        event_timestamp,
                        details:update_progress.state::string AS latest_state,
                        (CASE WHEN error_full is not null or level='ERROR' THEN message END) AS latest_error_log_message,
                        error_message as latest_error_message,
                        error_code as latest_error_code,
                        error_full AS latest_error_full,
                        event_type,
                        seq_num
                  FROM STREAM(`{EVENT_LOGS_BRONZE.name}`))
            WHERE event_type == 'create_update' OR event_type == 'update_progress')
      """)
      
    dlt.create_streaming_table(name=PIPELINE_RUNS_STATUS.name, 
                              cluster_by=['pipeline_id', 'pipeline_run_id'],
                              comment=PIPELINE_RUNS_STATUS.table_comment,
                              table_properties={
                                  "delta.enableRowTracking": "true",
                                  "delta.enableChangeDataFeed": "true"
                              })
    dlt.apply_changes(
            source=source_view_name,
            target=PIPELINE_RUNS_STATUS.name,
            keys = ["pipeline_id", "pipeline_run_id"],
            sequence_by = "seq_num",
            except_column_list = ['seq_num'],
            ignore_null_updates = True)
    
  def _get_events_errors_sql(self):
    return f"""
          SELECT pipeline_id,
                pipeline_run_id,
                pipeline_run_link,
                flow_name,
                table_name,
                event_timestamp,
                message AS error_log_message,
                error_message,
                error_code,
                error_full{Constants.sql_fields_def_extension_point}
          FROM STREAM(`{EVENT_LOGS_BRONZE.name}`)
          WHERE error_full is not null or level="ERROR"
          """

  def register_events_errors(self, spark: SparkSession):
    @dlt.table(name=EVENTS_ERRORS.name, 
               cluster_by=["pipeline_id", "pipeline_run_id"], 
               comment=EVENTS_ERRORS.table_comment,
               table_properties={
                 "delta.enableRowTracking": "true"
               })
    def generate_events_errors():
      return spark.sql(self._get_events_errors_sql())
    
  def _get_events_warnings_sql(self):
    return f"""
          SELECT pipeline_id,
                pipeline_run_id,
                pipeline_run_link,
                flow_name,
                table_name,
                event_timestamp,
                message AS warning_log_message{Constants.sql_fields_def_extension_point}
          FROM STREAM(`{EVENT_LOGS_BRONZE.name}`)
          WHERE level="WARN"
          """

  def register_events_warnings(self, spark: SparkSession):
    @dlt.table(name=EVENTS_WARNINGS.name, 
               cluster_by=["pipeline_id", "pipeline_run_id"], 
               comment=EVENTS_WARNINGS.table_comment,
               table_properties={
                  "delta.enableRowTracking": "true"
               })
    def generate_events_warnings():
      return spark.sql(self._get_events_warnings_sql())
  
  def register_metric_pipeline_hourly_error_rate(self, spark: SparkSession):
    @dlt.table(name=METRIC_PIPELINE_HOURLY_ERROR_RATE.name,
               comment=METRIC_PIPELINE_HOURLY_ERROR_RATE.table_comment,
               cluster_by=['pipeline_id'],
               table_properties={
                  "delta.enableRowTracking": "true"
               })
    def generate_metric_pipeline_hourly_error_rate():
      return spark.sql(f"""
        SELECT pipeline_id,
               date_trunc('hour', event_timestamp) AS hour,
               count(*) FILTER (WHERE level='ERROR' OR error_full IS NOT NULL) AS num_errors
        FROM `{EVENT_LOGS_BRONZE.name}`
        GROUP BY 1, 2
        """)

  def register_pipeline_status(self, spark: SparkSession):
    pipeline_runs_status_fqname=f"{self.conf.monitoring_catalog}.{self.conf.monitoring_schema}.{PIPELINE_RUNS_STATUS.name}"

    @dlt.view(name=f"{PIPELINE_RUNS_STATUS.name}_cdf")
    def pipeline_runs_status_cdf():
      return (
        spark.readStream
             .option("readChangeFeed", "true")
             .table(PIPELINE_RUNS_STATUS.name)
             .filter("_change_type IN ('insert', 'update_postimage')")
        )

    dlt.create_streaming_table(name=PIPELINES_STATUS_SILVER.name, 
                           cluster_by = ["pipeline_id"], 
                           comment=PIPELINES_STATUS_SILVER.table_comment,
                           table_properties={
                              "delta.enableRowTracking": "true"
                           })
    latest_runs_view_name = f"{PIPELINE_RUNS_STATUS.name}_latest"
    @dlt.view(name=latest_runs_view_name)
    def latest_pipeline_run_progress():
      return spark.sql(f"""
            SELECT pipeline_id,
                   pipeline_run_id as latest_pipeline_run_id,
                   pipeline_run_link as latest_pipeline_run_link,
                   create_time as latest_pipeline_run_create_time,
                   end_time as latest_pipeline_run_end_time,
                   latest_state as latest_pipeline_run_state,
                   state_color as latest_pipeline_run_state_color,
                   latest_state_with_color as latest_pipeline_run_state_with_color,
                   latest_state_level as latest_pipeline_run_state_level,
                   is_complete as latest_pipeline_run_is_complete,
                   -- use an empty strings so that it overwrites any errors from previous runs
                   ifnull(latest_error_log_message, '') AS latest_error_log_message, 
                   ifnull(latest_error_message, '') AS latest_error_message, 
                   ifnull(latest_error_code, '') AS latest_error_code,
                   (CASE WHEN latest_error_log_message is not NULL AND latest_error_log_message != '' THEN updated_at END) as latest_error_time,
                   null as latest_successful_run_id,
                   null as latest_successful_run_link,
                   null as latest_successful_run_create_time,
                   null as latest_successful_run_end_time,
                   null as latest_failed_run_id,
                   null as latest_failed_run_link,
                   null as latest_failed_run_create_time,
                   null as latest_failed_run_end_time,
                   null as latest_failed_run_error_log_message,
                   null as latest_failed_run_error_message,
                   null as latest_failed_run_error_code,
                   updated_at
            FROM STREAM(`{PIPELINE_RUNS_STATUS.name}_cdf`)
            """)
    dlt.create_auto_cdc_flow(
      name=f"apply_{latest_runs_view_name}",
      source=latest_runs_view_name,
      target=PIPELINES_STATUS_SILVER.name,
      keys=['pipeline_id'],
      sequence_by='updated_at',
      ignore_null_updates=True
    )

    successful_runs_view_name = f"{PIPELINE_RUNS_STATUS.name}_successful"
    @dlt.view(name=successful_runs_view_name)
    def latest_pipeline_successful_run():
      return spark.sql(f"""
            SELECT pipeline_id,
                  null as latest_pipeline_run_id,
                  null as latest_pipeline_run_link,
                  null as latest_pipeline_run_create_time,
                  null as latest_pipeline_run_end_time,
                  null as latest_pipeline_run_state,
                  null as latest_pipeline_run_state_color,
                  null as latest_pipeline_run_state_with_color,
                  null as latest_pipeline_run_state_level,
                  null as latest_pipeline_run_is_complete,
                  null as latest_error_log_message,
                  null AS latest_error_message,
                  null AS latest_error_code,
                  null as latest_error_time,
                  pipeline_run_id as latest_successful_run_id,
                  pipeline_run_link as latest_successful_run_link,
                  create_time as latest_successful_run_create_time,
                  end_time as latest_successful_run_end_time,
                  null as latest_failed_run_id,
                  null as latest_failed_run_link,                  
                  null as latest_failed_run_create_time,
                  null as latest_failed_run_end_time,
                  null as latest_failed_run_error_log_message,
                  null as latest_failed_run_error_message,
                  null as latest_failed_run_error_code,
                  updated_at
            FROM STREAM(`{PIPELINE_RUNS_STATUS.name}_cdf`)
            WHERE latest_state == 'COMPLETED'
      """)
        
    dlt.create_auto_cdc_flow(
      name=f"apply_{successful_runs_view_name}",
      source=successful_runs_view_name,
      target=PIPELINES_STATUS_SILVER.name,
      keys=['pipeline_id'],
      sequence_by='updated_at',
      ignore_null_updates=True
    )

    failed_runs_view_name = f"{PIPELINE_RUNS_STATUS.name}_failed"
    @dlt.view(name=failed_runs_view_name)
    def latest_pipeline_failed_run():
      return spark.sql(f"""
            SELECT pipeline_id,
                  null as latest_pipeline_run_id,
                  null as latest_pipeline_run_link,
                  null as latest_pipeline_run_create_time,
                  null as latest_pipeline_run_end_time,
                  null as latest_pipeline_run_state,
                  null as latest_pipeline_run_state_color,
                  null as latest_pipeline_run_state_with_color,
                  null as latest_pipeline_run_state_level,
                  null as latest_pipeline_run_is_complete,
                  null as latest_error_log_message,
                  null AS latest_error_message,
                  null AS latest_error_code,
                  null as latest_error_time,
                  null as latest_successful_run_id,
                   null as latest_successful_run_link,
                  null as latest_successful_run_create_time,
                  null as latest_successful_run_end_time,
                  pipeline_run_id as latest_failed_run_id,
                  pipeline_run_link as latest_failed_run_link,
                  create_time as latest_failed_run_create_time,
                  end_time as latest_failed_run_end_time,
                  -- use empty strings so that it overwrites any errors from previous runs
                  ifnull(latest_error_log_message, '') as latest_failed_run_error_log_message,
                  ifnull(latest_error_message, '') as latest_failed_run_error_message,
                  ifnull(latest_error_code, '') as latest_failed_run_error_code,
                  updated_at
            FROM STREAM(`{PIPELINE_RUNS_STATUS.name}_cdf`)
            WHERE latest_state == 'FAILED'
      """)
        
    dlt.create_auto_cdc_flow(
      name=f"apply_{failed_runs_view_name}",
      source=failed_runs_view_name,
      target=PIPELINES_STATUS_SILVER.name,
      keys=['pipeline_id'],
      sequence_by='updated_at',
      ignore_null_updates=True
    )

    @dlt.table(name=PIPELINES_STATUS.name,
               comment=PIPELINES_STATUS.table_comment,
               cluster_by=['pipeline_id'],
               table_properties={
                 "delta.enableRowTracking": "true"
               })
    def pipeline_status():
      return spark.sql(f"""
            SELECT latest.*,
                   ifnull(pe.num_errors, 0) latest_pipeline_run_num_errors,
                   ifnull(pw.num_warnings, 0) latest_pipeline_run_num_warnings
              FROM `{PIPELINES_STATUS_SILVER.name}`  as latest
                  LEFT JOIN (
                      SELECT pipeline_id, pipeline_run_id, count(*) num_errors
                      FROM `{EVENTS_ERRORS.name}`
                      GROUP BY 1, 2
                  ) as pe ON latest.pipeline_id = pe.pipeline_id and latest.latest_pipeline_run_id = pe.pipeline_run_id
                  LEFT JOIN (
                      SELECT pipeline_id, pipeline_run_id, count(*) num_warnings
                      FROM `{EVENTS_WARNINGS.name}`
                      GROUP BY 1, 2
                  ) as pw ON latest.pipeline_id = pw.pipeline_id and latest.latest_pipeline_run_id = pw.pipeline_run_id
            """)
      
  def _get_events_table_metrics_sql(self):
    return f"""
          SELECT pipeline_id, 
                 pipeline_run_id, 
                 pipeline_run_link,
                 flow_name,
                 table_name, 
                 event_timestamp,
                 details:flow_progress.metrics.num_output_rows::bigint as num_output_rows,
                 details:flow_progress.metrics.backlog_bytes::bigint as backlog_bytes,
                 details:flow_progress.metrics.backlog_records::bigint as backlog_records,
                 details:flow_progress.metrics.backlog_files::bigint as backlog_files,
                 details:flow_progress.metrics.backlog_seconds::bigint as backlog_seconds,
                 details:flow_progress.metrics.executor_time_ms::bigint as executor_time_ms,
                 details:flow_progress.metrics.executor_cpu_time_ms::bigint as executor_cpu_time_ms,
                 details:flow_progress.metrics.num_upserted_rows::bigint as num_upserted_rows,
                 details:flow_progress.metrics.num_deleted_rows::bigint as num_deleted_rows,
                 details:flow_progress.metrics.num_output_bytes::bigint as num_output_bytes,
                 (CASE WHEN details:flow_progress.metrics.num_output_rows::bigint IS NULL 
                           AND details:flow_progress.metrics.num_upserted_rows::bigint IS NULL
                           AND details:flow_progress.metrics.num_deleted_rows::bigint IS NULL THEN NULL
                       ELSE ifnull(details:flow_progress.metrics.num_output_rows::bigint, 0)
                           + ifnull(details:flow_progress.metrics.num_upserted_rows::bigint, 0) 
                           + ifnull(details:flow_progress.metrics.num_deleted_rows::bigint, 0) END) AS num_written_rows,
                 details:flow_progress.streaming_metrics.event_time.min::timestamp AS min_event_time,
                 details:flow_progress.streaming_metrics.event_time.max::timestamp AS max_event_time,
                 details:flow_progress.data_quality.dropped_records::bigint as num_expectation_dropped_records{Constants.sql_fields_def_extension_point}
          FROM STREAM(`{EVENT_LOGS_BRONZE.name}`)
          WHERE table_name is not null
                AND (details:flow_progress.metrics IS NOT NULL 
                     OR details:flow_progress.streaming_metrics IS NOT NULL
                     OR details:flow_progress.data_quality IS NOT NULL)
                     """

  def register_events_table_metrics(self, spark: SparkSession):
    @dlt.table(name=EVENTS_TABLE_METRICS.name,
           comment=EVENTS_TABLE_METRICS.table_comment,
           cluster_by=['pipeline_id', 'pipeline_run_id', 'table_name'],
           table_properties={
             "delta.enableRowTracking": "true"
           })
    def generate_events_table_metrics():
      return spark.sql(self._get_events_table_metrics_sql())

  def _get_table_run_processing_state_sql(self):
    return f"""
          SELECT *,
                 ('<span style="color:' || latest_state_color || ';">' || latest_state || '</span>') as latest_state_with_color
          FROM (SELECT *,
                  (CASE WHEN latest_state = 'FAILED' THEN 100 
                        WHEN latest_state = 'SKIPPED' THEN 50 
                        WHEN latest_state = 'STOPPED' THEN 13
                        WHEN latest_state = 'EXCLUDED' THEN 12
                        WHEN latest_state = 'IDLE' THEN 11
                        WHEN latest_state = 'COMPLETED' THEN 10
                        WHEN latest_state = 'RUNNING' THEN 5
                        WHEN latest_state = 'PLANNING' THEN 3
                        WHEN latest_state = 'STARTING' THEN 2
                        WHEN latest_state = 'QUEUED' THEN 1
                        ELSE 0 END) AS latest_state_level,
                    (CASE WHEN latest_state = 'FAILED' THEN 'red'
                          WHEN latest_state = 'SKIPPED' THEN 'red'
                          WHEN latest_state = 'STOPPED' THEN 'gray'
                          WHEN latest_state = 'EXCLUDED' THEN 'gray'
                          WHEN latest_state = 'IDLE' THEN 'green'
                          WHEN latest_state = 'COMPLETED' THEN 'green'
                          WHEN latest_state = 'RUNNING' THEN 'blue'
                          ELSE 'black'
                          END) AS latest_state_color
                FROM (SELECT pipeline_id,
                      pipeline_run_id,
                      pipeline_run_link,
                      table_name,
                      seq_num,
                      event_timestamp AS updated_at,
                      details:flow_progress.status::string AS latest_state,
                      (CASE WHEN event_type='dataset_definition' THEN details:dataset_definition.schema_json::string END) table_schema_json,
                      (CASE WHEN event_type='dataset_definition' THEN details:dataset_definition.schema::array<struct<name STRING, path STRING, data_type STRING, comment STRING>> END) table_schema,
                      (CASE WHEN level='ERROR' OR error_full IS NOT NULL THEN event_timestamp END) AS latest_error_time,
                      (CASE WHEN level='ERROR' OR error_full IS NOT NULL THEN message END) AS latest_error_log_message,
                      error_message AS latest_error_message,
                      error_code AS latest_error_code,
                      error_full AS latest_error_full{Constants.sql_fields_def_extension_point}
                FROM STREAM(`{EVENT_LOGS_BRONZE.name}`)
                WHERE event_type in ('dataset_definition', 'flow_progress')
                      AND table_name IS NOT NULL
                      {Constants.where_clause_extension_point}
                      ))
            """

  def register_table_status_per_pipeline_run(self, spark: SparkSession):
    dlt.create_streaming_table(name=TABLE_STATUS_PER_PIPELINE_RUN.name,
                               comment=TABLE_STATUS_PER_PIPELINE_RUN.table_comment,
                               cluster_by=['pipeline_id', 'pipeline_run_id', 'table_name'],
                               table_properties={
                                 "delta.enableRowTracking": "true",
                                 "delta.enableChangeDataFeed": "true",
                               })

    source_view_name=f"{TABLE_STATUS_PER_PIPELINE_RUN.name}_source"
    @dlt.view(name=source_view_name)
    def table_run_processing_state_source():
      return spark.sql(self._get_table_run_processing_state_sql())

    dlt.create_auto_cdc_flow(
        name=f"apply_{TABLE_STATUS_PER_PIPELINE_RUN.name}",
        source=source_view_name,
        target=TABLE_STATUS_PER_PIPELINE_RUN.name,
        keys=['pipeline_id', 'pipeline_run_id', 'table_name'],
        sequence_by='seq_num',
        ignore_null_updates=True,
        except_column_list=['seq_num'])


  def register_table_status(self, spark: SparkSession):
    # Use CDF because apply_changes can generate MERGE commits
    table_status_per_pipeline_run_cdf = f"{TABLE_STATUS_PER_PIPELINE_RUN.name}_cdf"

    @dlt.view(name=table_status_per_pipeline_run_cdf)
    def table_run_processing_state_cdf():
      return (
        spark.readStream
             .option("readChangeFeed", "true")
             .table(TABLE_STATUS_PER_PIPELINE_RUN.name)
             .filter("_change_type IN ('insert', 'update_postimage')")
      )

    silver_table_name = f"{TABLE_STATUS.name}_silver"
    dlt.create_streaming_table(name=silver_table_name,
                               comment="Capture information about the latest state, ingested data and errors for target tables",
                               cluster_by=['pipeline_id', 'table_name'],
                               table_properties={
                                 "delta.enableRowTracking": "true"
                               })

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
                 null AS latest_changes_time,
                 (CASE WHEN latest_error_time IS NOT NULL THEN pipeline_run_id END) AS latest_error_pipeline_run_id,
                 (CASE WHEN latest_error_time IS NOT NULL THEN pipeline_run_link END) AS latest_error_pipeline_run_link,
                 latest_error_time,
                 latest_error_log_message,
                 latest_error_message,
                 latest_error_code,
                 latest_error_full,
                 updated_at
          FROM STREAM(`{table_status_per_pipeline_run_cdf}`)
          """)

    dlt.create_auto_cdc_flow(
        name=f"{silver_table_name}_apply_latest",
        source=silver_latest_source_view_name,
        target=silver_table_name,
        keys=['pipeline_id', 'table_name'],
        sequence_by='updated_at',
        ignore_null_updates=True)

    silver_latest_changes_source_view_name = f"{silver_table_name}_latest_changes_source"
    @dlt.view(name=silver_latest_changes_source_view_name)
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
                 event_timestamp AS latest_changes_time,
                 null AS latest_error_pipeline_run_id,
                 null AS latest_error_pipeline_run_link,
                 null AS latest_error_time,
                 null AS latest_error_log_message,
                 null AS latest_error_message,
                 null AS latest_error_code,
                 null AS latest_error_full,
                 event_timestamp AS updated_at
          FROM STREAM(`{EVENTS_TABLE_METRICS.name}`)
          WHERE table_name IS NOT null AND num_written_rows > 0
            """)

    dlt.create_auto_cdc_flow(
        name=f"{silver_table_name}_apply_latest_changes",
        source=silver_latest_changes_source_view_name,
        target=silver_table_name,
        keys=['pipeline_id', 'table_name'],
        sequence_by='updated_at',
        ignore_null_updates=True)

    @dlt.table(name=TABLE_STATUS.name,
               comment=TABLE_STATUS.table_comment,
               cluster_by=['pipeline_id', 'table_name'],
               table_properties={
                    "delta.enableRowTracking": "true"
               })
    def table_status():
      return spark.sql(f"""
          SELECT s.*,
                 latest_pipeline_run_num_written_rows
          FROM {silver_table_name} s
               LEFT JOIN (
                    SELECT pipeline_id,
                           pipeline_run_id,
                           table_name,
                           sum(ifnull(num_written_rows, 0)) AS latest_pipeline_run_num_written_rows
                    FROM {EVENTS_TABLE_METRICS.name}
                    GROUP BY 1, 2, 3
                  ) AS etm 
                  ON s.pipeline_id = etm.pipeline_id 
                     AND s.latest_pipeline_run_id = etm.pipeline_run_id
                     AND s.table_name = etm.table_name
          """)
  
  def register_table_expectation_checks(self, spark: SparkSession):
    @dlt.table(name=TABLE_EVENTS_EXPECTATION_CHECKS.name,
               comment=TABLE_EVENTS_EXPECTATION_CHECKS.table_comment,
               cluster_by=['pipeline_id', 'pipeline_run_id', 'table_name', 'expectation_name'],
               table_properties={
                    "delta.enableRowTracking": "true"
               })
    def table_expectation_checks():
      return spark.sql(f"""
        SELECT pipeline_id,
               pipeline_run_id,
               pipeline_run_link,
               table_name,
               flow_name,
               event_timestamp,
               expectation_name,
               num_passed,
               num_failed,
               (100.0 * num_failed / (num_failed + num_passed)) AS failure_pct
        FROM(SELECT pipeline_id,
               pipeline_run_id,
               pipeline_run_link,
               table_name,
               flow_name,
               event_timestamp,
               expectation_metrics.name as expectation_name,
               ifnull(expectation_metrics.passed_records, 0) as num_passed,
               ifnull(expectation_metrics.failed_records, 0) as num_failed
            FROM (SELECT pipeline_id,
                    pipeline_run_id,
                    pipeline_run_link,
                    table_name,
                    flow_name,
                    event_timestamp,
                    explode(details:flow_progress.data_quality.expectations::array<struct<name STRING, dataset STRING, passed_records BIGINT, failed_records BIGINT>>) AS expectation_metrics
                  FROM STREAM(`{EVENT_LOGS_BRONZE.name}`)
                  WHERE details:flow_progress.data_quality IS NOT NULL
                  ))
          """)
    pass
