# Permissions and lifecycle

This Declarative Automation Bundles example shows combined bundle and resource permissions, target overrides, lifecycle protection, and resource-key replacement. See the [permissions documentation](https://docs.databricks.com/aws/en/dev-tools/bundles/permissions).

## Prerequisites

* Databricks CLI v1.20.0 or above.
* Workspace administrator access.
* A temporary workspace group name.
* Existing `<schema>_dev` and `<schema>_prod` Unity Catalog schemas for the pipelines.

## Usage

1. Create a temporary group.

   `databricks groups create --display-name bundle-permissions-test --profile dabs-examples`

2. Validate and deploy each target.

   `databricks bundle validate -t dev --var "temporary_group=bundle-permissions-test,catalog_name=<catalog>,schema_name=<schema>" --profile dabs-examples`

   `databricks bundle deploy -t dev --var "temporary_group=bundle-permissions-test,catalog_name=<catalog>,schema_name=<schema>" --profile dabs-examples`

   Repeat both commands with `-t prod`.

| Target | `users` from bundle | Temporary group on job | Temporary group on pipeline |
| --- | --- | --- | --- |
| dev | `CAN_VIEW` | `CAN_MANAGE_RUN` | `CAN_RUN` |
| prod | `CAN_VIEW` | `CAN_MANAGE` | `CAN_MANAGE` |

3. Run the job and pipeline for each target.

   `databricks bundle run permission_job -t dev --var "temporary_group=bundle-permissions-test,catalog_name=<catalog>,schema_name=<schema>" --profile dabs-examples`

   `databricks bundle run permission_pipeline -t dev --var "temporary_group=bundle-permissions-test,catalog_name=<catalog>,schema_name=<schema>" --profile dabs-examples`

   Repeat both commands with `-t prod`.

4. Get each job ID from `databricks bundle summary` and read its effective permissions.

   `databricks permissions get jobs <id> --profile dabs-examples`

5. Rename `permission_job` in both YAML files and deploy again to replace the job.

   Set `lifecycle.prevent_destroy` to `true` to block this replacement or cleanup.

6. Restore `lifecycle.prevent_destroy` to `false` and destroy both targets.

   `databricks bundle destroy -t dev --auto-approve --var "temporary_group=bundle-permissions-test,catalog_name=<catalog>,schema_name=<schema>" --profile dabs-examples`

   Repeat the command with `-t prod`.

7. Delete the temporary group.

   `databricks groups delete <group-id> --profile dabs-examples`
