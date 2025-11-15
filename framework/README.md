# Lakehouse Framework

A Python package for managing medallion architecture implementations using Databricks Lakeflow declarative pipelines.

## Overview

This package provides utilities and core functionality for implementing a medallion architecture (bronze, silver, gold layers) with Databricks Delta Live Tables.

## Features

- **Configuration Management**: Easy configuration of catalog and schema names for each medallion layer
- **Utility Functions**: Helper functions for constructing fully qualified table paths
- **Spark Integration**: Seamless integration with Spark configuration for pipeline parameters

## Installation

Install the package in development mode:

```bash
pip install -e .
```

Or install with development dependencies:

```bash
pip install -e ".[dev]"
```

## Usage

### Using the Configuration

```python
from lakehouse_framework.config import Config

# Load configuration from Spark config (in a pipeline)
config = Config.from_spark_config()

# Get layer paths
bronze_path = config.get_layer_path("bronze")  # catalog.bronze
silver_path = config.get_layer_path("silver")  # catalog.silver
gold_path = config.get_layer_path("gold")      # catalog.gold
```

### Using Utility Functions

```python
from lakehouse_framework.utils import get_table_path, get_catalog_schema

# Construct fully qualified paths
catalog_schema = get_catalog_schema("my_catalog", "my_schema")
table_path = get_table_path("my_catalog", "my_schema", "my_table")
```

### Running the CLI

```bash
python -m lakehouse_framework.main
```

Or using the installed script:

```bash
main
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

This project uses Black for code formatting:

```bash
black src/ tests/
```

## Project Structure

```
src/lakehouse_framework/
├── __init__.py      # Package initialization
├── main.py          # Main entry point
├── config.py        # Configuration management
└── utils.py         # Utility functions

tests/
└── test_lakehouse_framework.py  # Unit tests
```

## Dependencies

- Python >= 3.10, <= 3.13
- PySpark (via Databricks runtime)

### Development Dependencies

- pytest
- databricks-dlt
- databricks-connect (15.4.x)
