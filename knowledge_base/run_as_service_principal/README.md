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
* Deployers need the `Service Principal: User` role on the service principal.

## Usage

1. Deploy the bundle to dev: `databricks bundle deploy -t dev --profile <profile>`
2. Run the job in dev: `databricks bundle run -t dev whoami --profile <profile>`
3. In CI, authenticate as the service principal with OAuth M2M and set the application ID:

   ```sh
   export DATABRICKS_HOST=https://<workspace-host>
   export DATABRICKS_CLIENT_ID=<application-id>
   export DATABRICKS_CLIENT_SECRET=<secret from the CI secret store>
   export BUNDLE_VAR_service_principal_application_id=<application-id>
   ```

4. In CI, deploy the bundle to prod: `databricks bundle deploy -t prod`
5. In CI, run the job in prod: `databricks bundle run -t prod whoami`
6. Read the job output. In dev, it shows your user name. In prod, it shows the service principal:

   ```
   current_user():        <application-id>
   SDK user_name:         <application-id>
   SDK display_name:      <service principal display name>
   ```

7. Remove the dev resources: `databricks bundle destroy -t dev --profile <profile>`
8. In CI, remove the prod resources: `databricks bundle destroy -t prod`

| Target | Runs as |
| --- | --- |
| `dev` | The user who deploys |
| `prod` | The service principal |
