# Job with Git source

This Declarative Automation Bundles example runs a notebook directly from a public Git repository.
See the [Git source documentation](https://docs.databricks.com/aws/en/jobs/how-to/use-git-with-jobs) for supported providers and tasks.

| Source | Behavior |
| --- | --- |
| Git source | The job checks out the configured repository and branch at run time. |
| Synced source | The bundle uploads local files to the workspace during deployment. |

## Prerequisites

* Install Databricks CLI v1.20.0 or above.
* Configure the `dabs-examples` authentication profile.
* Use a workspace that supports serverless jobs.

## Usage

1. Validate the development target.

   ```sh
   databricks bundle validate -t dev --profile dabs-examples
   ```

2. Deploy and run the job.

   ```sh
   databricks bundle deploy -t dev --profile dabs-examples
   databricks bundle run -t dev git_source --profile dabs-examples
   ```

3. Override a Git setting when needed.

   ```sh
   databricks bundle deploy -t dev --var git_branch=main --profile dabs-examples
   ```

4. Remove the development deployment.

   ```sh
   databricks bundle destroy -t dev --auto-approve --profile dabs-examples
   ```

5. Deploy production from the `main` branch, then remove it.

   ```sh
   databricks bundle deploy -t prod --profile dabs-examples
   databricks bundle destroy -t prod --auto-approve --profile dabs-examples
   ```
