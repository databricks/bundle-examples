# Azure DevOps CI/CD

This Declarative Automation Bundles example validates and deploys a serverless job with Azure DevOps OIDC.
See [Azure DevOps authentication](https://docs.databricks.com/aws/en/dev-tools/auth/provider-azure-devops).

## Prerequisites

- A Databricks workspace that supports serverless jobs.
- Permission to manage Databricks service principals and Azure DevOps environments.
- Databricks CLI v1.20.0 or above.

## Usage

1. Create a Databricks service principal for the pipeline.
2. Grant it workspace access and the required Unity Catalog privileges.
3. Create a federation policy for the service principal.
4. Set the issuer to `https://vstoken.dev.azure.com/<organization-id>`.
5. Set the subject to `p://<organization-name>/<project-name>/<pipeline-name>`.
6. Set the audience to [`api://AzureADTokenExchange`](https://docs.databricks.com/aws/en/dev-tools/auth/provider-azure-devops).
7. Set pipeline variables `DATABRICKS_HOST` and `DATABRICKS_CLIENT_ID`.
8. Create `staging` and `prod` Azure DevOps environments.
9. Add an approval check to the `prod` environment.
10. Copy `azure-pipelines.yml` to your repository root.
11. Open a pull request to run validation.

| Trigger | Command and target |
|---|---|
| Pull request | `databricks bundle validate -t dev` |
| Push to `main` | `databricks bundle deploy -t staging` |
| Production approval | `databricks bundle deploy -t prod` |

## Notes

- Do not use personal access tokens. PR validation needs workspace authentication. Fork pull requests receive no OIDC token.
- Environment locks serialize deployments. The `prod` approval check gates production.
- The setup-cli SHA fixes CLI `1.20.0`. The bundle accepts CLI `>= 1.20.0`.
- After copying the pipeline, set `bundleDirectory` to your bundle path.
- Deploy `staging` and `prod` only from CI as the service principal.
