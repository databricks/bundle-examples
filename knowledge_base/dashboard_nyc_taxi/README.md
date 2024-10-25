# Dashboard for NYC Taxi Trip Analysis

This example demonstrates how to model an AI/BI dashboard in a Databricks Asset Bundle.

For more information about AI/BI dashboards, please refer to the [documentation](https://docs.databricks.com/en/dashboards/index.html#dashboards).

## Prerequisites

* Databricks CLI v0.232.0 or above

## Usage

First:
* Update the `host` field under `workspace` in `databricks.yml` to the Databricks workspace you wish to deploy to.
* Update the `warehouse` field under the `warehouse_id` variable to match the SQL warehouse you wish to use for your dashboard.

Run `databricks bundle deploy` to deploy the dashboard.

Run `databricks bundle open` to open the deployed dashboard in your browser.

Alternatively, run `databricks bundle summary` to display its URL.
