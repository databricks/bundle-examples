"""
Common observability classes and functions.
"""

import json
import logging
from pyspark.sql import SparkSession
import os
import re
from typing import List, Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import Dashboard
from databricks.sdk.service.sql import State


def parse_comma_separated_list(s: Optional[str]) ->List[str]:
  """
  Parses a notebook parameter that contains a comma-separated list of items. It strips whitespace and
  skips empty items.
  :return: The parsed list of items
  """
  if s is None:
    return []
  return [j for j in [i.strip() for i in s.strip().split(',')] if len(j) > 0]


def is_parameter_defined(s: Optional[str]) -> bool:
  return s is not None and len(s.strip()) > 0

def parse_tag_value_pairs(tags_str: Optional[str]) -> List[List[tuple]]:
  """
  Parses a tag filter expression with OR of ANDs semantics.

  Format: Semi-colon-separated groups where each group is comma-separated tag[:value] pairs.
  - Semicolons separate groups (OR logic between groups)
  - Commas separate tags within a group (AND logic within group)
  - 'tag' is shorthand for 'tag:' (tag with empty value)

  :param tags_str: String like "tier:T0;team:data,tier:T1" meaning (tier:T0) OR (team:data AND tier:T1)
  :return: List of groups, where each group is a list of tuples like [[("tier", "T0")], [("team", "data"), ("tier", "T1")]]

  Examples:
    - "env:prod" -> [[("env", "prod")]]
    - "env:prod,tier:T0" -> [[("env", "prod"), ("tier", "T0")]]
    - "env:prod;env:staging" -> [[("env", "prod")], [("env", "staging")]]
    - "tier:T0;team:data,tier:T1" -> [[("tier", "T0")], [("team", "data"), ("tier", "T1")]]
    - "monitoring" -> [[("monitoring", "")]]
  """
  if not is_parameter_defined(tags_str):
    return []

  result = []
  # Split by semicolon to get groups (OR logic)
  groups = [g.strip() for g in tags_str.strip().split(';') if g.strip()]

  for group in groups:
    # Split by comma to get individual tags in this group (AND logic)
    tag_pairs = []
    items = [item.strip() for item in group.split(',') if item.strip()]

    for item in items:
      if ':' in item:
        # tag:value format
        parts = item.split(':', 1)
        tag_pairs.append((parts[0].strip(), parts[1].strip()))
      else:
        # tag format (shorthand for tag:)
        tag_pairs.append((item.strip(), ""))

    if tag_pairs:
      result.append(tag_pairs)

  return result

def get_pipeline_tags(wc: WorkspaceClient, pipeline_id: str) -> Optional[dict]:
    # For now we use the REST API directly as older Python SDK versions may not support tags
    pipeline_spec = wc.api_client.do(method='get', path=f'/api/2.0/pipelines/{pipeline_id}')['spec']

    # Check if pipeline has tags
    return pipeline_spec.get('tags')


def get_pipeline_ids_by_tags(
    wc: WorkspaceClient,
    tag_groups: List[List[tuple]],
    spark: Optional[SparkSession] = None,
    index_table_fqn: Optional[str] = None,
    index_enabled: bool = True,
    index_max_age_hours: int = 24,
    api_fallback_enabled: bool = True,
    log: Optional[logging.Logger] = None
) -> List[str]:
  """
  Fetches pipeline IDs using OR of ANDs logic for tag matching.
  This is a common helper function used by both EventLogImporter and MonitoringEtlPipeline.

  Logic: A pipeline matches if it satisfies ALL tags in ANY group.
  - Within a group: ALL tags must match (AND logic)
  - Between groups: ANY group can match (OR logic)

  Tries to use the pipeline tags index table first (if enabled and fresh), falls back to API-based discovery if needed.

  :param wc: WorkspaceClient instance
  :param tag_groups: List of tag groups, e.g., [[("env", "prod")], [("team", "data"), ("tier", "T1")]]
                     means (env:prod) OR (team:data AND tier:T1)
  :param spark: Optional SparkSession for index table queries
  :param index_table_fqn: Fully qualified name of the pipeline tags index table
  :param index_enabled: Whether to use the index table
  :param index_max_age_hours: Maximum age of index (in hours) before falling back to API
  :param api_fallback_enabled: Whether to fall back to API if index is unavailable/stale
  :param log: Optional logger for logging
  :return: List of pipeline IDs matching the tag filter expression
  """
  if not tag_groups:
    return []

  if log is None:
    log = logging.getLogger("get_pipeline_ids_by_tags")

  # Try index-based lookup first
  if index_enabled and spark is not None and index_table_fqn:
    try:
      # Check index freshness
      try:
        freshness_check = spark.sql(f"""
          SELECT
            MAX(last_updated) as last_updated,
            timestampdiff(HOUR, MAX(last_updated), CURRENT_TIMESTAMP()) as age_hours
          FROM {index_table_fqn}
        """).collect()[0]
        age_hours = freshness_check['age_hours']
      except Exception as e:
        if log:
          log.warning(f"Failed to check pipeline tags index: {e}")
        age_hours = None

      if age_hours is None or age_hours <= index_max_age_hours:
        # Index is fresh, use it
        log.info(f"Using pipeline tags index table (age: {age_hours:.1f} hours)")

        # Step 1: Collect all unique (tag_key, tag_value) pairs across all groups
        all_tag_pairs = set()
        for group in tag_groups:
          all_tag_pairs.update(group)

        # Step 2: Query database once for all tag pairs
        where_conditions = " OR ".join([
          f"(tag_key = '{tag_key}' AND tag_value = '{tag_value}')"
          for tag_key, tag_value in all_tag_pairs
        ])

        log.info(f"Querying pipeline tags index table {index_table_fqn} with where conditions: {where_conditions}")

        query = f"""
          SELECT DISTINCT tag_key, tag_value, explode(pipeline_ids) as pipeline_id
          FROM {index_table_fqn}
          WHERE {where_conditions}
        """

        result = spark.sql(query).collect()

        # Step 3: Build map from (tag_key, tag_value) -> set of pipeline_ids
        tag_to_pipelines = {}
        for row in result:
          tag_pair = (row['tag_key'], row['tag_value'])
          if tag_pair not in tag_to_pipelines:
            tag_to_pipelines[tag_pair] = set()
          tag_to_pipelines[tag_pair].add(row['pipeline_id'])

        # Step 4: For each group, intersect pipeline_ids (AND logic)
        matching_pipeline_ids = set()
        for group in tag_groups:
          if not group:
            continue

          # Get pipeline_ids for each tag in the group
          group_pipeline_sets = []
          for tag_pair in group:
            if tag_pair in tag_to_pipelines:
              group_pipeline_sets.append(tag_to_pipelines[tag_pair])
            else:
              # Tag doesn't exist in index, so no pipelines match this group
              group_pipeline_sets = []
              break

          # Intersect all sets in this group (AND logic)
          if group_pipeline_sets:
            group_result = set.intersection(*group_pipeline_sets)
            if group_result:
              log.info(f"Found {len(group_result)} pipeline(s) matching group {group}")
              # Step 5: Union with results from other groups (OR logic)
              matching_pipeline_ids.update(group_result)

        return list(matching_pipeline_ids)
      else:
        # Index is stale
        log.warning(f"Pipeline tags index is stale (age: {age_hours:.1f} hours > max: {index_max_age_hours} hours)")
        if not api_fallback_enabled:
          raise ValueError(f"Index is stale and API fallback is disabled")
    except Exception as e:
      log.warning(f"Failed to use pipeline tags index: {e}")
      if not api_fallback_enabled:
        raise

  # Fall back to API-based discovery
  log.warning("Falling back to API-based pipeline discovery (this may be slow)")

  matching_pipeline_ids = set()

  # List all pipelines in the workspace (this returns basic info only)
  all_pipeline_ids = [(pi.pipeline_id, pi.name) for pi in wc.pipelines.list_pipelines()]

  for pipeline_id, pipeline_name in all_pipeline_ids:
    try:
      # Fetch the full pipeline spec to get tags
      pipeline_tags = get_pipeline_tags(wc, pipeline_id)

      if not pipeline_tags:
        continue

      # Check if this pipeline matches any group (OR of ANDs)
      for group in tag_groups:
        # Check if pipeline has ALL tags in this group
        group_matches = True
        for tag_key, tag_value in group:
          if tag_key not in pipeline_tags or pipeline_tags[tag_key] != tag_value:
            group_matches = False
            break

        if group_matches:
          matching_pipeline_ids.add(pipeline_id)
          log.info(f"Pipeline {pipeline_name} ({pipeline_id}) matches group {group}")
          break  # Pipeline matches at least one group, no need to check other groups
    except Exception as e:
      log.warning(f"Failed to fetch pipeline {pipeline_id}: {e}")
      continue

  return list(matching_pipeline_ids)


def get_optional_parameter(value: Optional[str]) -> str:
  return value.strip() if is_parameter_defined(value) else None

def get_required_parameter(name: str, value: Optional[str]) -> str:
  if is_parameter_defined(value):
    return value.strip()
  
  raise ValueError(f"Missing required parameter: {name}")

def get_required_widget_parameter(widgets, param_name: str):
  return get_required_parameter(param_name, widgets.get(param_name))

SDP_EVENT_LOG_SCHEMA="""
    id STRING,
    sequence STRUCT<data_plane_id: STRUCT<instance: STRING, seq_no: BIGINT>, 
                    control_plane_seq_no: BIGINT>,
    origin STRUCT<cloud: STRING, 
                  region: STRING, 
                  org_id: BIGINT, 
                  user_id: BIGINT, 
                  pipeline_id: STRING, 
                  pipeline_type: STRING, 
                  pipeline_name: STRING, 
                  cluster_id: STRING, 
                  update_id: STRING, 
                  maintenance_id: STRING, 
                  table_id: STRING, 
                  table_name: STRING, 
                  flow_id: STRING, 
                  flow_name: STRING, 
                  batch_id: BIGINT, 
                  request_id: STRING, 
                  uc_resource_id: STRING, 
                  dataset_name: STRING, 
                  sink_name: STRING, 
                  catalog_name: STRING, 
                  schema_name: STRING,
                  materialization_name: STRING, 
                  operation_id: STRING, 
                  flow_attempt_id: STRING,
                  source_name: STRING,
                  uc_table_id: STRING, 
                  ingestion_source_type: STRING, 
                  uc_parent_table_id: STRING>,
      timestamp TIMESTAMP,
      message STRING,
      level STRING,
      maturity_level STRING,
      error STRUCT<fatal: BOOLEAN, 
                  exceptions: ARRAY<STRUCT<class_name: STRING, 
                                            message: STRING, 
                                            stack: ARRAY<STRUCT<declaring_class: STRING, method_name: STRING, file_name: STRING, line_number: BIGINT>>>>>,
        details STRING,
        event_type STRING
      """


class EventLogImporter:
  """
  A helper class to incrementally import SDP event logs from pipelines that are not configured to store the event log
  directly in a Delta table (see the [`event_log` option](https://docs.databricks.com/api/workspace/pipelines/create#event_log) in the
  Pipelines API). This can happen for example, if the pipeline was created prior to the introduction of ability to [Publish to Multiple Catalogs and Schemas from a Single DLT/SDP Pipeline](https://www.databricks.com/blog/publish-multiple-catalogs-and-schemas-single-dlt-pipeline).

  The import is done into a Delta table that can be used to store the logs from multiple pipelines.

  Note that is an expensive operation (it uses `MERGE` statements to achieve incrementalization) and should be used only if
  direct write of the event log to a Delta table is not possible.
  """

  def __init__(self, monitoring_catalog: str, monitoring_schema: str, imported_event_logs_table: str,
               index_table_name: str = "pipeline_tags_index",
               index_enabled: bool = True,
               index_max_age_hours: int = 24,
               api_fallback_enabled: bool = True,
               wc: Optional[WorkspaceClient] = None):
    """
    Constructor.
    :param monitoring_catalog: The catalog for the table with the imported event logs
    :param monitoring_schema: The schema for the table with the imported event logs
    :param imported_event_logs_table: The name of the table where the imported event logs are to be stored
    :param index_table_name: The name of the pipeline tags index table
    :param index_enabled: Whether to use the pipeline tags index
    :param index_max_age_hours: Maximum age of the index (in hours) before falling back to API
    :param api_fallback_enabled: Whether to fall back to API if index is unavailable/stale
    :param wc: The WorkspaceClient to use; if none is specified, a new one will be instantiated
    """
    if monitoring_catalog is None or len(monitoring_catalog.strip()) == 0:
      raise ValueError("Monitoring catalog cannot be empty")
    if monitoring_schema is None or len(monitoring_schema.strip()) == 0:
      raise ValueError("Monitoring schema cannot be empty")
    if imported_event_logs_table is None or len(imported_event_logs_table) == 0:
      raise ValueError("Imported event logs table cannot be empty")

    self.monitoring_catalog = monitoring_catalog.strip()
    self.monitoring_schema = monitoring_schema.strip()
    self.imported_event_logs_table = imported_event_logs_table.strip()
    self.imported_event_logs_table_fqname = f"`{self.monitoring_catalog}`.`{self.monitoring_schema}`.`{self.imported_event_logs_table}`"
    self.index_table_fqn = f"`{self.monitoring_catalog}`.`{self.monitoring_schema}`.`{index_table_name}`"
    self.index_enabled = index_enabled
    self.index_max_age_hours = index_max_age_hours
    self.api_fallback_enabled = api_fallback_enabled
    self.wc = wc if wc else WorkspaceClient()
    self.log = logging.getLogger("EventLogImporter")


  def create_target_table(self, spark: SparkSession):
    """
    Creates the target table where the event logs will be imported if it does not exists.
    """
    spark.sql(f"CREATE TABLE IF NOT EXISTS {self.imported_event_logs_table_fqname} ({SDP_EVENT_LOG_SCHEMA}) CLUSTER BY AUTO")


  def import_event_log_for_one_pipeline(self, pipeline_id: str, spark: SparkSession):
    """
    Imports current contents of the event log for the pipeline with the specified `pipeline_id`
    """
    self.log.info(f"Merging changes from event log for pipeline {pipeline_id} ...")
    merge_res_df = spark.sql(f"""
        MERGE INTO {self.imported_event_logs_table_fqname} AS t
        USING (SELECT * FROM event_log('{pipeline_id}')) as s
        ON t.origin.pipeline_id = s.origin.pipeline_id and t.id = s.id
        WHEN NOT MATCHED THEN INSERT *
        """)
    merge_res_df.show(truncate=False)
    latest_event_timestamp = spark.sql(f"""
          SELECT max(`timestamp`)
          FROM {self.imported_event_logs_table_fqname}
          WHERE origin.pipeline_id='{pipeline_id}' """).collect()[0][0]
    self.log.info(f"Latest imported event for pipeline {pipeline_id} as of {latest_event_timestamp}")


  def import_event_logs_for_pipelines(self, pipeline_ids: List[str], spark: SparkSession):
    """
    Imports current contents of the event logs for the pipelines in the `pipeline_ids` list
    """
    if len(pipeline_ids) == 0:
      print("Nothing to import")
    else:
      for pipeline_id in pipeline_ids:
        self.import_event_log_for_one_pipeline(pipeline_id, spark)


  def import_event_logs_for_pipelines_comma_list(self, pipeline_ids_list: str, spark: SparkSession):
    """
    Imports current contents of the event logs for the pipelines in comma-separated list in
    `pipeline_ids_list`. This is primarily for use with notebook parameters.
    """
    self.import_event_logs_for_pipelines(parse_comma_separated_list(pipeline_ids_list), spark)


  def import_event_logs_for_pipelines_by_tags(self, tags_str: str, spark: SparkSession):
    """
    Imports current contents of the event logs for pipelines matching ANY of the specified tag:value pairs.
    :param tags_str: Comma-separated list of tag:value pairs (e.g., "env:prod,team:data")
    :param spark: SparkSession instance
    """
    tag_value_pairs = parse_tag_value_pairs(tags_str)
    if not tag_value_pairs:
      self.log.info("No tags specified for pipeline filtering")
      return

    self.log.info(f"Fetching pipelines matching tags: {tags_str}")
    pipeline_ids = get_pipeline_ids_by_tags(self.wc, tag_value_pairs, self.log)

    if not pipeline_ids:
      self.log.warning(f"No pipelines found matching any of the tags: {tags_str}")
    else:
      self.log.info(f"Found {len(pipeline_ids)} pipeline(s) matching tags")
      self.import_event_logs_for_pipelines(pipeline_ids, spark)


  def import_event_logs_for_pipelines_by_ids_and_tags(self, pipeline_ids_list: str, tags_str: str, spark: SparkSession):
    """
    Imports current contents of the event logs for pipelines specified by IDs or matching tags.
    Pipelines matching either criteria will be included.
    :param pipeline_ids_list: Comma-separated list of pipeline IDs
    :param tags_str: Comma-separated list of tag:value pairs
    :param spark: SparkSession instance
    """
    # Collect pipeline IDs from explicit list
    explicit_ids = set(parse_comma_separated_list(pipeline_ids_list)) if pipeline_ids_list else set()

    # Collect pipeline IDs from tags
    tag_value_pairs = parse_tag_value_pairs(tags_str) if tags_str else []
    tag_ids = set(get_pipeline_ids_by_tags(
      self.wc,
      tag_value_pairs,
      spark=spark,
      index_table_fqn=self.index_table_fqn,
      index_enabled=self.index_enabled,
      index_max_age_hours=self.index_max_age_hours,
      api_fallback_enabled=self.api_fallback_enabled,
      log=self.log
    )) if tag_value_pairs else set()

    # Combine both sets
    all_pipeline_ids = explicit_ids.union(tag_ids)

    if not all_pipeline_ids:
      self.log.info("No pipelines specified (neither by ID nor by tags)")
      return

    self.log.info(f"Importing event logs for {len(all_pipeline_ids)} pipeline(s)")
    self.import_event_logs_for_pipelines(list(all_pipeline_ids), spark)


class PipelineTagsIndexBuilder:
  """
  A helper class to build an inverted index mapping pipeline tags to pipeline IDs.
  The index is stored in a Delta table and enables efficient discovery of pipelines by tags
  without having to query the Databricks API for every pipeline.
  """

  def __init__(self, monitoring_catalog: str, monitoring_schema: str, index_table_name: str, wc: Optional[WorkspaceClient] = None):
    """
    Constructor.
    :param monitoring_catalog: The catalog for the index table
    :param monitoring_schema: The schema for the index table
    :param index_table_name: The name of the index table
    :param wc: The WorkspaceClient to use; if none is specified, a new one will be instantiated
    """
    self.monitoring_catalog = monitoring_catalog.strip()
    self.monitoring_schema = monitoring_schema.strip()
    self.index_table_name = index_table_name.strip()
    self.index_table_fqn = f"`{self.monitoring_catalog}`.`{self.monitoring_schema}`.`{self.index_table_name}`"
    self.wc = wc if wc else WorkspaceClient()
    self.log = logging.getLogger("PipelineTagsIndexBuilder")


  def build_index(self, spark: SparkSession):
    """
    Builds the pipeline tags index and writes it to a Delta table.
    The index maps tag:value pairs to lists of pipeline IDs.
    """
    from datetime import datetime
    from pyspark.sql import Row

    self.log.info(f"Building pipeline tags index in table: {self.index_table_fqn}")

    # List all pipelines
    self.log.info("Listing all pipelines...")
    all_pipelines_id = [pi.pipeline_id for pi in self.wc.pipelines.list_pipelines()]
    self.log.info(f"Found {len(all_pipelines_id)} pipelines")

    # Build inverted index: tag:value -> [pipeline_ids]
    tags_index = {}  # {(tag_key, tag_value): [pipeline_ids]}
    processed_count = 0
    error_count = 0

    for pipeline_id in all_pipelines_id:
      try:
        # Check if pipeline has tags
        pipeline_tags = get_pipeline_tags(self.wc, pipeline_id)
        if pipeline_tags:
          # Add to inverted index
          for tag_key, tag_value in pipeline_tags.items():
            key = (tag_key, tag_value)
            if key not in tags_index:
              tags_index[key] = []
            tags_index[key].append(pipeline_id)

        processed_count += 1
        if processed_count % 100 == 0:
          self.log.info(f"Processed {processed_count}/{len(all_pipelines_id)} pipelines...")

      except Exception as e:
        error_count += 1
        self.log.warning(f"Failed to process pipeline {pipeline_id}: {e}")
        continue

    self.log.info(f"Processed {processed_count} pipelines ({error_count} errors)")
    self.log.info(f"Found {len(tags_index)} unique tag:value pairs")

    # Convert to DataFrame and write to Delta table
    if tags_index:
      # Create rows for the DataFrame
      rows = [
        Row(
          tag_key=tag_key,
          tag_value=tag_value,
          pipeline_ids=pipeline_ids,
          last_updated=datetime.utcnow()
        )
        for (tag_key, tag_value), pipeline_ids in tags_index.items()
      ]

      # Create DataFrame
      df = spark.createDataFrame(rows)

      # Write to Delta table (overwrite to ensure freshness)
      self.log.info(f"Writing index to {self.index_table_fqn}...")
      df.write \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .saveAsTable(self.index_table_fqn)

      self.log.info(f"Successfully built pipeline tags index with {len(tags_index)} entries")

    else:
      self.log.warning("No tags found in any pipelines. Index table will not be created/updated.")


class DashboardTemplate:
  """
  A helper class to transform the definition of dashboard based on DAB configuration variables. This is a workaround as
  currently AI/BI dashboards have limitted parametrization capabilites.

  Currently, the only transformation supported is setting the default catalog and schema for all datasets in the dashboard.
  """
  def __init__(self, 
               dashboard_template_path: str,
               dashboard_id: Optional[str] = None, 
               published_dashboard_name: Optional[str] = None,
               default_dataset_catalog: Optional[str] = None,
               default_dataset_schema: Optional[str] = None,
               warehouse_id: Optional[str] = None,
               wc: Optional[WorkspaceClient] = None):
    """
    Constructor
    :param dashboard_template_path: (required) the path to the `.lvdash.json` file of the dashboard to use as a template for publishing
    :param dashboard_id: the name of the AI/BI dashboard to update if known. If not specified, the notebook will attempt to find a 
                         dashboard with the specified `published_dashboard_name`. If none is found, a new one will be created. If 
                         multiple such dashboards aere found, the notebook will fail with an error and an explicit dashboard_id must 
                         be specified. 
    :param published_dashboard_name: (optional) the display name of the dashboard. If not specified, the name of the file (without 
                         the .lvdash.json extension and "Template") will be used.
    :param default_dataset_catalog: (optional) the default catalog for datasets to be set
    :param default_dataset_schema: (optional) the detault schema for datasets to be set
    :param warehouse_id: (optional) the ID of the warehouse to use for the AI/BI dashboard. If not specified, the first suitable one will be used.
    :param wc: the WorkspaceClient to use; if none is specified, a new one will be instantiated
    """
    self.log = logging.getLogger("DashboardTemplate")
    self.wc = wc if wc else WorkspaceClient()
    self.dashboard_template_path = get_required_parameter(name='dashboard_template_path', value=dashboard_template_path)
    if not os.path.exists(dashboard_template_path):
      raise ValueError(f"Dashboard at path {dashboard_template_path} does not exist")
    self.dashboard_id = get_optional_parameter(dashboard_id)
    self.published_dashboard_name = published_dashboard_name if is_parameter_defined(published_dashboard_name) else self._extract_dashboard_name_from_path(dashboard_template_path)
    self.default_dataset_catalog = get_optional_parameter(default_dataset_catalog)
    self.default_dataset_schema = get_optional_parameter(default_dataset_schema)
    self.warehouse_id = warehouse_id if is_parameter_defined(warehouse_id) else self._get_default_warehouse_id()
    if self.warehouse_id is None:
      raise Exception("Unable to find a suitable warehouse for the AI/BI dashboard. Please set `warehouse_id` with the ID of the warehouse to use.")

  @staticmethod
  def from_notebook_widgets(widgets, wc: Optional[WorkspaceClient] = None):
    return DashboardTemplate(dashboard_template_path=widgets.get("dashboard_template_path"),
                             dashboard_id=widgets.get("dashboard_id"),
                             published_dashboard_name=widgets.get("published_dashboard_name"),
                             default_dataset_catalog=widgets.get("default_dataset_catalog"),
                             default_dataset_schema=widgets.get("default_dataset_schema"),
                             warehouse_id=widgets.get("warehouse_id"),
                             wc=wc)
  

  @staticmethod
  def _extract_dashboard_name_from_path(dasboard_path: str) -> str:
    display_name = os.path.basename(dashboard_path).replace(".lvdash.json", "")
    return re.sub(r'\s+Template', '', display_name)


  def _get_default_warehouse_id(self):
      warehouse_name = None
      preferred_warehouse = min([w for w in self.wc.warehouses.list() if w.state == State.RUNNING], 
                                key=lambda w: f"{'0' if w.enable_serverless_compute else '9'}{w.name}")
      if preferred_warehouse is not None:
        self.log.info(f"Using warehouse: {preferred_warehouse.name} ({preferred_warehouse.id})")
        return preferred_warehouse.id
      else:
        self.log.warn(f"No suitable warehouse found")


  def _find_all_dashboards_with_name(self, display_name: str):
    dashboard_ids = []
    for d in self.wc.lakeview.list():
      if d.display_name == display_name:
        dashboard_ids.append(d.dashboard_id)
        self.log.info(f"Found existing dashboard with display name '{d.display_name}' ({d.dashboard_id})")
      else:
        self.log.debug(f"Ignoring dashboard with display name '{d.display_name}' != '{display_name}'")
    return dashboard_ids
  

  def _get_dashboard_id(self) -> Optional[str]:
    if self.dashboard_id is not None:
      return self.dashboard_id

    candidate_ids = self._find_all_dashboards_with_name(self.published_dashboard_name)
    if len(candidate_ids) > 1:
      raise ValueError(f"Multiple dashboard found with display name {self.published_dashboard_name}. Please specify an explicit `dashboard_id`.")
    return None if len(candidate_ids) == 0 else candidate_ids[0]


  def _process_dataset(self, dataset_elem: dict):
    dataset_elem['catalog'] = self.default_dataset_catalog
    dataset_elem['schema'] = self.default_dataset_schema


  def publish(self):
    """
    Publishes the dashboard
    """
    with open(self.dashboard_template_path) as f:
      dashboard_json = json.load(f)
    
    for ds in dashboard_json.get("datasets", []):
      self._process_dataset(ds)

    real_dashboard_id = self._get_dashboard_id()
    if real_dashboard_id is None:
      self.log.info(f"Creating new dashboard with display name '{self.published_dashboard_name}'")
    else:
      self.log.info(f"Using existing dashboard with ID {real_dashboard_id}")
    
    d_json = {
        "display_name": self.published_dashboard_name,
        "serialized_dashboard": json.dumps(dashboard_json),
        "warehouse_id": self.warehouse_id
        }

    if real_dashboard_id is None:
      d = self.wc.lakeview.create(dashboard=Dashboard.from_dict(d_json))
      self.log.info(f"Created dashboard '{d.display_name}' (ID={d.dashboard_id} ETAG={d.etag})")
      real_dashboard_id = d.dashboard_id
    else:
      d_json["dashboard_id"] = real_dashboard_id
      d = self.wc.lakeview.update(dashboard_id=real_dashboard_id, dashboard=Dashboard.from_dict(d_json))
      self.log.info(f"Updated dashboard '{d.display_name}' (ID={d.dashboard_id} ETAG={d.etag})")

    pd = self.wc.lakeview.publish(dashboard_id=real_dashboard_id, embed_credentials=True, warehouse_id=self.warehouse_id)
    self.log.info(f"Published dashboard '{pd.display_name}' revision time {pd.revision_create_time}")


