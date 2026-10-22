# Complex variables and lookups

This Declarative Automation Bundles example shows `type: complex` variables and `lookup` variables.
It resolves warehouse, cluster policy, service principal, cluster, job, and metastore IDs by name.
A small serverless job prints the resolved IDs.

For more information, see the [variables documentation](https://docs.databricks.com/aws/en/dev-tools/bundles/variables).

## Prerequisites

* Databricks CLI v1.20.0 or above
* A SQL warehouse, cluster policy, service principal, cluster, and job in the workspace
* Update each `lookup` name in `databricks.yml` to match those resources
* Metastore lookup needs account admin, or set `BUNDLE_VAR_metastore_id`

## Usage

1. Set lookup names in `databricks.yml` to resources in your workspace.

2. Optional: override the complex `environment_spec` with a file.

   Precedence is CLI `--var` > `BUNDLE_VAR_*` > `.databricks/bundle/<target>/variable-overrides.json` > defaults.
   Complex variables use the overrides file or target defaults. They do not use `BUNDLE_VAR_*`.

   ```bash
   mkdir -p .databricks/bundle/dev
   printf '%s\n' '{"environment_spec":{"environment_version":"4"}}' > .databricks/bundle/dev/variable-overrides.json
   ```

3. Optional: override a lookup ID: `export BUNDLE_VAR_warehouse_id=<warehouse-id>`

4. Validate and deploy: `databricks bundle validate -t dev` then `databricks bundle deploy -t dev`

5. Run the job: `databricks bundle run -t dev lookup_demo`

6. Deploy and run production: `databricks bundle deploy -t prod` then `databricks bundle run -t prod lookup_demo`

7. Remove resources: `databricks bundle destroy -t dev --auto-approve` and `databricks bundle destroy -t prod --auto-approve`

| Override source | Example |
| --- | --- |
| CLI flag | `--var="warehouse_id=..."` |
| Environment | `BUNDLE_VAR_warehouse_id=<id>` |
| Overrides file | `.databricks/bundle/dev/variable-overrides.json` |
| Default / target | `variables` in `databricks.yml` |
