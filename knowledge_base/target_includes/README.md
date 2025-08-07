# Target Includes Example

This example demonstrates the concept of using `target_includes` (or similar include mechanisms) in Databricks Asset Bundles to organize job configurations across different environments without duplication.

It addresses the use case described in [GitHub Issue #2878](https://github.com/databricks/cli/issues/2878), which requests the ability to include specific resource files based on target configurations.

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

- **dev**: Includes only `resources/set1/*.yml`
   - Contains: set1-job-1, set1-job-2
   - Environment: development

- **staging**: Includes both `resources/set1/*.yml` and `resources/set2/*.yml`
   - Contains: set1-job-1, set1-job-2, set2-job-1, set2-job-2
   - Environment: staging

- **prod**: Includes only `resources/set2/*.yml`
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
      Name: Set1 Job 1 - foo
      URL:  (not deployed)
    set1-job-2:
      Name: Set1 Job 2 - foo
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
      Name: Set1 Job 1 - bar
      URL:  (not deployed)
    set1-job-2:
      Name: Set1 Job 2 - bar
      URL:  (not deployed)
    set2-job-1:
      Name: Set2 Job 1 - bar
      URL:  (not deployed)
    set2-job-2:
      Name: Set2 Job 2 - bar
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
      Name: Set2 Job 1 - baz
      URL:  (not deployed)
    set2-job-2:
      Name: Set2 Job 2 - baz
      URL:  (not deployed)
```

## Notes

There are some important aspects of this implementation:
- The `databricks.yml` file includes all configuration files for all targets (see `include` section). This does not impact which resources will be deployed to each target.
- For each job in a corresponding configuration file, such as `resources/set1/job_1.yml`, targets are defined where the job should be deployed. YAML anchors are used to avoid duplications between targets.
