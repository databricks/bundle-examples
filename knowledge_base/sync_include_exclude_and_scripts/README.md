# Sync include, exclude, and scripts

This Declarative Automation Bundles example shows `sync.include`, `sync.exclude`, and a `predeploy` hook that writes a gitignored file for upload while excluding a local file. A serverless job reads the generated file after deploy.

For more information, see the [sync settings documentation](https://docs.databricks.com/aws/en/dev-tools/bundles/settings#sync).

## Prerequisites

* Databricks CLI v1.20.0 or above
* A workspace with serverless jobs

## Usage

1. Validate: `databricks bundle validate -t dev --profile <profile>`
2. Deploy: `databricks bundle deploy -t dev --profile <profile>`
3. Confirm the deploy stops when `PAYLOAD_TEXT` is empty:

```bash
PAYLOAD_TEXT= databricks bundle deploy -t dev --profile <profile>
```

4. List the generated file and confirm `local_only/notes.txt` is absent:

```bash
databricks workspace list \
  /Workspace/bundle-examples/sync_include_exclude_and_scripts/dev/<short-name>/files/generated \
  --profile <profile>
```

5. Run the job: `databricks bundle run -t dev read_generated --profile <profile>`
6. Destroy: `databricks bundle destroy -t dev --auto-approve --profile <profile>`
7. Repeat steps 1–6 with `-t prod` (prod root path has no `<short-name>` segment).

| Path | Local | Uploaded |
| --- | --- | --- |
| `generated/payload.txt` | gitignored; written by `predeploy` | yes (`sync.include`) |
| `local_only/notes.txt` | committed | no (`sync.exclude`) |
