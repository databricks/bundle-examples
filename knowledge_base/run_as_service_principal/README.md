# Run as a service principal

This Declarative Automation Bundles example runs a prod job as a service principal.
The dev job runs as the user who deploys it.

For more information, see the [run_as documentation](https://docs.databricks.com/dev-tools/bundles/run-as.html).

## What this example shows

* The `dev` target uses `mode: development`. The job runs as the user who deploys it.
* The `prod` target uses `mode: production` and `run_as.service_principal_name`. The job runs as the service principal.
* A variable supplies the application ID of the service principal. The bundle contains no IDs, hosts, or secrets.
* The `prod` target gives `CAN_MANAGE` to a deployer group and `CAN_VIEW` to a viewer group.
* No individual user gets `CAN_MANAGE` from the bundle.
* The `prod` target sets an explicit `workspace.root_path`. This keeps one copy of the prod deployment.
* The `whoami` job runs on serverless compute with `environment_version: "4"`.
* The job prints `current_user()` and the SDK identity. The output shows which identity ran the job.

The bundle contains these files:

| File | Content |
| --- | --- |
| `databricks.yml` | Variables, the `dev` target, and the `prod` target with `run_as` and `permissions`. |
| `resources/whoami.job.yml` | The serverless `whoami` job. The job has no schedule. |
| `src/whoami.py` | The task that prints the run identity. |

## Prerequisites

* Databricks CLI. We tested this example with v1.20.0.
* A Databricks workspace with Unity Catalog and serverless jobs.
* Workspace admin access, or a workspace admin who can do the steps in the next section.

The bundle has no cloud-specific settings. It applies to AWS, Azure, and GCP.
This example uses serverless compute only. We did not test classic compute.

## Create the service principal and grant it access

Do these steps one time for each workspace.

1. Create the service principal.
   In the workspace, open **Settings > Identity and access > Service principals**.
   Click **Add service principal**.
   You can also create it in the account console under **User management**.
2. If you created the service principal in the account console, assign it to the workspace.
   Open **Workspaces**, select the workspace, and open **Permissions**.
3. Copy the **Application ID** of the service principal. This value is a UUID.
   Use this value for `service_principal_application_id`.
4. Make sure that the service principal has the **Workspace access** entitlement.
5. Create a workspace group for deployers. The default name in this example is `bundle-deployers`.
6. Add each person who deploys to prod to the deployer group.
7. Add the service principal to the deployer group. CI deploys as the service principal.
8. Give the deployer group the `Service Principal: User` role on the service principal.
   Open the service principal and then open the **Permissions** tab.
   Click **Grant access**, select the deployer group, and select **Service Principal: User**.
   The `Service Principal: Manager` role also includes this permission.
9. Grant the Unity Catalog privileges that your job needs to the service principal.
   Use the application ID as the principal name.
   The `whoami` job reads no tables, so it needs no grants.
   A job that reads a table needs grants such as these:

   ```sql
   GRANT USE CATALOG ON CATALOG <catalog> TO `<application-id>`;
   GRANT USE SCHEMA, SELECT ON SCHEMA <catalog>.<schema> TO `<application-id>`;
   ```

10. If your workspace uses serverless budget policies, give the service principal access to a policy.
11. For CI, create an OAuth secret for the service principal.
    Open the service principal and then open the **Secrets** tab.
    Click **Generate secret**.
    Keep the secret in the secret store of your CI system.
    Do not put the secret in the bundle or in Git.

## Configure

Set the variables with `--var` or with `BUNDLE_VAR_<name>` environment variables.

| Variable | Default | Target | Description |
| --- | --- | --- | --- |
| `service_principal_application_id` | None. This value is mandatory for `prod`. | `prod` | The application ID of the service principal that runs the prod job. |
| `deployer_group` | `bundle-deployers` | `prod` | The group that gets `CAN_MANAGE`. Its members and CI deploy to prod. |
| `viewer_group` | `users` | `prod` | The group that gets `CAN_VIEW` on the prod job and its runs. |

The `dev` target sets `service_principal_application_id` to `not-used-in-dev`.
The `dev` target does not use this value.

The bundle does not set `workspace.host`.
Select the workspace with a profile, for example `-p <profile>`.
Alternatively, set the `DATABRICKS_HOST` environment variable.

## Deploy and run in dev

1. Validate the bundle:

   ```sh
   databricks bundle validate -t dev
   ```

2. Deploy the bundle:

   ```sh
   databricks bundle deploy -t dev
   ```

3. Run the job:

   ```sh
   databricks bundle run -t dev whoami
   ```

Development mode adds the `[dev <your short name>]` prefix to the job name.
The bundle deploys to your home folder.

## Deploy and run in prod

Deploy prod from CI as the service principal.
Use OAuth machine-to-machine (M2M) authentication.
Do not use a personal access token.

1. In the CI secret store, keep the OAuth secret of the service principal.
2. In the CI job, set these environment variables:

   ```sh
   export DATABRICKS_HOST=https://<workspace-host>
   export DATABRICKS_CLIENT_ID=<application-id>
   export DATABRICKS_CLIENT_SECRET=<secret from the CI secret store>
   export BUNDLE_VAR_service_principal_application_id=$DATABRICKS_CLIENT_ID
   ```

3. Validate the bundle. Make sure that the output contains `run_as`:

   ```sh
   databricks bundle validate -t prod -o json
   ```

4. Deploy the bundle:

   ```sh
   databricks bundle deploy -t prod
   ```

5. Run the job:

   ```sh
   databricks bundle run -t prod whoami
   ```

You can also use workload identity federation in CI.
Federation removes the stored OAuth secret.
For more information, see [OAuth token federation](https://docs.databricks.com/dev-tools/auth/oauth-federation.html).

A member of the deployer group can also deploy prod from a laptop:

```sh
databricks bundle deploy -t prod --var service_principal_application_id=<application-id>
```

Do not mix the two methods.
The `root_path` contains the user name of the deploying identity.
A deploy by a different identity makes a second copy of the prod job.

## Verify the identity

The `whoami` job prints three lines.
`bundle run` shows the task output when the run completes.

In dev, the output shows your user name:

```
current_user():        <your user name>
SDK user_name:         <your user name>
SDK display_name:      <your display name>
```

In prod, the output shows the application ID of the service principal:

```
current_user():        <application-id>
SDK user_name:         <application-id>
SDK display_name:      <service principal display name>
```

You can also open the job in the workspace.
The **Run as** field of the job shows the identity.

## Identity model

| Target | Deployment identity | Run identity | Owner (`IS_OWNER`) |
| --- | --- | --- | --- |
| `dev` | You | You | You |
| `prod`, deployed by CI | The service principal | The service principal | The service principal |
| `prod`, deployed by a person | The person in the deployer group | The service principal | The person who deployed |

* The deployment identity is the identity that runs `databricks bundle deploy`.
* The run identity comes from `run_as`. If `run_as` is not set, the run identity is the deployment identity.
* The owner is always the deployment identity. The bundle adds `IS_OWNER` for it.

## Edge cases and common errors

### Missing value for the service principal

If you do not set `service_principal_application_id` for `prod`, the CLI shows this error:

```
Error: no value assigned to required variable service_principal_application_id.
```

Set the variable with `--var` or `BUNDLE_VAR_service_principal_application_id`.
Use the application ID. Do not use the display name.

### Missing Service Principal User role

A person who deploys prod must have the `Service Principal: User` role on the service principal.
If the role is missing, `bundle validate` passes, but `bundle deploy` fails.
The Jobs API rejects the `run_as` setting when the CLI creates or updates the job.
The text of the error comes from the API. We did not record the exact text.
To fix the error, do step 8 in [Create the service principal and grant it access](#create-the-service-principal-and-grant-it-access).

### run_as in development mode

CLI v1.20.0 accepts `run_as` in a `mode: development` target.
The CLI shows no error and no warning.
Do not set `run_as` in dev.
A dev job that runs as the service principal hides your own permission problems.
Also, each developer then needs the `Service Principal: User` role.

### Deploy performed by the service principal

When CI deploys as the service principal, the deployment identity and the run identity are the same.
The service principal needs no `Service Principal: User` role on itself.
The service principal needs the **Workspace access** entitlement.
The `root_path` resolves to `/Workspace/Users/<application-id>/.bundle/run_as_service_principal/prod`.

Run `databricks bundle init` as a person, not as the service principal.
CI runs only `validate`, `deploy`, `run`, and `destroy`.

### Validate recommendations for prod

When a person who is not in the deployer group validates prod, the CLI shows this recommendation:

```
Recommendation: permissions section should explicitly include the current deployment identity '<user>' or one of its groups
If it is not included, CAN_MANAGE permissions are only applied if the present identity is used to deploy.
```

This is a recommendation, not an error.
Add the deploying identity to the deployer group.
For CI, add the service principal to the deployer group.

The CLI can also show this warning:

```
Warning: workspace folder has permissions not configured in bundle
```

The `root_path` is in the home folder of the deploying identity.
That identity has `CAN_MANAGE` on its home folder, and the bundle does not list it.
The warning does not stop the deploy.

### Pipelines and other resources with run_as

Older CLI versions do not support `run_as` for pipelines.
CLI v0.241.0 added this support.
Before v0.241.0, a bundle with a pipeline and a different `run_as` identity fails with this error:

```
Error: pipelines do not support a setting a run_as user that is different from the owner.
```

The rule is: the run identity of the resource must be the same as the owner.
The owner is the deployment identity.

CLI v1.20.0 supports `run_as` for jobs and pipelines.
Some resource types still use the old rule.
For example, `model_serving_endpoints` and `quality_monitors` fail with this error:

```
Error: model_serving_endpoints do not support a setting a run_as user that is different from the owner.
Current identity: <deployer>. Run as identity: <application-id>.
```

To fix the error, do one of these steps:

* Deploy as the service principal. Then the owner and the run identity are the same.
* Move the resource to a bundle that does not set `run_as`.

The `experimental.use_legacy_run_as` option changes the owner of pipelines to the `run_as` identity.
This option is experimental.
It requires a workspace admin to deploy, and a metastore admin for Unity Catalog pipelines.
Do not use this option for new bundles.

## Clean up

1. Remove the dev deployment:

   ```sh
   databricks bundle destroy -t dev
   ```

2. Remove the prod deployment. Use the identity that deployed prod:

   ```sh
   databricks bundle destroy -t prod --var service_principal_application_id=<application-id>
   ```

3. If you made an OAuth secret only for this example, delete the secret.
4. If you made the service principal only for this example, delete the service principal.

`bundle destroy` removes only the resources that this bundle deployed.
It does not remove the service principal, the groups, or the Unity Catalog grants.
