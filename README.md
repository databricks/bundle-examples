# Databricks Lakeflow Project Example

This project implements a classic medallion architecture using Databricks Lakeflow declarative pipelines for the entire ETL process. The medallion architecture provides a structured approach to data processing with bronze (raw), silver (cleansed), and gold (aggregated) layers, enabling reliable and scalable data transformations.

## Project Structure

* `src/`: Python source code for pipeline transformations at each medallion layer
* `framework/`: Reusable Python package with utilities for medallion architecture, dimension tables, fact tables, and configuration management
* `resources/`: Resource configurations (jobs, pipelines, schemas, volumes, etc.)
* `tests/`: Unit tests for framework functionality

## Medallion Architecture

This project uses the **TPC-H sample dataset** (provided by Databricks at `samples.tpch`) to demonstrate a complete medallion architecture implementation with dimensional modeling.

### Bronze Layer - Raw Data Ingestion
The bronze layer ingests raw data from the TPC-H source tables:
- **Source**: `samples.tpch` schema (customer, orders, lineitem, part, supplier, nation, region, partsupp)
- **Processing**:
  - Direct ingestion from source tables
  - Metadata columns added (`ingest_timestamp`)
  - No transformations or quality checks
- **Output**: Raw tables in `{bronze_catalog}.tpch` schema
- **Location**: `src/tpch_lakeflow_pipeline/transformations/bronze/`

### Silver Layer - Cleaned and Validated Data
The silver layer applies data quality rules and cleansing:
- **Source**: Bronze layer tables
- **Processing**:
  - Data quality expectations enforced (e.g., valid phone numbers, positive prices, valid status codes)
  - Primary key constraints validated
  - Referential integrity checks
  - Invalid records dropped or quarantined
- **Output**: Cleansed tables in `{silver_catalog}.tpch` schema
- **Configuration**: Expectations defined in `tpch_tables_config.json`
- **Location**: `src/tpch_lakeflow_pipeline/transformations/silver/`

### Gold Layer - Dimension Tables
The gold layer implements star schema dimensions with surrogate keys:
- **Source**: Silver layer tables with joins to enrich attributes
- **Processing**:
  1. Enrich dimensions by joining related tables (e.g., customer → nation → region)
  2. **Add surrogate keys** using `monotonically_increasing_id()` starting from 1
  3. **Add metadata columns** (`ingest_timestamp`)
  4. **Add dummy row** with surrogate key = -1 for unknown/missing dimension values
- **Dimensions**:
  - `dim_customer`: Customer attributes with nation and region
  - `dim_part`: Product/part attributes
  - `dim_supplier`: Supplier attributes with nation and region
  - `dim_calendar`: Date dimension with calendar attributes
- **Output**: Dimension tables in `{gold_catalog}.sales_model` schema
- **Location**: `src/tpch_lakeflow_pipeline/transformations/gold/dim_*.py`

### Gold Layer - Fact Table
The gold layer fact table implements the star schema with foreign key relationships:
- **Source**: Silver layer lineitem, orders, and partsupp tables
- **Processing**:
  1. Join fact sources to create base fact table with natural keys (*_key columns)
  2. **Build dimension mappings** automatically from column naming conventions
  3. **Enrich with surrogate keys** by joining to dimension tables
  4. Replace natural keys with surrogate IDs (*_id columns)
  5. Handle missing dimension keys with -1 (unknown dimension row)
  6. Reorder columns with all *_id columns first
- **Measures**:
  - Additive: quantity, extended price, discount, tax, supply cost
  - Semi-additive: order lag days (commit, receipt, ship)
  - Degenerate dimensions: order header code, order line code
- **Output**: `fact_sales` table in `{gold_catalog}.sales_model` schema
- **Location**: `src/tpch_lakeflow_pipeline/transformations/gold/fact_sales.py`

## Framework Package

The `framework/` package provides reusable utilities for implementing medallion architecture patterns:

- **`config.py`**: Configuration management for medallion layers (catalog/schema names)
- **`dimension_utils.py`**: Dimension table utilities
  - `add_surrogate_id()`: Generate surrogate keys using monotonically_increasing_id()
  - `add_dummy_row()`: Add unknown dimension row with -1 keys
- **`fact_utils.py`**: Fact table utilities
  - `build_dimension_mappings()`: Extract dimension mappings from column names
  - `enrich_with_surrogate_keys()`: Join with dimensions and replace natural keys with surrogate IDs
- **`utils.py`**: Common utilities (metadata columns, table paths, Spark config)
- **`write.py`**: DLT table creation with metadata and expectations

## Getting started

Choose how you want to work on this project:

(a) Directly in your Databricks workspace, see
    https://docs.databricks.com/dev-tools/bundles/workspace.

(b) Locally with an IDE like Cursor or VS Code, see
    https://docs.databricks.com/vscode-ext.

(c) With command line tools, see https://docs.databricks.com/dev-tools/cli/databricks-cli.html

# Using this project using the CLI

The Databricks workspace and IDE extensions provide a graphical interface for working
with this project. It's also possible to interact with it directly using the CLI:

1. Authenticate to your Databricks workspace, if you have not done so already:
    ```
    $ databricks configure
    ```

2. To deploy a development copy of this project, type:
    ```
    $ databricks bundle deploy --target dev
    ```
    (Note that "dev" is the default target, so the `--target` parameter
    is optional here.)

    This deploys everything that's defined for this project.
    For example, the default template would deploy a pipeline called
    `[dev yourname] tpch_lakeflow_pipeline` to your workspace.
    You can find that resource by opening your workpace and clicking on **Jobs & Pipelines**.

3. Similarly, to deploy a production copy, type:
   ```
   $ databricks bundle deploy --target prod
   ```
   Note the default template has a includes a job that runs the pipeline every day
   (defined in resources/sample_job.job.yml). The schedule
   is paused when deploying in development mode (see
   https://docs.databricks.com/dev-tools/bundles/deployment-modes.html).

4. To run a job or pipeline, use the "run" command:
   ```
   $ databricks bundle run
   ```
