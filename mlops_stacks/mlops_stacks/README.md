# mlops_stacks

This directory contains python code, notebooks and ML resource configs related to one ML project.

See the [Project overview](../docs/project-overview.md) for details on code structure of project directory.

## Set up mlops_stacks
- Create a catalog called `dev` in your workspace (this is pre-defined in `databricks.yml`)
- Add your workspace url to the host fields in `databricks.yml`
- For running `databricks run batch_inference_job` first create an input table for inference and add the definiton in `resources/batch-inference-workflow-resource.yml`
- For development and pull requests
    - `pip install -r requirements.txt`
    - Its recommended to create a dev environment with Python 3.10
