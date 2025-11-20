# Overview

This package contains common code and DABs to deploy observability ETL and dashboards for Databricks ingestion projects. The goal is to provide an example and a starting point for building ingestion observability across pipelines and datasets.

In particular, the package provides:
 - Tools to ETL observability data from a variety of sources such as SDP event log, Auto Loader `cloud_file_states`, system tables and other.
 - Tag-based pipeline discovery: Specify pipelines to monitor using flexible tag expressions with OR-of-ANDs logic (e.g., `"tier:T0;team:data,tier:T1"`) instead of maintaining lists of pipeline IDs
 - Performance-optimized pipeline discovery: Optional inverted index for efficient tag-based pipeline discovery at scale
 - Build a collection of observability tables on top of the above data using the medallion architecture.
 - Provide out-of-the-box AI/BI Dashboards based on the above observability tables
 - Code and examples to integrate the observability tables with third-party monitoring providers such as Datadog, New Relic, Azure Monitor, Splunk

The package contains deployable [Databricks Asset Bundles (DABs)](https://docs.databricks.com/aws/en/dev-tools/bundles/) for easy distribution:

- Generic SDP pipelines
- CDC Connector

Coming soon

- SDP pipelines with Auto Loader
- SaaS Connectors

# Prerequisites

- [Databricks Asset Bundles (DABs)](https://docs.databricks.com/aws/en/dev-tools/bundles/)
- PrPr for forEachBatch sinks in SDP (if using the 3P observabitlity platforms integration)


# Artifacts

- Generic SDP DAB (in `generic_sdp_monitoring_dab/`). See [generic_sdp_monitoring_dab/README.md](generic_sdp_monitoring_dab/README.md) for more info.
- CDC Connectors Monitoring DAB (in `cdc_connector_monitoring_dab/`) See [cdc_connector_monitoring_dab/README.md](cdc_connector_monitoring_dab/README.md) for more info. 


# Developer information

## Shared top-level directories

- `jobs/` - Shared notebooks to be used in jobs in the individual monitoring DABs.
- `lib/` - Shared python code.
- `resources/` - Shared DAB resources definitions
- `scripts/` - helper scripts
- `README-third-party-monitoring.md` and `third_party_sinks/` - 3P observability integration (Datadog, New Relic Splunk, Azure Monitor) 
- `vars/` - DAB variables for the shared resources customization




