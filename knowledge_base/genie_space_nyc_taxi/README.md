# Genie space for NYC Taxi Trip Analysis

This example shows how to define a Genie space using Declarative Automation Bundles. Genie spaces let business users ask questions about data in natural language.

It deploys a Genie space that answers questions about the `samples.nyctaxi.trips` [table](https://docs.databricks.com/aws/en/discover/databricks-datasets#nyctaxi).

For more information about Genie, see the [Databricks documentation](https://docs.databricks.com/genie/index.html).

## Prerequisites

* Databricks CLI v1.3.0 or above.
* Genie spaces can only be deployed with the [direct deployment engine](https://docs.databricks.com/dev-tools/bundles/direct) (`engine: direct`), which is the default for new deployments since CLI v1.3.0.

## Usage

1. Modify `databricks.yml`:
   - Update the `host` field to your Databricks workspace URL
   - Update the `warehouse` field to the name of your SQL warehouse

2. Deploy the Genie space:
   ```sh
   databricks bundle deploy
   ```

3. Open the deployed Genie space in your browser:
   ```sh
   databricks bundle open
   ```
   Alternatively, run `databricks bundle summary` to display its URL.

## Key configuration

The Genie space configuration in `resources/nyc_taxi_genie.genie_space.yml` includes:

- **title**: Display name of the Genie space
- **file_path**: Path to the `.geniespace.json` file that holds the serialized definition of the space: its data sources, instructions, and sample questions. Instead of `file_path`, the definition can also be inlined in YAML under `serialized_space`.
- **warehouse_id**: The SQL warehouse used to run the queries that Genie generates
- **permissions**: Who can use the space (`CAN_VIEW`, `CAN_RUN`, `CAN_EDIT`, `CAN_MANAGE`)

## Importing an existing Genie space

To bring a Genie space that was authored in the Databricks UI into a bundle, run:

```sh
databricks bundle generate genie-space --existing-id <space-id>
```

This writes the configuration to `resources/<key>.genie_space.yml` and the space definition to `src/<key>.geniespace.json`.

## Visual modification

You can use the Databricks UI to modify the deployed Genie space, but any modifications made through the UI will not be applied to the bundle `.geniespace.json` file unless you explicitly update it.

To update the local bundle `.geniespace.json` file, run:

```sh
databricks bundle generate genie-space --resource nyc_taxi_genie --force
```

To continuously poll and retrieve the updated `.geniespace.json` file when it changes, run:

```sh
databricks bundle generate genie-space --resource nyc_taxi_genie --force --watch
```

Any remote modifications of a Genie space are noticed by the `deploy` command and require
you to acknowledge that remote changes can be overwritten by local changes.
It is therefore recommended to run the `generate` command before running the `deploy` command.
Otherwise, you may lose your remote changes.

### Manual modification

You can modify the `.geniespace.json` file directly and redeploy to observe your changes.
