# pydabs_job_file_arrival

This example demonstrates a Lakeflow Job that uses file arrival triggers to automatically process new files when they arrive in a Unity Catalog Volume.

The Lakeflow Job is configured with:
- **File arrival trigger**: Monitors a Unity Catalog Volume (root or subpath) for new files, recursively.
- **Configurable wait times**: 
  - Minimum time between triggers: 60 seconds
  - Wait after last file change: 90 seconds (ensures file write is complete)
- **Automatic processing**: When files are detected, the job automatically runs and processes them

* `src/`: Notebook source code for this project.
  * `src/process_files.ipynb`: Processes newly arrived files from the volume path.
* `resources/`:  Resource configurations (jobs, pipelines, etc.)
  * `resources/file_arrival.py`: PyDABs job with file arrival trigger configuration.


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
    `[dev yourname] pydabs_job_file_arrival` to your workspace.
    You can find that resource by opening your workspace and clicking on **Jobs & Pipelines**.

3. To configure the volume location:
   - Edit `resources/file_arrival.py` and update the `url` parameter to point to your Unity Catalog Volume:

     ```python
     url="/Volumes/your_catalog/your_schema/your_volume/"
     ```

4. Development vs. Production behavior
   - Dev target (mode: development): Schedules and automatic triggers are disabled by design, so the job will not auto-fire on file arrival. Use manual runs to test the logic. 
     You can also manually run it with:

     ```
     $ databricks bundle run pydabs_job_file_arrival
     ```
   - Prod target (mode: production): Automatic triggers are active. Uploading a file to the configured Unity Catalog Volume path will trigger the job run when the trigger evaluates.
   