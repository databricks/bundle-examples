"""
Metadata utilities for loading and validating table configurations.

This module provides functions to load table configuration files and validate their schema.
"""

import json
from pathlib import Path
from typing import List, Set


# Expected keys in table configuration
REQUIRED_KEYS: Set[str] = {
    "source", 
    "destination", 
    "primary_keys"
}

OPTIONAL_KEYS: Set[str] = {
    "description",
    "tags",
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
    
    if "tags" in config:
        if not isinstance(config["tags"], list):
            raise ValueError(f"'tags'{file_info} must be a list")
        # Validate tags list contains strings
        for idx, tag in enumerate(config["tags"]):
            if not isinstance(tag, str):
                raise ValueError(f"tags[{idx}]{file_info} must be a string")
    
    return True


def load_table_configs(config_dir: str, validate: bool = True) -> list:
    """
    Load and merge all JSON configuration files from a directory.
    Each JSON file should contain either a list of table configuration dictionaries or a single dictionary.
    Optionally validates the schema of each configuration entry.
    
    Args:
        config_dir: Path to the directory containing JSON configuration files
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
    json_files = sorted(config_dir.glob("*.json"))
    
    if not json_files:
        print(f"Warning: No JSON files found in {config_dir}")
        return all_configs
    
    for json_file in json_files:
        try:
            with open(json_file, "r") as f:
                file_configs = json.load(f)
            
            # Convert single dict to list for uniform processing
            if isinstance(file_configs, dict):
                file_configs = [file_configs]
            elif not isinstance(file_configs, list):
                raise ValueError(f"File '{json_file.name}' must contain either a dictionary or a list of dictionaries")
            
            # Validate each config entry if requested
            if validate:
                for idx, config in enumerate(file_configs):
                    validate_table_metadata(config, f"{json_file.name}[{idx}]")
            
            # Add all configs from this file
            all_configs.extend(file_configs)
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file '{json_file.name}': {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error loading config file '{json_file.name}': {str(e)}")
    
    print(f"Loaded {len(json_files)} configuration file(s) with {len(all_configs)} table(s)")
    
    return all_configs
