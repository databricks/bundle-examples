# Multi-region Serving

This Databricks Asset Bundle (DAB) is an example tool used to sync resources between main 
workspaces and remote workspaces to simplify the workflow for serving models or features 
across multiple regions.

## How to use this example
1. Download this example

2. Make changes as needed. Some files to highlight:
   * databricks.yml - DAB bundle configuration including variable names and default values.
   * src/manage_endpoint.ipynb - Notebook for create / update serving endpoints.
   * src/manage_share.ipynb - Notebook for syncing dependencies of a shared model.

## How to trigger the workflows

1. Install the Databricks CLI from https://docs.databricks.com/dev-tools/cli/databricks-cli.html

2. Authenticate to your Databricks workspaces, if you have not done so already:
    ```
    $ databricks configure
    ```

3. Validate bundle variables

   If you don't want to set a default value for any variables defined in `databricks.yaml`, you
   need to provide the variables when running any commands. You can validate if all variables are
   provided
   ```
   $ MY_BUNDLE_VARS="share_name=<SHARE_NAME>,model_name=<MODEL_NAME>,model_version=<MODEL_VERSION>,endpoint_name=<ENDPOINT_NAME>,notification_email=<EMAIL_ADDRESS>"
   $ databricks bundle validate --var=$MY_BUNDLE_VARS
   ```

4. To deploy a copy to your main workspace:
    ```
    $ databricks bundle deploy --target main --var=$MY_BUNDLE_VARS
    ```
    (Note that "main" is the target name defined in databricks.yml)

    This deploys everything that's defined for this project.
    For example, the default template would deploy a job called
    `[dev yourname] manage_serving_job` to your workspace.
    You can find that job by opening your workpace and clicking on **Workflows**.

5. Similarly, to deploy a remote workspace, type:
   ```
   $ databricks bundle -p <DATABRICKS_PROFILE> deploy --target remote1 --var=$MY_BUNDLE_VARS
   ```

   Use `-p` to specify the databricks profile used by this command. The profile need to be 
   configured in `~/.databrickscfg`. 

6. To run the workflow to sync a share, use the "run" command:
   ```
   $ databricks bundle -t main -p <DATABRICKS_PROFILE> run manage_share_job --var=$MY_BUNDLE_VARS 
   ```

7. For documentation on the Databricks asset bundles format used
   for this project, and for CI/CD configuration, see
   https://docs.databricks.com/dev-tools/bundles/index.html.
