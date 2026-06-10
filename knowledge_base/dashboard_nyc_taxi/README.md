# Dashboard for NYC Taxi Trip Analysis

This example shows how to define a Declarative Automation Bundle with an AI/BI dashboard, a job that captures a snapshot of the dashboard and emails it to a subscriber, and a Genie space to ask questions about the same data in natural language.

It deploys the sample __NYC Taxi Trip Analysis__ dashboard to a Databricks workspace and configures a daily schedule to run the dashboard and send the snapshot in email to a specified email address.

For more information about AI/BI dashboards, please refer to the [documentation](https://docs.databricks.com/dashboards/index.html).
For more information about Genie, please refer to the [documentation](https://docs.databricks.com/genie/index.html).

## Prerequisites

This example includes a Genie space, which requires Databricks CLI v1.3.0 or above. Genie spaces can only be deployed with the [direct deployment engine](https://docs.databricks.com/dev-tools/bundles/direct) (`engine: direct`), which is the default for new deployments since CLI v1.3.0.

## Usage

1. Modify `databricks.yml`:
    - Update the `host` field under `workspace` to the Databricks workspace to deploy to.
    - Update the `warehouse` field under `warehouse_id` to the name of the SQL warehouse to use.

2. Modify `resources/nyc_taxi_trip_analysis.job.yml`:
    - Update the `user_name` field under `subscribers` to the dashboard subscriber's email.

3. Deploy the dashboard:
    - Run `databricks bundle deploy` to deploy the dashboard.
    - Run `databricks bundle open` to navigate to the deployed dashboard in your browser. Alternatively, run `databricks bundle summary` to display its URL.

The AI/BI dashboard is created and the snapshot job is set to run daily at 8 AM, which captures a snapshot of the dashboard, and sends it in email to the specified subscriber.

The bundle also deploys the __NYC Taxi Trip Analysis Genie__ space defined in `resources/nyc_taxi_genie.genie_space.yml`, where users can ask questions about the same data in natural language. Its data sources, instructions, and sample questions are stored in `src/nyc_taxi_genie.geniespace.json`.

### Visual modification

You can use the Databricks UI to modify the dashboard, but any modifications made through the UI will not be applied to the bundle `.lvdash.json` file unless you explicitly update it.

To update the local bundle `.lvdash.json` file, run:

```sh
databricks bundle generate dashboard --resource nyc_taxi_trip_analysis --force
```

To continuously poll and retrieve the updated `.lvdash.json` file when it changes, run:

```sh
databricks bundle generate dashboard --resource nyc_taxi_trip_analysis --force --watch
```

The same workflow applies to the Genie space and its `.geniespace.json` file:

```sh
databricks bundle generate genie-space --resource nyc_taxi_genie --force
```

Any remote modifications of a dashboard or Genie space are noticed by the `deploy` command and require
you to acknowledge that remote changes can be overwritten by local changes.
It is therefore recommended to run the `generate` command before running the `deploy` command.
Otherwise, you may lose your remote changes.

### Manual modification

You can modify the `.lvdash.json` or `.geniespace.json` files directly and redeploy to observe your changes.
