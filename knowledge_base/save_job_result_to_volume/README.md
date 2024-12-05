# Save job result to volume

This example demonstrates how to define and use a Unity Catalog Volume in a Databricks Asset Bundle.

Specifically we'll define a `top_ten_trips` job which computes the top ten NYC trips with the highest
fares and stores the result in a Unity Catalog Volume.

The bundle also defines a Volume and the associated schema to which we'll store the results to.

## Prerequisites

* Databricks CLI v0.236.0 or above

## Usage

Update the `host` field under `workspace` in `databricks.yml` to the Databricks workspace you wish to deploy to.

Run `databricks bundle deploy` to deploy the job.

Run `databricks bundle run top_ten_trips` to run the job and store the results in UC volume.
