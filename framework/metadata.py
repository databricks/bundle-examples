"""
Metadata utilities for loading and validating table configurations.

This module provides functions to load table configuration files and validate their schema.
"""

import json
from pathlib import Path
from typing import List, Set

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# Expected keys in table configuration
REQUIRED_KEYS: Set[str] = {
    "source", 
    "destination", 
    "primary_keys"
}

# Optional keys in table configuration
OPTIONAL_KEYS: Set[str] = {
    "description",
    "expectations_warn",
    "expectations_fail_update",
    "expectations_drop_row",
    "table_properties",
}

ALLOWED_KEYS: Set[str] = REQUIRED_KEYS | OPTIONAL_KEYS


def validate_table_metadata(config: dict, filename: str = "") -> bool:
    """
    Validate the schema of a table configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
        filename: Optional filename for better error messages
        
    Returns:
        bool: True if valid, raises ValueError if invalid
        
    Raises:
        ValueError: If the configuration schema is invalid
    """
    file_info = f" in '{filename}'" if filename else ""
    
    # Check if it's a dictionary
    if not isinstance(config, dict):
        raise ValueError(f"Configuration entry{file_info} must be a dictionary")
    
    # Check for unexpected keys
    unexpected_keys = set(config.keys()) - ALLOWED_KEYS
    if unexpected_keys:
        raise ValueError(
            f"Configuration entry{file_info} contains unexpected keys: {sorted(unexpected_keys)}. "
            f"Allowed keys are: {sorted(ALLOWED_KEYS)}"
        )
    
    # Required fields
    for required_key in REQUIRED_KEYS:
        if required_key not in config:
            raise ValueError(f"Configuration entry{file_info} is missing required '{required_key}' field")
    
    # Validate types
    if not isinstance(config["source"], str):
        raise ValueError(f"'source'{file_info} must be a string")
    
    if not isinstance(config["destination"], str):
        raise ValueError(f"'destination'{file_info} must be a string")
    
    if not isinstance(config["primary_keys"], list):
        raise ValueError(f"'primary_keys'{file_info} must be a list")
    
    # Validate primary_keys list contains strings
    for idx, key in enumerate(config["primary_keys"]):
        if not isinstance(key, str):
            raise ValueError(f"primary_keys[{idx}]{file_info} must be a string")
    
    # Validate optional fields
    if "expectations_warn" in config and not isinstance(config["expectations_warn"], dict):
        raise ValueError(f"'expectations_warn'{file_info} must be a dictionary")
    
    if "expectations_fail_update" in config and not isinstance(config["expectations_fail_update"], dict):
        raise ValueError(f"'expectations_fail_update'{file_info} must be a dictionary")
    
    if "expectations_drop_row" in config and not isinstance(config["expectations_drop_row"], dict):
        raise ValueError(f"'expectations_drop_row'{file_info} must be a dictionary")
    
    if "table_properties" in config and not isinstance(config["table_properties"], dict):
        raise ValueError(f"'table_properties'{file_info} must be a dictionary")
    
    if "description" in config and not isinstance(config["description"], str):
        raise ValueError(f"'description'{file_info} must be a string")
    
    return True


def load_table_configs(config_dir: str, validate: bool = True) -> list:
    """
    Load and merge all YAML or JSON configuration files from a directory.
    Each file should contain a 'tables' key with a list of table configurations,
    or a list/single dictionary for backwards compatibility.
    Optionally validates the schema of each configuration entry.
    
    Args:
        config_dir: Path to the directory containing configuration files (.yml, .yaml, or .json)
        validate: If True, validate schema of each config entry (default: True)
        
    Returns:
        list: Combined list of all table configurations from all files
        
    Raises:
        ValueError: If validation is enabled and a config has invalid schema
        FileNotFoundError: If the config directory doesn't exist
    """
    config_dir = Path(config_dir)
    
    if not config_dir.exists():
        raise FileNotFoundError(f"Configuration directory not found: {config_dir}")
    
    if not config_dir.is_dir():
        raise ValueError(f"Path is not a directory: {config_dir}")
    
    all_configs = []
    
    # Find all config files (YAML and JSON)
    yaml_files = sorted(list(config_dir.glob("*.yml")) + list(config_dir.glob("*.yaml")))
    json_files = sorted(config_dir.glob("*.json"))
    config_files = yaml_files + json_files
    
    if not config_files:
        print(f"Warning: No configuration files found in {config_dir}")
        return all_configs
    
    for config_file in config_files:
        try:
            with open(config_file, "r") as f:
                if config_file.suffix in [".yml", ".yaml"]:
                    if not YAML_AVAILABLE:
                        raise ImportError("PyYAML is required to load YAML files. Install it with: pip install pyyaml")
                    file_data = yaml.safe_load(f)
                else:
                    file_data = json.load(f)
            
            # Handle YAML structure with 'tables' key
            if isinstance(file_data, dict) and "tables" in file_data:
                file_configs = file_data["tables"]
            # Convert single dict to list for uniform processing
            elif isinstance(file_data, dict):
                file_configs = [file_data]
            elif isinstance(file_data, list):
                file_configs = file_data
            else:
                raise ValueError(f"File '{config_file.name}' must contain a 'tables' key, a dictionary, or a list of dictionaries")
            
            # Validate each config entry if requested
            if validate:
                for idx, config in enumerate(file_configs):
                    validate_table_metadata(config, f"{config_file.name}[{idx}]")
            
            # Add all configs from this file
            all_configs.extend(file_configs)
                
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ValueError(f"Invalid format in file '{config_file.name}': {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error loading config file '{config_file.name}': {str(e)}")
    
    print(f"Loaded {len(config_files)} configuration file(s) with {len(all_configs)} table(s)")
    
    return all_configs
