# Run a job as a service principal

This Declarative Automation Bundles example runs a prod job as a service principal.
In dev, the job runs as the user who deploys it.
The serverless `whoami` job prints its identity, so you can see the effect of `run_as`.

For more information, see the [run_as documentation](https://docs.databricks.com/dev-tools/bundles/run-as.html).

## Prerequisites

* Databricks CLI v1.20.0 or above
* A workspace with Unity Catalog and serverless jobs.
* A service principal in the workspace. Copy its application ID.
* A deployer group (default `bundle-deployers`) that contains the deployers and the service principal.
* The `Service Principal: User` role on the service principal for the deployer group.
* The Unity Catalog grants that your job needs, given to the service principal. `whoami` needs none.

## Usage

The bundle does not set `workspace.host`.
Select the workspace with `--profile <profile>` or the `DATABRICKS_HOST` environment variable.

1. Deploy the bundle to dev: `databricks bundle deploy -t dev`
2. Run the job in dev: `databricks bundle run -t dev whoami`
3. In CI, authenticate as the service principal. See the Notes.
4. In CI, set the variable once: `export BUNDLE_VAR_service_principal_application_id=<application-id>`
5. In CI, deploy the bundle to prod: `databricks bundle deploy -t prod`
6. In CI, run the job in prod: `databricks bundle run -t prod whoami`
7. Read the job output to see which identity ran the job.

Output in prod (in dev, the lines show your user name):

```
current_user():        <application-id>
SDK user_name:         <application-id>
SDK display_name:      <service principal display name>
```

| Target | Deploys | Runs as | `IS_OWNER` set by the bundle |
| --- | --- | --- | --- |
| `dev` | You | You | You |
| `prod` | The service principal, from CI | The service principal | The deploying identity (the service principal) |

## Notes

* Do not set `run_as` in dev. The CLI accepts it, but each developer then needs the `Service Principal: User` role.
* In CI, deploy `prod` as the service principal with OAuth M2M. Set `DATABRICKS_HOST`, `DATABRICKS_CLIENT_ID`, and `DATABRICKS_CLIENT_SECRET`. Do not use personal access tokens.
* Each deployer needs the `Service Principal: User` role. The `Service Principal: Manager` role is not sufficient. Without it, the deploy fails with `Cannot bind the service principal provided in 'run_as' field`.
* Deploy `prod` from one identity. Another identity that is not a workspace admin cannot take over the job. The deploy fails with `only workspace admins can change the owner of a job`.
* A new deploy to the same target updates the same resources. With the same variable, `databricks bundle destroy -t prod` removes only the job of this bundle.
* The bundle works on AWS, Azure, and GCP with serverless compute. We did not test classic compute. The bundle contains no secrets: the OAuth M2M secret stays in the CI secret store. The job has no schedule.
