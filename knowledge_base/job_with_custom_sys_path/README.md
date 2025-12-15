# Job with custom `sys.path`

This example demonstrates how to:
1. Define a job that takes parameters with values that derive from the bundle.
2. Use the path parameter to augment Python's `sys.path` to import a module from the bundle.
3. Access job parameters from the imported module.

## Prerequisites

* Databricks CLI v0.230.0 or above

## Usage

This example includes a unit test for the function defined under `my_custom_library` that you can execute on your machine.

```bash
# Setup a virtual environment
uv venv
source .venv/bin/activate
uv pip install -r ./requirements.txt

# Run the unit test
python -m pytest
```

To deploy the bundle to Databricks, follow these steps:

* Update the `host` field under `workspace` in `databricks.yml` to the Databricks workspace you wish to deploy to.
* Run `databricks bundle deploy` to deploy the job.
* Run `databricks bundle run print_bundle_configuration` to run the job.

Example output:

```
% databricks bundle run print_bundle_configuration
Run URL: https://...

2024-10-15 11:48:43 "[dev pieter_noordhuis] Example to demonstrate job parameterization" TERMINATED SUCCESS
```

Navigate to the run URL to observe the output of the loaded configuration file.

You can execute the same steps for the `prod` target.
