# Dashboard for NYC Taxi Trip Analysis

This example shows how to define an AI/BI dashboard within a Databricks Asset Bundle, set up a job to capture a snapshot of the dashboard, and email it to a subscriber.

It deploys the sample __NYC Taxi Trip Analysis__ dashboard to a Databricks workspace and configures a daily schedule to run the dashboard and send the snapshot via email.

For more information about AI/BI dashboards, please refer to the [documentation](https://docs.databricks.com/dashboards/index.html).

## Prerequisites

- For creating dashboard: Databricks CLI v0.232.0 or above
- For dashboard snapshot task: Databricks CLI v0.250.0 or above

## Usage

#### Step1: Modify `databricks.yml`:

- Update the `host` field under `workspace` to the Databricks workspace to deploy to.
- Update the `warehouse` field under `warehouse_id` to the name of the SQL warehouse to use.

#### Step2: Modify `resources/nyc_taxi_trip_analysis.job.yml`:

- Update the `user_name` field under `subscribers` to the dashboard subscriber's email

#### Step3: Deploy the dashboard

Run `databricks bundle deploy` to deploy the dashboard.

Run `databricks bundle open` to navigate to the deployed dashboard in your browser. Alternatively, run `databricks bundle summary` to display its URL.
Note:
At this moment, we have created the AI/BI dashboard and sets up the snapshot job to run daily at 8 AM, capture a snapshot of the dashboard, and send it via email to the specified subscriber.

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

Any remote modifications of a dashboard are noticed by the `deploy` command and require
you to acknowledge that remote changes can be overwritten by local changes.
It is therefore recommended to run the `generate` command before running the `deploy` command.
Otherwise, you may lose your remote changes.

### Manual modification

You can modify the `.lvdash.json` file directly and redeploy to observe your changes.
