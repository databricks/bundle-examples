# Private wheel packages

This example demonstrates how to use a private wheel package from a job in a Databricks Asset Bundle.

## Prerequisites

* Databricks CLI v0.235.0 or above
* Python 3.10 or above

# Usage

Databricks does not natively support referring to wheels hosted on a private repository.

We can work around this by downloading the wheel and including it in the Databricks Asset Bundle.

To emulate this for this example, we will download a wheel from PyPI, include it in deployment, and refer to it from job configuration.

## Downloading a wheel

First, download the wheel to the `dist` directory:

```shell
pip download -d dist cowsay==6.1
```

## Deploying the example

Next, update the `host` field under `workspace` in `databricks.yml` to the Databricks workspace you wish to deploy to.

Run `databricks bundle deploy` to upload the wheel and deploy the jobs.

Run `databricks bundle run` to run either job.

Example output:
```
$ databricks bundle run
Run URL: https://...

2024-11-27 13:23:01 "[dev pieter_noordhuis] Example to demonstrate using a private wheel package on serverless" TERMINATED SUCCESS
  _____________
| Hello, world! |
  =============
             \
              \
                ^__^
                (oo)\_______
                (__)\       )\/\
                    ||----w |
                    ||     ||
```
