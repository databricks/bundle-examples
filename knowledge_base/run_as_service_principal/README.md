# Run a job as a service principal

This Declarative Automation Bundles example runs a prod job as a service principal.
In dev, the job runs as the user who deploys it.
The serverless `whoami` job prints its identity, so you can see the effect of `run_as`.

For more information, see the [run_as documentation](https://docs.databricks.com/dev-tools/bundles/run-as.html).

## Prerequisites

* Databricks CLI. We tested this example with v1.20.0.
* A workspace with Unity Catalog and serverless jobs.
* A service principal in the workspace. Copy its application ID.
* A deployer group (default `bundle-deployers`) that contains the deployers and the service principal.
* The `Service Principal: User` role on the service principal for the deployer group.
* The Unity Catalog grants that your job needs, given to the service principal. `whoami` needs none.

## Usage

The bundle does not set `workspace.host`.
Select the workspace with `--profile <profile>` or the `DATABRICKS_HOST` environment variable.

1. Deploy and run the job in dev:

   ```sh
   databricks bundle deploy -t dev
   databricks bundle run -t dev whoami
   ```

2. Deploy and run the job in prod. Set the application ID of the service principal:

   ```sh
   databricks bundle validate -t prod --var service_principal_application_id=<application-id>
   databricks bundle deploy -t prod --var service_principal_application_id=<application-id>
   databricks bundle run -t prod whoami
   ```

3. Read the job output to see which identity ran the job.
   In dev, the output shows your user name.
   In prod, the output shows the application ID:

   ```
   current_user():        <application-id>
   SDK user_name:         <application-id>
   SDK display_name:      <service principal display name>
   ```

| Target | Deploys | Runs as | Owner |
| --- | --- | --- | --- |
| `dev` | You | You | You |
| `prod` | CI as the service principal, or a deployer | The service principal | The identity that deploys |

## Notes

* Do not set `run_as` in dev. The CLI accepts it, but each developer then needs the `Service Principal: User` role.
* In CI, deploy as the service principal with OAuth M2M. Set `DATABRICKS_HOST`, `DATABRICKS_CLIENT_ID`, and `DATABRICKS_CLIENT_SECRET`. Do not use personal access tokens.
* Deploy prod from one identity only. The `root_path` contains the deployer name, so a different identity makes a second copy.
* `validate -t prod` can show a recommendation to include the deployment identity in `permissions`. Add that identity to the deployer group.
* `validate -t prod` can show the warning `workspace folder has permissions not configured in bundle`. The deployer owns its home folder. The deploy continues.
