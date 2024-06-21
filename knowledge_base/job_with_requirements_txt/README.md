# Job that uses `requirements.txt`

This example demonstrates how to make a job pick up a `requirements.txt` dependency file.

## Prerequisites

* Databricks CLI v0.222.0 (unreleased) or above

## Usage

Update the `host` field under `workspace` in `databricks.yml` to the Databricks workspace you wish to deploy to.

Run `databricks bundle deploy` to deploy the job.

Run `databricks bundle run job_with_requirements_txt` to run the job.

Example output:

```
$ databricks bundle run job_with_requirements_txt
Run URL: https://...

2024-06-21 13:38:12 "[dev pieter_noordhuis] Example job that uses a requirements.txt file" TERMINATED SUCCESS
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
