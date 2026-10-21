# GitHub Actions CI/CD

## What this example shows

This example validates and deploys a serverless job with GitHub Actions and Databricks workload identity federation.

Copy `.github/workflows/bundle.yml` from this example to your repository root.

## Prerequisites

- Use a Databricks workspace that supports serverless jobs.
- Get permission to create a Databricks service principal and federation policies.
- Get permission to manage GitHub environments and repository variables.
- Install Databricks CLI `0.272.0` or newer for local tests.

The bundle accepts compatible newer CLI versions. The workflow pins `0.272.0` for repeatable CI runs.

## Set up identity

1. Create one Databricks service principal for the pipeline.
2. Create three federation policies for the service principal.
3. Set each issuer to `https://token.actions.githubusercontent.com`.
4. Set the dev subject to `repo:<owner>/<repository>:environment:dev`.
5. Set the staging subject to `repo:<owner>/<repository>:environment:staging`.
6. Set the prod subject to `repo:<owner>/<repository>:environment:prod`.
7. Set each audience to your Databricks account ID.
8. Grant the service principal `CAN_USE` access to the workspace.
9. Grant the required Unity Catalog privileges for resources that you add.
10. Do not create or store a personal access token.

Use numeric owner and repository IDs in subjects when your GitHub organization requires immutable subjects.

## Configure the CI system

Create these GitHub repository or environment variables.

| Variable | Location | Value |
|---|---|---|
| `DATABRICKS_HOST` | Each environment | The workspace URL for that target |
| `DATABRICKS_CLIENT_ID` | Each environment | The Databricks service principal application ID |

1. Create GitHub environments named `dev`, `staging`, and `prod`.
2. Add the variables to each environment.
3. Add required reviewers to the `prod` environment.
4. Do not add required reviewers to `dev` or `staging`.

## Pipeline flow

| Trigger | Stage | Command | Target |
|---|---|---|---|
| Pull request | Validate | `databricks bundle validate -t dev` | `dev` |
| Push to `main` | Staging | `databricks bundle deploy -t staging` | `staging` |
| Approved push to `main` | Production | `databricks bundle deploy -t prod` | `prod` |

## Run it the first time

1. Copy the workflow to your repository root at `.github/workflows/bundle.yml`.
2. Replace `<owner>` and `<repository>` in the federation policies.
3. Open a pull request that changes this example.
4. Confirm that the validate job succeeds.
5. Merge the pull request into `main`.
6. Confirm that the staging deployment succeeds.
7. Approve the pending `prod` environment deployment.
8. Confirm that the production deployment succeeds.

## Edge cases and common errors

- Fork pull requests do not receive an OIDC token. Run validation from a trusted branch.
- The concurrency groups prevent two deployments to the same target.
- A wrong subject claim causes an identity federation match error. Check the exact environment name.
- A CLI older than `0.272.0` causes bundle version errors. Update the local CLI or the workflow pin.
- An interrupted deployment can leave a deployment lock. Retry after the active deployment ends.
- Serverless availability, storage URIs, identities, and regions differ by cloud. This example does not validate classic compute.
- Bundle deployment is idempotent. Retry the same target after a safe interruption.

## Clean up

1. Run `databricks bundle destroy -t dev` if you deployed the dev target.
2. Run `databricks bundle destroy -t staging`.
3. Run `databricks bundle destroy -t prod`.
4. Delete only the three federation policies for this example.
5. Delete the service principal if no other system uses it.
