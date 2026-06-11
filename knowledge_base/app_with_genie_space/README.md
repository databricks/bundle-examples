# Databricks app using a Genie space

This example demonstrates how to define a Databricks app that uses a Genie space in a Declarative Automation Bundle.

It deploys a Genie space for the `samples.nyctaxi.trips` [table](https://docs.databricks.com/aws/en/discover/databricks-datasets#nyctaxi) and a Flask app that lets users ask the space questions in natural language through the [Genie Conversation API](https://docs.databricks.com/genie/conversation-api.html).

For more information about Databricks Apps, see the [documentation](https://docs.databricks.com/aws/en/dev-tools/databricks-apps).
For more information about Genie, see the [documentation](https://docs.databricks.com/genie/index.html).

## Prerequisites

* Databricks CLI v1.3.0 or above.
* Genie spaces can only be deployed with the [direct deployment engine](https://docs.databricks.com/dev-tools/bundles/direct) (`engine: direct`), which is the default for new deployments since CLI v1.3.0.

## Usage

1. Modify `databricks.yml`:
   - Update the `host` field to your Databricks workspace URL
   - Update the `warehouse` field to the name of your SQL warehouse

2. Deploy the bundle:
   ```sh
   databricks bundle deploy
   ```

3. Run the app:
   ```sh
   databricks bundle run genie_assistant
   ```

4. Open the app in your browser:
   ```sh
   databricks bundle open genie_assistant
   ```
   Alternatively, run `databricks bundle summary` to display its URL.

## How it works

* `resources/nyc_taxi_genie.genie_space.yml` defines the Genie space, with its data sources, instructions, and sample questions stored in `src/nyc_taxi_genie.geniespace.json`.
* `resources/genie_assistant.app.yml` declares the Genie space as an app resource. This grants the app's service principal `CAN_RUN` permission on the space:
  ```yaml
  resources:
    - name: "genie-space"
      genie_space:
        name: "NYC Taxi Trip Analysis"
        space_id: ${resources.genie_spaces.nyc_taxi_genie.space_id}
        permission: CAN_RUN
  ```
* The `config` block in `resources/genie_assistant.app.yml` injects the space ID into the app as the `GENIE_SPACE_ID` environment variable using `value_from: "genie-space"`.
* `app/app.py` sends each question to the space with `w.genie.start_conversation_and_wait(...)` and renders the text answer or the generated SQL and its results.

Note that the app queries Genie with its own service principal identity: in addition to the `CAN_RUN` permission on the space granted by the bundle, the service principal must be able to use the SQL warehouse and read the tables that back the space. If access to the `samples` catalog is restricted for service principals in your workspace, point the space at a table the app can read.
