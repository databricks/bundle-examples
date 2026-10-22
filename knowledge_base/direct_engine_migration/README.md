# Direct engine migration

This Declarative Automation Bundles example migrates a serverless job from the Terraform engine to the direct engine. See the [direct engine documentation](https://docs.databricks.com/dev-tools/bundles/direct).

## Prerequisites

* Databricks CLI v1.19.x for the initial Terraform deployment
* Databricks CLI v1.20.0 or above for migration and later commands
* A Databricks workspace configuration profile named `dabs-examples`

## Usage

| Engine | Local state | Workspace state |
| --- | --- | --- |
| Terraform | `.databricks/bundle/dev/terraform/terraform.tfstate` | `<root_path>/state/terraform.tfstate` |
| Direct | `.databricks/bundle/dev/resources.json` | `<root_path>/state/resources.json` |

1. Use Databricks CLI v1.19.x to validate the bundle with the Terraform engine.

   ```text
   DATABRICKS_BUNDLE_ENGINE=terraform databricks bundle validate --profile dabs-examples
   ```

2. Deploy and run the job with the Terraform engine.

   ```text
   DATABRICKS_BUNDLE_ENGINE=terraform databricks bundle deploy --profile dabs-examples
   DATABRICKS_BUNDLE_ENGINE=terraform databricks bundle run direct_engine_migration --profile dabs-examples
   ```

3. Record the job ID and inspect `.databricks/bundle/dev/terraform/terraform.tfstate`.

   ```text
   DATABRICKS_BUNDLE_ENGINE=terraform databricks bundle summary --output json --profile dabs-examples
   ```

4. Upgrade to Databricks CLI v1.20.0 or above. Migrate the local state.

   ```text
   DATABRICKS_BUNDLE_ENGINE=direct databricks bundle deployment migrate --profile dabs-examples
   ```

5. Inspect the direct state at `.databricks/bundle/dev/resources.json`.

6. Confirm that the plan has zero changes. Deploy and run the same job ID.

   ```text
   DATABRICKS_BUNDLE_ENGINE=direct databricks bundle plan --profile dabs-examples
   DATABRICKS_BUNDLE_ENGINE=direct databricks bundle deploy --profile dabs-examples
   DATABRICKS_BUNDLE_ENGINE=direct databricks bundle run direct_engine_migration --profile dabs-examples
   ```

7. Remove the job and workspace files.

   ```text
   DATABRICKS_BUNDLE_ENGINE=direct databricks bundle destroy --auto-approve --profile dabs-examples
   ```
