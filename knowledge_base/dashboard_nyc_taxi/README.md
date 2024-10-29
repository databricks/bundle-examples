# Dashboard for NYC Taxi Trip Analysis

This example demonstrates how to define an AI/BI dashboard in a Databricks Asset Bundle.

It includes and deploys the sample __NYC Taxi Trip Analysis__ dashboard to a Databricks workspace.

For more information about AI/BI dashboards, please refer to the [documentation](https://docs.databricks.com/dashboards/index.html).

## Prerequisites

* Databricks CLI v0.232.0 or above

## Usage

Modify `databricks.yml`:
* Update the `host` field under `workspace` to the Databricks workspace to deploy to.
* Update the `warehouse` field under the `warehouse_id` variable to match the SQL warehouse you wish to use.

Run `databricks bundle deploy` to deploy the dashboard.

Run `databricks bundle open` to open the deployed dashboard in your browser.

Alternatively, run `databricks bundle summary` to display its URL.

### Visual modification

Dashboards are inherently visual, so you may want to use the web interface to modify the dashboard.
Any modifications that are done through the web interface won't automatically be reflected in the `.lvdash.json` file.
You can, however, run a dedicated bundle command to retrieve these changes and update your `.lvdash.json` file.

To retrieve the updated `.lvdash.json` file, run:

```sh
databricks bundle generate dashboard --resource nyc_taxi_trip_analysis --force
```

To continuously poll and retrieve the updated `.lvdash.json` file when it changes, run:

```sh
databricks bundle generate dashboard --resource nyc_taxi_trip_analysis --force --watch
```

Any remote modifications of a dashboard are noticed by the `deploy` command and require
you to explicitly acknowledge that remote changes are overwritten by local changes.
It is therefore recommended to run the `generate` command before running the `deploy` command.
Otherwise, you may lose your remote changes.

### Manual modification

You can modify the `.lvdash.json` file directly and redeploy to observe your changes.
