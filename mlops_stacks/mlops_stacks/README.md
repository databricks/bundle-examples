# mlops_stacks
This project comes with example ML code to train, validate and deploy a regression model to predict NYC taxi fares.
If you're a data scientist just getting started with this repo for a brand new ML project, we recommend 
adapting the provided example code to your ML problem. Then making and 
testing ML code changes on Databricks or your local machine.

The "Getting Started" docs can be found at https://learn.microsoft.com/azure/databricks/dev-tools/bundles/mlops-stacks.

## Table of contents
* [Code structure](#code-structure): structure of this project.

* [Iterating on ML code](#iterating-on-ml-code): making and testing ML code changes on Databricks or your local machine.
* [Next steps](#next-steps)

This directory contains an ML project based on the default
[Databricks MLOps Stacks](https://github.com/databricks/mlops-stacks),
defining a production-grade ML pipeline for automated retraining and batch inference of an ML model on tabular data.

## Code structure
This project contains the following components:

| Component                  | Description                                                                                                                                                                                                                                                                                                                                             |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ML Code                    | Example ML project code, with unit tested Python modules and notebooks                                                                                                                                                                                                                                                                                  |
| ML Resources as Code | ML pipeline resources (training and batch inference jobs with schedules, etc) configured and deployed through [databricks CLI bundles](https://learn.microsoft.com/azure/databricks/dev-tools/cli/bundle-cli)                                                                                              |

contained in the following files:

```
mlops_stacks        <- Root directory. Both monorepo and polyrepo are supported.
│
├── mlops_stacks       <- Contains python code, notebooks and ML resources related to one ML project. 
│   │
│   ├── requirements.txt        <- Specifies Python dependencies for ML code (for example: model training, batch inference).
│   │
│   ├── databricks.yml          <- databricks.yml is the root bundle file for the ML project that can be loaded by databricks CLI bundles. It defines the bundle name, workspace URL and resource config component to be included.
│   │
│   ├── training                <- Training folder contains Notebook that trains and registers the model.
│   │
│   ├── validation              <- Optional model validation step before deploying a model.
│   │
│   ├── monitoring              <- Model monitoring, feature monitoring, etc.
│   │
│   ├── deployment              <- Deployment and Batch inference workflows
│   │   │
│   │   ├── batch_inference     <- Batch inference code that will run as part of scheduled workflow.
│   │   │
│   │   ├── model_deployment    <- As part of CD workflow, deploy the registered model by assigning it the appropriate alias.
│   │
│   │
│   ├── tests                   <- Unit tests for the ML project, including the modules under `features`.
│   │
│   ├── resources               <- ML resource (ML jobs, MLflow models) config definitions expressed as code, across dev/staging/prod/test.
│       │
│       ├── model-workflow-resource.yml                <- ML resource config definition for model training, validation, deployment workflow
│       │
│       ├── batch-inference-workflow-resource.yml      <- ML resource config definition for batch inference workflow
│       │
│       ├── ml-artifacts-resource.yml                  <- ML resource config definition for model and experiment
│       │
│       ├── monitoring-resource.yml           <- ML resource config definition for quality monitoring workflow
```


## Iterating on ML code

### Deploy ML code and resources to dev workspace using Bundles

Refer to [Local development and dev workspace](./resources/README.md#local-development-and-dev-workspace)
to use databricks CLI bundles to deploy ML code together with ML resource configs to dev workspace.

This will allow you to develop locally and use databricks CLI bundles to deploy to your dev workspace to test out code and config changes.

### Develop on Databricks using Databricks Git folders

#### Prerequisites
You'll need:
* Access to run commands on a cluster running Databricks Runtime ML version 11.0 or above in your dev Databricks workspace
* To set up [Databricks Git folders](https://learn.microsoft.com/azure/databricks/repos/index): see instructions below

#### Configuring Databricks Git folders
To use Git folders, [set up git integration](https://learn.microsoft.com/azure/databricks/repos/repos-setup) in your dev workspace.

If the current project has already been pushed to a hosted Git repo, follow the
[UI workflow](https://learn.microsoft.com/azure/databricks/repos/git-operations-with-repos#add-a-repo-and-connect-remotely-later)
to clone it into your dev workspace and iterate. 

Otherwise, e.g. if iterating on ML code for a new project, follow the steps below:
* Follow the [UI workflow](https://learn.microsoft.com/azure/databricks/repos/git-operations-with-repos#add-a-repo-and-connect-remotely-later)
  for creating a repo, but uncheck the "Create repo by cloning a Git repository" checkbox.
* Install the `dbx` CLI via `pip install --upgrade dbx`
* Run `databricks configure --profile mlops_stacks-dev --token --host <your-dev-workspace-url>`, passing the URL of your dev workspace.
  This should prompt you to enter an API token
* [Create a personal access token](https://learn.microsoft.com/azure/databricks/dev-tools/auth/pat)
  in your dev workspace and paste it into the prompt from the previous step
* From within the root directory of the current project, use the [dbx sync](https://dbx.readthedocs.io/en/latest/guides/python/devloop/mixed/#using-dbx-sync-repo-for-local-to-repo-synchronization) tool to copy code files from your local machine into the Repo by running
  `dbx sync repo --profile mlops_stacks-dev --source . --dest-repo your-repo-name`, where `your-repo-name` should be the last segment of the full repo name (`/Repos/username/your-repo-name`)



## Next Steps

When you're satisfied with initial ML experimentation (e.g. validated that a model with reasonable performance can be trained on your dataset) and ready to deploy production training/inference pipelines, ask your ops team to set up CI/CD for the current ML project if they haven't already. CI/CD can be set up as part of the

MLOps Stacks initialization even if it was skipped in this case, or this project can be added to a repo setup with CI/CD already, following the directions under "Setting up CI/CD" in the repo root directory README.

To add CI/CD to this repo:
 1. Run `databricks bundle init mlops-stacks` via the Databricks CLI
 2. Select the option to only initialize `CICD_Only`
 3. Provide the root directory of this project and answer the subsequent prompts

More details can be found on the homepage [MLOps Stacks README](https://github.com/databricks/mlops-stacks/blob/main/README.md).
