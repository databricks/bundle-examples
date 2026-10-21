# GitHub Actions CI/CD

This Declarative Automation Bundles example validates and deploys a serverless job with GitHub Actions and OIDC.
See [GitHub Actions authentication](https://docs.databricks.com/aws/en/dev-tools/auth/provider-github).

## Prerequisites

- A Databricks workspace that supports serverless jobs.
- Permission to manage Databricks service principals and GitHub environments.
- Databricks CLI v1.20.0 or above.

## Usage

1. Create a Databricks service principal for the pipeline.
2. Grant it workspace access and the required Unity Catalog privileges.
3. Create federation policies with issuer `https://token.actions.githubusercontent.com`.
4. Use subject `repo:<owner>/<repository>:environment:dev` for dev.
5. Use subject `repo:<owner>/<repository>:environment:staging` for staging.
6. Use subject `repo:<owner>/<repository>:environment:prod` for prod.
7. Set the audience to your Databricks account ID.
8. Create `dev`, `staging`, and `prod` GitHub environments.
9. Set `DATABRICKS_HOST` and `DATABRICKS_CLIENT_ID` in each environment.
10. Add required reviewers to the `prod` environment.
11. Copy `.github/workflows/bundle.yml` to your repository root.
12. Open a pull request to run validation.

| Trigger | Command and target |
|---|---|
| Pull request | `databricks bundle validate -t dev` |
| Push to `main` | `databricks bundle deploy -t staging` |
| Production approval | `databricks bundle deploy -t prod` |

## Notes

- Do not create or store personal access tokens.
- PR validation needs workspace authentication. Fork pull requests receive no OIDC token.
- Concurrency groups serialize each target. Required reviewers gate production.
- `databricks/setup-cli` pins CLI `1.20.0`. The bundle accepts CLI `>= 1.20.0`.
- After copying the workflow, set `working-directory` to your bundle path.
