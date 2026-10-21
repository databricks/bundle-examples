# Azure DevOps CI/CD

## What this example shows

This example validates and deploys a serverless job with Azure DevOps OIDC and Databricks workload identity federation.

## Prerequisites

- Use a Databricks workspace that supports serverless jobs.
- Get permission to create a Databricks service principal and federation policy.
- Get permission to manage Azure DevOps pipelines and environments.
- Install Databricks CLI `0.272.0` for local tests.

## Set up identity

1. Create one Databricks service principal for the pipeline.
2. Create a federation policy for the service principal.
3. Set the issuer to `https://vstoken.dev.azure.com/<organization-id>`.
4. Set the subject to `p://<organization-name>/<project-name>/<pipeline-name>`.
5. Set the audience to your Databricks account ID.
6. Grant the service principal `CAN_USE` access to the workspace.
7. Grant the required Unity Catalog privileges for resources that you add.
8. Do not create or store a personal access token.

Use the Azure DevOps organization GUID in the issuer. Use names, not IDs, in the subject.

## Configure the CI system

Create these Azure DevOps variables.

| Variable | Location | Value |
|---|---|---|
| `DATABRICKS_HOST` | Pipeline or variable group | The workspace URL |
| `DATABRICKS_CLIENT_ID` | Pipeline or variable group | The Databricks service principal application ID |
| `System.AccessToken` | Built in | The Azure DevOps OIDC token source |

1. Create Azure DevOps environments named `staging` and `prod`.
2. Add an approval check to the `prod` environment.
3. Restrict each environment to this pipeline.
4. Set the pipeline variables without secret values or personal access tokens.

## Pipeline flow

| Trigger | Stage | Command | Target |
|---|---|---|---|
| Pull request | Validate | `databricks bundle validate -t dev` | `dev` |
| Push to `main` | Staging | `databricks bundle deploy -t staging` | `staging` |
| Approved push to `main` | Production | `databricks bundle deploy -t prod` | `prod` |

## Run it the first time

1. Replace the identity placeholders in the federation policy.
2. Create a pipeline from `azure-pipelines.yml`.
3. Open a pull request that changes this example.
4. Confirm that the validate stage succeeds.
5. Merge the pull request into `main`.
6. Confirm that the staging deployment succeeds.
7. Approve the pending `prod` environment deployment.
8. Confirm that the production deployment succeeds.

## Edge cases and common errors

- Fork pull requests do not receive an OIDC token. Run validation from a trusted branch.
- Azure DevOps environment exclusive locks prevent concurrent deployments. Configure the lock behavior for each environment.
- A wrong subject claim causes an identity federation match error. Check all three names and their letter case.
- CLI version drift causes bundle version errors. Keep the pipeline and bundle versions equal.
- An interrupted deployment can leave a deployment lock. Retry after the active deployment ends.
- Serverless availability, storage URIs, identities, and regions differ by cloud. This example does not validate classic compute.
- Bundle deployment is idempotent. Retry the same target after a safe interruption.

## Clean up

1. Run `databricks bundle destroy -t dev` if you deployed the dev target.
2. Run `databricks bundle destroy -t staging`.
3. Run `databricks bundle destroy -t prod`.
4. Delete only the federation policy for this example.
5. Delete the service principal if no other system uses it.
