# Direct engine migration

This Declarative Automation Bundles example migrates a serverless job from the Terraform engine to the direct engine.

See the [direct engine documentation](https://docs.databricks.com/dev-tools/bundles/direct).

## Prerequisites

* Databricks CLI v1.19.x for the Terraform deployment. Version 1.20.0 removes the Terraform engine.
* Databricks CLI v1.20.0 or above for the migration

## Usage

| Engine | Local state | Workspace state |
| --- | --- | --- |
| Terraform | `.databricks/bundle/dev/terraform/terraform.tfstate` | `<root_path>/state/terraform.tfstate` |
| Direct | `.databricks/bundle/dev/resources.json` | `<root_path>/state/resources.json` |

1. Use Databricks CLI v1.19.x to deploy with the Terraform engine.

   ```text
   DATABRICKS_BUNDLE_ENGINE=terraform databricks bundle deploy
   ```

2. Record the job ID with the Terraform engine.

   ```text
   DATABRICKS_BUNDLE_ENGINE=terraform databricks bundle summary --output json
   ```

3. Upgrade to Databricks CLI v1.20.0 or above. Migrate the local state. `databricks bundle deploy` also migrates the state automatically.

   ```text
   databricks bundle deployment migrate
   ```

4. Confirm that the migration plan has zero changes.

   ```text
   databricks bundle plan
   ```

5. Deploy and run the job. Confirm that the job ID is unchanged.

   ```text
   databricks bundle deploy
   databricks bundle run direct_engine_migration
   databricks bundle summary --output json
   ```

6. Confirm that the deployed bundle still has zero changes.

   ```text
   databricks bundle plan
   ```

7. Remove the job and workspace files.

   ```text
   databricks bundle destroy --auto-approve
   ```
