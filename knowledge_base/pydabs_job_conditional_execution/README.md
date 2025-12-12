# pydabs_job_conditional_execution

This example demonstrates a Lakeflow Job that uses conditional task execution based on data quality checks.

The Lakeflow Job consists of following tasks:
1. Checks data quality and calculates bad records
2. Evaluates if bad records exceed a threshold (100 records)
3. Routes to different processing paths based on the condition:
   - If bad records > 100: runs `handle_bad_data` task
   - If bad records ≤ 100: runs `continue_pipeline` task

* `src/`: Notebook source code for this project.
  * `src/check_quality.ipynb`: Checks data quality and outputs bad record count
  * `src/process_bad_data.ipynb`: Handles cases with high bad record count
  * `src/process_good_data.ipynb`: Continues normal pipeline for good data
* `resources/`:  Resource configurations (jobs, pipelines, etc.)
  * `resources/conditional_execution.py`: PyDABs job definition with conditional tasks


## Getting started

Choose how you want to work on this project:

(a) Directly in your Databricks workspace, see
    https://docs.databricks.com/dev-tools/bundles/workspace.

(b) Locally with an IDE like Cursor or VS Code, see
    https://docs.databricks.com/vscode-ext.

(c) With command line tools, see https://docs.databricks.com/dev-tools/cli/databricks-cli.html

If you're developing with an IDE, dependencies for this project should be installed using uv:

*  Make sure you have the UV package manager installed.
   It's an alternative to tools like pip: https://docs.astral.sh/uv/getting-started/installation/.
*  Run `uv sync --dev` to install the project's dependencies.


# Using this project using the CLI

The Databricks workspace and IDE extensions provide a graphical interface for working
with this project. It's also possible to interact with it directly using the CLI:

1. Authenticate to your Databricks workspace, if you have not done so already:
    ```
    $ databricks configure
    ```

2. To deploy a development copy of this project, type:
    ```
    $ databricks bundle deploy --target dev
    ```
    (Note that "dev" is the default target, so the `--target` parameter
    is optional here.)

    This deploys everything that's defined for this project.
    For example, this project will deploy a job called
    `[dev yourname] pydabs_job_conditional_execution` to your workspace.
    You can find that resource by opening your workspace and clicking on **Jobs & Pipelines**.

3. To run the job, use the "run" command:
   ```
   $ databricks bundle run pydabs_job_conditional_execution
   ```