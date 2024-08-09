# SBT example

This example demonstrates how to build a Scala JAR with [sbt](https://www.scala-sbt.org/) and use it from a job.

## Prerequisites

* Databricks CLI v0.226.0 or above
* [sbt](https://www.scala-sbt.org/) v1.10.1 or above

## Usage

Update the `host` field under `workspace` in `databricks.yml` to the Databricks workspace you wish to deploy to.

Update the `artifact_path` field under `workspace` in `databricks.yml` to the Unity Catalog Volume path where the JAR artifact needs to be deployed.

Run `databricks bundle deploy` to deploy the job.

Run `databricks bundle run spark_jar_job` to run the job.

Example output:

```
% databricks bundle run example_job
Run URL: https://...

2024-08-09 15:49:17 "Example running a Scala JAR built with sbt" TERMINATED SUCCESS
+-----+
| word|
+-----+
|Hello|
|World|
+-----+
```
