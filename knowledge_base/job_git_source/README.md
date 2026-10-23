# Job with Git source

This Declarative Automation Bundles example runs a notebook directly from a public Git repository.
See the [Git source documentation](https://docs.databricks.com/aws/en/jobs/how-to/use-git-with-jobs) for supported providers and tasks.

| Source | Behavior |
| --- | --- |
| Git source | The job checks out the configured repository and branch at run time. |
| Synced source | The bundle uploads local files to the workspace during deployment. |

## Prerequisites

* Install Databricks CLI v1.20.0 or above.
* Configure Databricks CLI authentication.
* Use a workspace that supports serverless jobs.

## Usage

1. Validate the development target.

   ```sh
   databricks bundle validate -t dev
   ```

2. Deploy and run the job.

   ```sh
   databricks bundle deploy -t dev
   databricks bundle run -t dev git_source
   ```

3. Override a Git setting when needed.

   ```sh
   databricks bundle deploy -t dev --var git_branch=main
   ```

4. Remove the development deployment.

   ```sh
   databricks bundle destroy -t dev --auto-approve
   ```

5. Deploy production from the `main` branch.

   ```sh
   databricks bundle deploy -t prod
   ```

6. Remove the production deployment.

   ```sh
   databricks bundle destroy -t prod --auto-approve
   ```
