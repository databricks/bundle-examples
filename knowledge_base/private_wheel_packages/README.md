# Private wheel packages

This example demonstrates how to use a private wheel package from a job in a Databricks Asset Bundle.

## Prerequisites

* Databricks CLI v0.235.0 or above
* Python 3.10 or above

# Usage

Typically, private wheels are hosted in a private repository and are not built inline.
To emulate this, we will build a local copy of an example wheel that does not exist on PyPI and copy it to the `dist` directory.

## Building the example wheel

First, build a local copy of `example_private_wheel` and copy the resulting wheel file to the local `dist` directory.

```shell
cd example_private_wheel
python3 -m build
cd ..
cp example_private_wheel/dist/example_private_wheel-0.1.0-py3-none-any.whl dist/
```

## Deploying the example

Next, update the `host` field under `workspace` in `databricks.yml` to the Databricks workspace you wish to deploy to.

Run `databricks bundle deploy` to upload the wheel and deploy the jobs.

Run `databricks bundle run` to run either job.

Example output:
```
$ databricks bundle run
Run URL: https://...

2024-11-22 16:18:50 "[dev pieter_noordhuis] Example to demonstrate using a private wheel package on serverless" TERMINATED SUCCESS
Hello from example-private-wheel!
```
