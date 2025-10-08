import os
import json
from databricks.sdk import WorkspaceClient

def get_config() -> dict:
  json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "environment.json")
  if not os.path.exists(json_path):
    raise RuntimeError(f"Missing environment file: {json_path}. This should be run in a workspace, not locally. And make sure to run `databricks bundle run configuration_job` at least once.")
  with open(json_path, "r") as f:
    configs = json.load(f)
  return configs

def has_default_storage() -> bool:
  catalog = get_config()["catalog_name"]

  w = WorkspaceClient()

  # Try SDK model first
  info = w.catalogs.get(catalog)
  storage_root = getattr(info, "storage_root", None)
  storage_location = getattr(info, "storage_location", None)
  props = getattr(info, "properties", {}) or {}

  # Some workspaces expose fields only via raw JSON; fall back if all empty
  if not (storage_root or storage_location or props):
    j = w.api_client.do("GET", f"/api/2.1/unity-catalog/catalogs/{catalog}")
    storage_root = j.get("storage_root") or j.get("storageLocation")
    storage_location = j.get("storage_location") or j.get("storageLocation")
    props = j.get("properties", {}) or {}

  # Heuristics: any of these indicates “default storage” is set
  return bool(
    storage_root or
    storage_location or
    props.get("defaultManagedLocation") or
    props.get("delta.defaultLocation")
  )
