import sys
import os

# Add parent directory to sys.path to import utils package
sys.path.insert(0, os.path.join(os.getcwd(), ".."))

from databricks.sdk import WorkspaceClient
import argparse
import json
import logging
from utils import tablemanager
from utils import envmanager

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--catalog_name", type=str, required=True)
parser.add_argument("--schema_name", type=str, required=True)
parser.add_argument("--volume_path_root", type=str, required=True)
parser.add_argument("--logging_level", type=str, required=False, default="dev")
args = parser.parse_args()

catalog_name = args.catalog_name
schema_name = args.schema_name
volume_path_root = args.volume_path_root
volume_path_data = args.volume_path_root + "/data"
volume_path_archive = args.volume_path_root + "/archive"
logging_level = logging.DEBUG if args.logging_level == "dev" else logging.INFO

# Logging
logging.basicConfig(
    level=logging_level, format="%(asctime)s [%(levelname)s] %(module)s - %(message)s"
)
logger = logging.getLogger(__name__)  # per-module logger

# Initialize workspace client
ws = WorkspaceClient()

# Dump configs to environment json early
all_configs = {
    "catalog_name": catalog_name,
    "schema_name": schema_name,
    "volume_path_root": volume_path_root,
    "volume_path_data": volume_path_data,
    "volume_path_archive": volume_path_archive,
}
with open("../configs/environment.json", "w") as f:
    json.dump(all_configs, f)
logger.info("Environment configuration file created")

# Load and validate table configurations early for fail-fast
logger.info("Loading and validating table configurations")
with open("../configs/tables.json", "r") as f:
    table_configs = json.load(f)

logger.debug(f"Found {len(table_configs)} table(s) in configuration")
try:
    tablemanager.validate_configs(table_configs)
    logger.info("All table configurations validated successfully")
except ValueError as e:
    logger.error(f"Configuration validation failed: {e}")
    raise

# Check for default storage (recommended setting)
logger.info(f"Checking default storage configuration for catalog {catalog_name}")
try:
    if not envmanager.has_default_storage(ws, catalog_name):
        logger.warning(
            f"Default storage is NOT enabled for catalog '{catalog_name}'. "
            "It is recommended to enable default storage for the catalog to ensure "
            "proper data management and storage configuration."
        )
    else:
        logger.info(f"Default storage is enabled for catalog '{catalog_name}'")
except Exception as e:
    logger.warning(f"Could not verify default storage setting: {e}")

# Set property to schema
logger.info(f"Setting property to schema {catalog_name}.{schema_name}")
logger.debug(f"Volume path root: {volume_path_root}")
logger.debug(f"Volume path data: {volume_path_data}")
ws.schemas.update(
    full_name=f"{catalog_name}.{schema_name}",
    properties={
        "filepush.volume_path_root": volume_path_root,
        "filepush.volume_path_data": volume_path_data,
        "filepush.volume_path_archive": volume_path_archive,
    },
)
logger.info(f"Schema {catalog_name}.{schema_name} configured")

# Initialize volume folder structure
logger.info(f"Initializing volume folder structure {volume_path_root}")
logger.debug(f"Creating data directory {volume_path_data}")
ws.files.create_directory(volume_path_data)
logger.debug(f"Creating archive directory {volume_path_archive}")
ws.files.create_directory(volume_path_archive)
for table in table_configs:
    table_volume_path_data = f"{volume_path_data}/{table['name']}"
    logger.debug(f"Creating table directory {table_volume_path_data}")
    ws.files.create_directory(table_volume_path_data)
    table_volume_path_archive = f"{volume_path_archive}/{table['name']}"
    logger.debug(f"Creating table archive directory {table_volume_path_archive}")
    ws.files.create_directory(table_volume_path_archive)
logger.info(f"Volume {volume_path_root} configured")

logger.info(
    "==========\n%s\n==========",
    "\n".join(f"{k}: {v}" for k, v in all_configs.items()),
)
