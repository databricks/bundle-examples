# Sync include, exclude, and scripts

This Declarative Automation Bundles example shows `sync.include`, `sync.exclude`, and deploy scripts.
A `predeploy` hook writes a gitignored file. `sync.include` uploads it. `sync.exclude` keeps a local file out of the workspace.
A serverless job reads the generated file after deploy.

For more information, see the [sync settings documentation](https://docs.databricks.com/aws/en/dev-tools/bundles/settings#sync).

## Prerequisites

* Databricks CLI v1.20.0 or above
* A workspace with serverless jobs

## Usage

1. Validate: `databricks bundle validate -t dev --profile <profile>`
2. Deploy: `databricks bundle deploy -t dev --profile <profile>`
3. List files and confirm `generated/payload.txt` is present and `local_only/secret.txt` is absent:

```bash
databricks workspace list \
  /Workspace/bundle-examples/sync_include_exclude_and_scripts/dev/<short-name>/files \
  --profile <profile>
```

4. Run the job: `databricks bundle run -t dev read_generated --profile <profile>`
5. Destroy: `databricks bundle destroy -t dev --auto-approve --profile <profile>`
6. Repeat steps 1–5 with `-t prod` (prod root path has no `<short-name>` segment).

| Path | Local | Uploaded |
| --- | --- | --- |
| `generated/payload.txt` | gitignored; written by `predeploy` | yes (`sync.include`) |
| `local_only/secret.txt` | committed | no (`sync.exclude`) |
