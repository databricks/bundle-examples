"""Test validate_table_metadata with example config files"""
from framework.utils import validate_table_metadata
import json
from pathlib import Path

def test_config_file(file_path, label):
    """Test a single config file"""
    file = Path(file_path)
    if not file.exists():
        print(f"{label}: File not found")
        return
    
    with open(file) as f:
        configs = json.load(f)
    
    # Handle both single dict and list of dicts
    if isinstance(configs, dict):
        configs = [configs]
    
    for idx, config in enumerate(configs):
        try:
            validate_table_metadata(config, f"{label}[{idx}]")
            dest = config.get("destination", "unknown")
            print(f"✓ {label}[{idx}] ({dest}): VALID")
        except ValueError as e:
            print(f"✗ {label}[{idx}]: {e}")

print("Testing Bronze Configs:")
print("-" * 60)
test_config_file(
    "src/pipelines/pipeline_tpch/transformations/bronze/metadata/tpch_bronze_tables.json",
    "bronze_tables_metadata"
)
test_config_file(
    "src/pipelines/pipeline_tpch/transformations/bronze/metadata/tpch_supplier.json",
    "tpch_supplier"
)

print("\nTesting Silver Configs:")
print("-" * 60)
test_config_file(
    "src/pipelines/pipeline_tpch/transformations/silver/metadata/tpch_silver_tables.json",
    "silver_tables"
)

print("\nSummary:")
print("-" * 60)
print("Validation complete! All configs tested.")
