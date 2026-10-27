# Wheel with dynamic version and uv

This Declarative Automation Bundles example builds a Python wheel with `uv build` and runs it in a serverless job.
The `presets.artifacts_dynamic_version` setting adds a build timestamp to the wheel version on each deploy.
Each deploy installs the new wheel.
The base version in `pyproject.toml` stays `0.1.0`.

For more information, see the [artifacts documentation](https://docs.databricks.com/aws/en/dev-tools/bundles/settings#artifacts).

## Prerequisites

* Databricks CLI v1.20.0 or above
* uv 0.10 or above (see [Installing uv](https://docs.astral.sh/uv/getting-started/installation/))
* A workspace with serverless compute for jobs

## Usage

1. Deploy the bundle. The CLI builds the wheel with `uv build --wheel`:
   ```bash
   databricks bundle deploy
   ```
2. Run the job:
   ```bash
   databricks bundle run dynamic_version_job
   ```
   The output shows the patched version and the marker:
   ```
   dynamic_version_demo 0.1.0+<timestamp>: marker-v1
   ```
3. Change `MARKER` in `src/dynamic_version_demo/main.py` to `marker-v2`. Keep `version = "0.1.0"` in `pyproject.toml`.
4. Deploy and run the job again:
   ```bash
   databricks bundle deploy
   databricks bundle run dynamic_version_job
   ```
   The output shows a new version suffix and the new marker:
   ```
   dynamic_version_demo 0.1.0+<timestamp>: marker-v2
   ```
5. Remove the deployed resources:
   ```bash
   databricks bundle destroy
   ```
