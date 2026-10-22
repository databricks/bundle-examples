# Bind existing resources

This Declarative Automation Bundles example puts an existing job and dashboard under bundle management.
It generates the configuration, binds it to the workspace resources, deploys it, and then unbinds it.

For more information, see the [bind documentation](https://docs.databricks.com/dev-tools/bundles/migrate-resources.html).

## Prerequisites

* Databricks CLI v1.20.0 or above
* A workspace with serverless jobs and a SQL warehouse named `Serverless Starter Warehouse`.
* An existing job and an existing AI/BI dashboard. Copy their IDs from the workspace URLs.

## Usage

1. Generate the job configuration. This replaces the sample files in `resources/` and `src/`:
   `databricks bundle generate job --existing-job-id <job-id> --key existing_job --force --profile <profile>`
2. Generate the dashboard configuration:
   `databricks bundle generate dashboard --existing-id <dashboard-id> --key existing_dashboard --force --profile <profile>`
3. In `resources/existing_dashboard.dashboard.yml`, replace the literal `warehouse_id` with `${var.warehouse_id}`.
4. In the same file, set `parent_path: ${var.dashboard_parent_path}`.
5. Set the folder of the existing dashboard: `export BUNDLE_VAR_dashboard_parent_path=/Workspace/Users/<user>/<folder>`
6. Bind the job: `databricks bundle deployment bind existing_job <job-id> -t prod --profile <profile>`
7. Bind the dashboard: `databricks bundle deployment bind existing_dashboard <dashboard-id> -t prod --profile <profile>`
8. Show the changes that the deploy makes: `databricks bundle plan -t prod --profile <profile>`
9. Deploy the bundle: `databricks bundle deploy -t prod --profile <profile>`
10. Run the job: `databricks bundle run existing_job -t prod --profile <profile>`
11. Unbind the job: `databricks bundle deployment unbind existing_job -t prod --profile <profile>`
12. Unbind the dashboard: `databricks bundle deployment unbind existing_dashboard -t prod --profile <profile>`
13. Remove the bundle files: `databricks bundle destroy -t prod --profile <profile>`

After step 13, the job and the dashboard stay in the workspace with the bundle settings.
The job notebook path points to the deleted bundle files. Set a new notebook path before you run the job again.

| Step | Effect on the workspace resource |
| --- | --- |
| `bind` | No change. The bundle state records the resource ID. |
| `plan` | Shows drift. Changes made in the UI appear as `update`. |
| `deploy` | Overwrites the resource with the bundle configuration. The ID stays the same. |
| `unbind` | No change. The bundle state forgets the resource ID. |
| `destroy` | Deletes only the bundle files. Unbound resources stay. |
