import os
import json
import re
from . import envmanager
from . import formatmanager
from pyspark.sql.streaming import DataStreamReader
from pyspark.sql import DataFrame, SparkSession
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors.platform import NotFound


def validate_config(table_config: dict):
    # Required fields
    if not table_config.get("name"):
        raise ValueError("name is required for table config")
    if not table_config.get("format"):
        raise ValueError("format is required for table config")

    # Validate table name characters (Databricks naming convention)
    table_name = table_config.get("name")
    if not re.match(r"^[a-z0-9_-]+$", table_name):
        raise ValueError(
            f"Table name '{table_name}' contains unsupported characters. "
            "Table names must only consist of lowercase letters, numbers, underscores, and dashes."
        )

    # Validate format is supported
    fmt = table_config.get("format")
    try:
        fmt_mgr = formatmanager.get_format_manager(fmt)
    except ValueError as e:
        raise ValueError(f"Unsupported format for table '{table_name}': {e}")

    # Validate format options (check for blocklisted/hidden options)
    format_options = table_config.get("format_options", {})
    if format_options:
        try:
            fmt_mgr.validate_user_options(format_options)
        except ValueError as e:
            raise ValueError(f"Invalid format options for table '{table_name}': {e}")


def validate_configs(table_configs: list):
    names = [cfg.get("name") for cfg in table_configs]
    duplicates = set(
        [name for name in names if names.count(name) > 1 and name is not None]
    )
    if duplicates:
        raise ValueError(
            f"Duplicate table names found in table configs: {sorted(duplicates)}"
        )
    for table_config in table_configs:
        validate_config(table_config)


def get_configs() -> list:
    json_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "configs", "tables.json"
    )
    if not os.path.exists(json_path):
        raise RuntimeError(
            f"Missing table configs file: {json_path}. Please following README.md to create one, deploy and run configuration_job."
        )
    with open(json_path, "r") as f:
        configs = json.load(f)
    validate_configs(configs)
    return configs


def get_table_volume_path(table_name: str) -> str:
    ws = WorkspaceClient()
    table_volume_path_data = os.path.join(
        envmanager.get_config()["volume_path_data"], table_name
    )
    try:
        ws.files.get_directory_metadata(table_volume_path_data)
    except NotFound:
        raise RuntimeError(
            f"Table data path not found for table `{table_name}`. Have you run `databricks bundle run configuration_job`?"
        )
    return table_volume_path_data


def has_data_file(table_name: str) -> bool:
    ws = WorkspaceClient()
    table_volume_path_data = get_table_volume_path(table_name)
    try:
        iter = ws.files.list_directory_contents(table_volume_path_data)
        next(iter)
    except StopIteration:
        return False
    return True


def is_table_created(table_name: str) -> bool:
    ws = WorkspaceClient()
    return ws.tables.exists(
        full_name=f"{envmanager.get_config()['catalog_name']}.{envmanager.get_config()['schema_name']}.{table_name}"
    ).table_exists


def _apply_table_options(
    reader: DataStreamReader, table_config: dict, fmt_mgr, is_placeholder: bool = False
) -> DataStreamReader:
    name = table_config.get("name")
    fmt = table_config.get("format")

    # format options
    user_fmt_opts = table_config.get("format_options", {})
    final_fmt_opts = fmt_mgr.get_merged_options(user_fmt_opts, name, is_placeholder)
    reader = reader.option("cloudFiles.format", fmt)
    for k, v in final_fmt_opts.items():
        reader = reader.option(k, v)

    # schema hints
    schema_hints = table_config.get("schema_hints")

    use_schema = (
        final_fmt_opts.get("cloudFiles.schemaEvolutionMode", "").lower() == "rescue"
        or is_placeholder
    )

    # schema_hints goes first, then default schema entries (ordered)
    base_schema = []
    if schema_hints:
        base_schema.append(schema_hints)
    base_schema.extend(fmt_mgr.default_schema)

    joined_schema = ", ".join(base_schema)

    if use_schema:
        reader = reader.schema(joined_schema)
    else:
        reader = reader.option("cloudFiles.schemaHints", joined_schema)

    return reader


def get_df_with_config(
    spark: SparkSession, table_config: dict, schema_location: str = None
) -> DataFrame:
    validate_config(table_config)
    fmt = table_config.get("format")
    fmt_mgr = formatmanager.get_format_manager(fmt)

    reader = spark.readStream.format("cloudFiles")
    reader = _apply_table_options(reader, table_config, fmt_mgr)
    if schema_location:
        reader = reader.option("cloudFiles.schemaLocation", schema_location)

    # include file metadata
    return reader.load(get_table_volume_path(table_config.get("name"))).selectExpr(
        "*", "_metadata"
    )


def get_placeholder_df_with_config(
    spark: SparkSession, table_config: dict
) -> DataFrame:
    validate_config(table_config)
    fmt = table_config.get("format")
    fmt_mgr = formatmanager.get_format_manager(fmt)

    reader = spark.readStream.format("cloudFiles")
    reader = _apply_table_options(reader, table_config, fmt_mgr, is_placeholder=True)

    return reader.load(get_table_volume_path(table_config.get("name")))
