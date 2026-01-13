# Databricks Asset Bundle Claude Skills

This folder contains specialized Claude skills for working with Databricks Asset Bundles (DABs). These skills provide expert guidance on creating, configuring, validating, and deploying bundles.

## Skills Overview

### Core Bundle Skills
- **create-bundle** - Create new bundles from scratch with proper structure
- **validate-bundle** - Validate configurations and troubleshoot errors
- **optimize-bundle** - Design patterns, architecture guidance, and optimization
- **secure-bundle** - Permissions, grants, secrets, and security

### Resource Configuration Skills
- **configure-job** - Configure jobs with tasks, schedules, and orchestration
- **configure-pipeline** - Set up Delta Live Tables (DLT) pipelines
- **configure-app** - Deploy Databricks Apps (Dash, Streamlit, etc.)
- **configure-dashboard** - Configure AI/BI dashboards and snapshots
- **configure-alert** - Set up SQL alerts and monitoring
- **configure-schema** - Manage Unity Catalog schemas and catalogs
- **configure-volume** - Configure Unity Catalog volumes for file storage
- **configure-cluster** - Configure clusters for jobs and pipelines
- **configure-ml-resources** - Set up ML resources (models, experiments)

### Advanced Configuration Skills
- **use-python-resources** - Python-based resource definitions (pydabs pattern)
- **configure-environments** - Configure dev/staging/prod deployment environments
- **manage-variables** - Variables, interpolation, and resource references
- **manage-dependencies** - Build and manage Python wheels, JARs, and libraries

## How Skills Work

### Three-Tier Approach for Maximum Portability

These skills are designed to work in any repository, not just the bundle-examples repo:

**Tier 1: Local Examples** (if available)
- Skills first try to find local example files using Glob
- If found, they Read and reference them
- Works when skills are in the bundle-examples repo

**Tier 2: GitHub Examples** (fetch remotely)
- If no local files, skills use WebFetch to get examples from:
  - https://github.com/databricks/bundle-examples
- Ensures skills work in any repository
- Always fetches latest examples

**Tier 3: Inline Templates** (always available)
- All skills contain comprehensive inline YAML/Python examples
- Works even without local files or network access
- Self-contained and complete

### Documentation Integration

Every skill automatically fetches the latest Databricks documentation using WebFetch:
- Official docs: https://docs.databricks.com/aws/en/dev-tools/bundles/
- Always up-to-date guidance
- Combines official docs with practical examples

## Usage Examples

### Creating a New Bundle
```
"Help me create a new Python ETL bundle"
→ Triggers create-bundle skill
→ Fetches latest docs
→ Shows relevant examples
→ Generates complete databricks.yml
```

### Configuring a Job
```
"Create a job that runs daily at 2 AM"
→ Triggers configure-job skill
→ Fetches job task documentation
→ Shows job configuration patterns
→ Generates complete job YAML
```

### Troubleshooting
```
"Getting error: variable 'catalog' not defined"
→ Triggers validate-bundle skill
→ Diagnoses the issue
→ Shows fix with correct configuration
```

### Best Practices
```
"How should I structure my production deployment?"
→ Triggers optimize-bundle skill
→ Fetches deployment mode docs
→ Shows production patterns
→ Provides security checklist
```

## Portability Features

These skills are fully portable and can be copied to any repository:

✅ **Work in bundle-examples repo** - Uses local example files
✅ **Work in any other repo** - Fetches examples from GitHub
✅ **Work offline** - Uses comprehensive inline templates
✅ **Always current** - Fetches latest Databricks documentation
✅ **Self-contained** - No external dependencies required

## References

- **EXAMPLES.md** - Complete list of GitHub URLs for all example files
- **Databricks Docs**: https://docs.databricks.com/aws/en/dev-tools/bundles/
- **GitHub Repo**: https://github.com/databricks/bundle-examples

## Skill Development Notes

Each skill follows Claude Agent best practices:
- YAML frontmatter with `name` and `description`
- Clear procedural instructions for Claude
- Comprehensive inline examples
- Progressive disclosure (local → GitHub → inline)
- Related skills cross-references
- Common issues and solutions

## Contributing

When updating skills:
1. Ensure three-tier approach is maintained (local/GitHub/inline)
2. Keep inline examples comprehensive and current
3. Update GitHub URLs if example locations change
4. Test skills work outside bundle-examples repo
5. Update EXAMPLES.md if adding new example references
