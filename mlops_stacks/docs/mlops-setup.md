# MLOps Setup Guide
[(back to main README)](../README.md)

## Table of contents
* [Intro](#intro)
* [Create a hosted Git repo](#create-a-hosted-git-repo)
* [Configure CI/CD](#configure-cicd---github-actions)
* [Merge PR with initial ML code](#merge-a-pr-with-your-initial-ml-code)
* [Create release branch](#create-release-branch)

* [Deploy ML resources and enable production jobs](#deploy-ml-resources-and-enable-production-jobs)
* [Next steps](#next-steps)

## Intro
This page explains how to productionize the current project, setting up CI/CD and
ML resource deployment, and deploying ML training and inference jobs.

After following this guide, data scientists can follow the [ML Pull Request](ml-pull-request.md) guide to make changes to ML code or deployed jobs.

## Create a hosted Git repo
Create a hosted Git repo to store project code, if you haven't already done so. From within the project
directory, initialize Git and add your hosted Git repo as a remote:
```
git init --initial-branch=main
```

```
git remote add upstream <hosted-git-repo-url>
```

Commit the current `README.md` file and other docs to the `main` branch of the repo, to enable forking the repo:
```

git add README.md docs .gitignore mlops_stacks/resources/README.md
git commit -m "Adding project README"

git push upstream main
```

## Configure CI/CD - GitHub Actions

### Prerequisites
* You must be an account admin to add service principals to the account.
* You must be a Databricks workspace admin in the staging and prod workspaces. 
  Verify that you're an admin by viewing the
  [staging workspace admin console](https://adb-xxxx.xx.azuredatabricks.net#setting/accounts) and
  [prod workspace admin console](https://adb-xxxx.xx.azuredatabricks.net#setting/accounts). 
  If the admin console UI loads instead of the Databricks workspace homepage, you are an admin.

### Set up authentication for CI/CD
#### Set up Service Principal

To authenticate and manage ML resources created by CI/CD, 
[service principals](https://learn.microsoft.com/azure/databricks/administration-guide/users-groups/service-principals)
for the project should be created and added to both staging and prod workspaces. Follow
[Add a service principal to your Azure Databricks account](https://learn.microsoft.com/azure/databricks/administration-guide/users-groups/service-principals#--add-a-service-principal-to-your-azure-databricks-account)
and [Add a service principal to a workspace](https://learn.microsoft.com/azure/databricks/administration-guide/users-groups/service-principals#--add-a-service-principal-to-a-workspace)
for details.

For your convenience, we also have Terraform modules that can be used to [create](https://registry.terraform.io/modules/databricks/mlops-azure-project-with-sp-creation/databricks/latest) or [link](https://registry.terraform.io/modules/databricks/mlops-azure-project-with-sp-linking/databricks/latest) service principals.



#### Configure Service Principal (SP) permissions 
If the created project uses **Unity Catalog**, we expect a catalog to exist with the name of the deployment target by default. 
For example, if the deployment target is dev, we expect a catalog named dev to exist in the workspace. 
If you want to use different catalog names, please update the target names declared in the[mlops_stacks/databricks.yml](../mlops_stacks/databricks.yml) file.
If changing the staging, prod, or test deployment targets, you'll also need to update the workflows located in the .github/workflows directory.

The SP must have proper permission in each respective environment and the catalog for the environments.

For the integration test and the ML training job, the SP must have permissions to read the input Delta table and create experiment and models. 
i.e. for each environment:
- USE_CATALOG
- USE_SCHEMA
- MODIFY
- CREATE_MODEL
- CREATE_TABLE

For the batch inference job, the SP must have permissions to read input Delta table and modify the output Delta table. 
i.e. for each environment
- USAGE permissions for the catalog and schema of the input and output table.
- SELECT permission for the input table.
- MODIFY permission for the output table if it pre-dates your job.


#### Set secrets for CI/CD

After creating the service principals and adding them to the respective staging and prod workspaces, refer to
[Manage access tokens for a service principal](https://learn.microsoft.com/azure/databricks/administration-guide/users-groups/service-principals#--manage-access-tokens-for-a-service-principal)
and [Get Azure AD tokens for service principals](https://learn.microsoft.com/azure/databricks/dev-tools/api/latest/aad/service-prin-aad-token)
to get your service principal credentials (tenant id, application id, and client secret) for both the staging and prod service principals, and [Encrypted secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
to add the following secrets to GitHub:
- `PROD_AZURE_SP_TENANT_ID`
- `PROD_AZURE_SP_APPLICATION_ID`
- `PROD_AZURE_SP_CLIENT_SECRET`
- `STAGING_AZURE_SP_TENANT_ID`
- `STAGING_AZURE_SP_APPLICATION_ID`
- `STAGING_AZURE_SP_CLIENT_SECRET`
- `WORKFLOW_TOKEN` : [Github token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic) with workflow permissions. This secret is needed for the Deploy CI/CD Workflow.
Be sure to update the [Workflow Permissions](https://docs.github.com/en/actions/security-guides/automatic-token-authentication#modifying-the-permissions-for-the-github_token) section under Repo Settings > Actions > General to allow `Read and write permissions`.


### Setting up CI/CD workflows
After setting up authentication for CI/CD, you can now set up CI/CD workflows. We provide a [Deploy CICD workflow](../.github/workflows/deploy-cicd.yml) that can be used to generate the other CICD workflows mentioned below for projects. 
This workflow is manually triggered with `project_name` as parameter. This workflow will need to be triggered for each project to set up its set of CI/CD workflows that can be used to deploy ML resources and run ML jobs in the staging and prod workspaces. 
These workflows will be defined under `.github/workflows`.

If you want to deploy CI/CD for an initialized project (`Project-Only` MLOps Stacks initialization), you can manually run the `deploy-cicd.yml` workflow from the [Github Actions UI](https://docs.github.com/en/actions/using-workflows/manually-running-a-workflow?tool=webui) once the project code has been added to your main repo. 
The workflow will create a pull request with all the changes against your main branch. Review and approve it to commit the files to deploy CI/CD for the project. 


## Merge a PR with your initial ML code
Create and push a PR branch adding the ML code to the repository.

```
git checkout -b add-ml-code
git add .
git commit -m "Add ML Code"
git push upstream add-ml-code
```

Open a PR from the newly pushed branch. CI will run to ensure that tests pass
on your initial ML code. Fix tests if needed, then get your PR reviewed and merged.
After the pull request merges, pull the changes back into your local `main`
branch:

```
git checkout main
git pull upstream main
```

## Create release branch
Create and push a release branch called `release` off of the `main` branch of the repository:
```
git checkout -b release main
git push upstream release
git checkout main
```

Your production jobs (model training, batch inference) will pull ML code against this branch, while your staging jobs will pull ML code against the `main` branch. Note that the `main` branch will be the source of truth for ML resource configs and CI/CD workflows.

For future ML code changes, iterate against the `main` branch and regularly deploy your ML code from staging to production by merging code changes from the `main` branch into the `release` branch.

## Deploy ML resources and enable production jobs
Follow the instructions in [mlops_stacks/resources/README.md](../mlops_stacks/resources/README.md) to deploy ML resources
and production jobs.

## Next steps
After you configure CI/CD and deploy training & inference pipelines, notify data scientists working
on the current project. They should now be able to follow the
[ML pull request guide](ml-pull-request.md) and 
[ML resource config guide](../mlops_stacks/resources/README.md)  to propose, test, and deploy
ML code and pipeline changes to production.
