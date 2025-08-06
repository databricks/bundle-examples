# Target Includes Example

This example demonstrates the concept of using `target_includes` (or similar include mechanisms) in Databricks Asset Bundles to organize job configurations across different environments without duplication.

## Overview

This example implements the use case described in [GitHub Issue #2878](https://github.com/databricks/cli/issues/2878), which requests the ability to include specific resource files based on target configurations.

## Directory Structure

```
target_includes/
├── databricks.yml          # Main bundle configuration with 3 targets
├── resources/
│   ├── set1/              # Jobs for dev and staging environments
│   │   ├── job_1.yml
│   │   └── job_2.yml
│   └── set2/              # Jobs for staging and prod environments
│       ├── job_1.yml
│       └── job_2.yml
└── README.md
```

## Target Configuration

The bundle defines three targets:

1. **dev**: Includes only `resources/set1/*.yml`
   - Contains: set1-job-1, set1-job-2
   - Environment: development

2. **staging**: Includes both `resources/set1/*.yml` and `resources/set2/*.yml`
   - Contains: set1-job-1, set1-job-2, set2-job-1, set2-job-2
   - Environment: staging

3. **prod**: Includes only `resources/set2/*.yml`
   - Contains: set2-job-1, set2-job-2
   - Environment: production

## Usage

```bash
# Summary of the bundle resources for dev
databricks bundle summary -p u2m -t dev

Name: target-includes-example
Target: dev
Workspace:
  User: ***
  Path: ***
Resources:
  Jobs:
    set1-job-1:
      Name: Set1 Job 1 - dev
      URL:  (not deployed)
    set1-job-2:
      Name: Set1 Job 2 - dev
      URL:  (not deployed)

# Summary of the bundle resources for staging
databricks bundle summary -p u2m -t staging

Name: target-includes-example
Target: staging
Workspace:
  User: ***
  Path: ***
Resources:
  Jobs:
    set1-job-1:
      Name: Set1 Job 1 - staging
      URL:  (not deployed)
    set1-job-2:
      Name: Set1 Job 2 - staging
      URL:  (not deployed)
    set2-job-1:
      Name: Set2 Job 1 - staging
      URL:  (not deployed)
    set2-job-2:
      Name: Set2 Job 2 - staging
      URL:  (not deployed)

# Summary of the bundle resources for prod
databricks bundle summary -p u2m -t prod   

Name: target-includes-example
Target: prod
Workspace:
  User: ***
  Path: ***
Resources:
  Jobs:
    set2-job-1:
      Name: Set2 Job 1 - prod
      URL:  (not deployed)
    set2-job-2:
      Name: Set2 Job 2 - prod
      URL:  (not deployed)
```

## Notes

There are some key aspects in this implementation
1. In `databricks.yml` file we include (see `include` section) all configuration files for all targets. This does not impact which resources will be deployed for which target.
2. For each job in corresponding configuration file like `resources/set1/job_1.yml` we define in which targets this job should be deployed. We use YAML anchors to avoid duplications between targets.
