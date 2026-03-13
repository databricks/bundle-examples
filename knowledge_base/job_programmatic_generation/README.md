# job_programmatic_generation

This example demonstrates a simple Databricks job with programmatic generation and customization.

* `src/`: Source code for this project, i.e. SQL files that are turned into jobs programmatically.
* `resources/`: Resource configurations loaded programmatically; see below.

## Programmatic resources and mutators

### `resources/__init__.py`

This module implements _programmatic resource loading_ for the bundle. The `load_resources` function is referenced in `databricks.yml` and is invoked by the Databricks CLI during `databricks bundle deploy`. 

It scans all `src/*.sql` files and creates one job per SQL file, each having a single SQL task.

### `mutators.py`

This module customizes jobs after they are loaded. The `@job_mutator` decorator registers a function that receives every `Job` in the bundle and can return a modified copy.

For any target other than `dev`, the mutator adds email notifications on job failure.

## Documentation

For more information about programmatic resource generation and mutators, see:
- [Bundle Configuration in Python](https://docs.databricks.com/aws/en/dev-tools/bundles/python/)
- [Mutator functions in databricks.yml](https://docs.databricks.com/aws/en/dev-tools/bundles/python/#modify-resources-defined-in-yaml-or-python)

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
    For example, the default template would deploy a job called
    `[dev yourname] airflow_job` to your workspace.
    You can find that resource by opening your workspace and clicking on **Jobs & Pipelines**.

3. Similarly, to deploy a production copy, type:
   ```
   $ databricks bundle deploy --target prod
   ```
   Note that the default job from the template has a schedule that runs every day
   (defined in resources/sample_job.job.yml). The schedule
   is paused when deploying in development mode (see
   https://docs.databricks.com/dev-tools/bundles/deployment-modes.html).

4. To run a job or pipeline, use the "run" command:
   ```
   $ databricks bundle run
   ```

5. Finally, to run tests locally, use `pytest`:
   ```
   $ uv run pytest
   ```

