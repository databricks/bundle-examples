# Scalable Databricks Asset Bundles (DABs) mono-repo.

This project aims to give users an idea of how you can structure your DABs git repositories in a scalable & effective manner, as well as some general best practices & CI/CD examples.

**This repo is only intended to be used for demonstrative purposes. Myself & Databricks are not liable for any short-comings in this project.**

## Prerequisites

1\. Python versions & environments are managed via. `pyenv`. You can [install pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation) using a package manager such as [homebrew](https://docs.brew.sh/):

```
brew update
brew install pyenv
```

## Getting started

1\. Install the Databricks CLI from https://docs.databricks.com/dev-tools/cli/databricks-cli.html

2a. Authenticate to your Sandbox / Development workspace, if you have not done so already:
   ```
   $ databricks configure
   ```

2b. Setup your default Databricks profile in `.databrickscfg` so that any validation & deployment requests are made against that workspace:
   ```
   host = <your_workspace_uri>
   serverless_compute_id = auto
   token = <your_personal_access_token>
   ```

**Note:** it is advised that you use serverless compute where possible to run your tests, this provides the shortest feedback loop for development. If you want to use an interactive cluster instead, remove the `serverless_compute_id = auto` flag & replace it with the `cluster_id = <your_cluster_id>` flag.

3\. Setup your local environment for development purposes by running:
   ```
   make setup
   ```
This creates a local python virtual environment & installs all project dependencies, it also installs `pre-commit` hooks, these are entirely optional.

4\. Verify that your environment is correctly configured by running:

   ```
   make test
   ```

This will run all package tests defined in `./tests/` remotely in your Databricks workspace on serverless or interactive compute, depending on which you have specified. Alternatively, you _could_ run this locally by containerising spark & integrating it to run your tests.

5\. To deploy a development copy of this project, type:
   ```
   $ databricks bundle deploy --target dev
   ```
(Note that "dev" is the default target, so the `-t` parameter is optional here.)

This deploys everything that's defined for this project.
For example, the default template would deploy a job called
`[dev yourname] my_workflow_dev` to your workspace.
You can find that job by opening your workpace and clicking on **Workflows**.

6\. Verify that the job has been deployed by running:
   ```
   $ databricks bundle run my_serverless_workflow -t dev
   ```

You should see something like the following from your IDE:

```
Run URL: https://company.databricks.com/<job_id>/<run_id>

2024-01-01 00:00:00 "[dev <my_user>] my_serverless_workflow_dev" RUNNING
.
.
.
```

You can verify that the job is running by visiting the UI. Once the job has started, you should see the cluster logs in your IDE again:

```
cowsay is installed & has version: 6.1
boto3 is installed & has version: 1.0.0
get_taxis_data is installed & has version: 0.1.0
utils is installed & has version: 0.1.0
+--------------------+---------------------+-------------+-----------+----------+-----------+--------------------+
|tpep_pickup_datetime|tpep_dropoff_datetime|trip_distance|fare_amount|pickup_zip|dropoff_zip|processing_timestamp|
+--------------------+---------------------+-------------+-----------+----------+-----------+--------------------+
| 2016-02-14 16:52:13|  2016-02-14 17:16:04|         4.94|       19.0|     10282|      10171|2024-10-25 15:00:...|
| 2016-02-04 18:44:19|  2016-02-04 18:46:00|         0.28|        3.5|     10110|      10110|2024-10-25 15:00:...|
| 2016-02-17 17:13:57|  2016-02-17 17:17:55|          0.7|        5.0|     10103|      10023|2024-10-25 15:00:...|
| 2016-02-18 10:36:07|  2016-02-18 10:41:45|          0.8|        6.0|     10022|      10017|2024-10-25 15:00:...|
| 2016-02-22 14:14:41|  2016-02-22 14:31:52|         4.51|       17.0|     10110|      10282|2024-10-25 15:00:...|
+--------------------+---------------------+-------------+-----------+----------+-----------+--------------------+
only showing top 5 rows
```

## Intended Usage.

The intended workflow for this project / demo looks something like the following:

1\. Contributors branch off of the remote staging branch for their new features.

2\. As contributors make their development changes locally on this new branch, they can run their tests either locally or in their remote sandbox / development Databricks workspace using a compute resource of their choice & on a DBR of their choice.

3\. Contributors can also deploy their changes to this sandbox / development workspace for integrated testing & to run jobs or workflows if they want to.

4\. Once the contributor is happy with their changes, they can commit their changes up to the remote feature branch & open a PR.

5\. Upon merge into the `staging` branch, the github workflow defined at `.github/workflows` will run the same tests, validation & deployment in a controlled environment & using a service principle. This will deploy all changes to the staging workspace.

6\. Once the deployment has succeeded & further testing in staging has been done, the same process is carried out to deploy into production (this still needs to be done).
