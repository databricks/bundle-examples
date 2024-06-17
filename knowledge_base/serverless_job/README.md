# Serverless job

This example demonstrates how to define and use a serverless job in a Databricks Asset Bundle.

## Prerequisites

* Databricks CLI v0.218.0 or above

## Usage

Configure the Databricks CLI profile to use:

```bash
export DATABRICKS_CONFIG_PROFILE=<my profile>
```

Run `databricks bundle deploy` to deploy the job.

Run `databricks bundle run serverless_job` to run the job.

Example output:

```
$ databricks bundle run serverless_job
Run URL: https://...

2024-06-17 09:58:06 "[dev pieter_noordhuis] Example serverless job" TERMINATED SUCCESS
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
