# Presets and multi-workspace targets

This Declarative Automation Bundles example shows `presets` on `dev`, `staging`, and `prod` targets.
Each target uses a different `workspace.host` placeholder and an optional `profile`.
It also shows target overrides for tasks, environments, and a staging-only job parameter.

For more information, see the [deployment modes documentation](https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes).

## Prerequisites

* Databricks CLI v1.20.0 or above
* Three workspaces, or one workspace for a dry run
* Profiles in `~/.databrickscfg` when you set `profile`

## Usage

1. Set each target `workspace.host` in `databricks.yml`. Uncomment `profile` if needed.
2. Set `workspace.root_path` under `prod` to a path you own.
3. Validate: `databricks bundle validate -t dev`
4. Deploy: `databricks bundle deploy -t dev`
5. Repeat steps 3–4 with `-t staging` and `-t prod`.
6. Check prefixed names:

```bash
databricks bundle validate -t dev -o json | jq -r '.resources.jobs.presets_demo.name'
```

| Target | Name prefix | Pause status | Concurrency |
| --- | --- | --- | --- |
| `dev` | `[dev presets <user>]` | `PAUSED` | `4` |
| `staging` | `[staging]` | `PAUSED` | `2` |
| `prod` | `[prod]` | `UNPAUSED` | `1` |

## Notes

* `mode: development` rejects `presets.trigger_pause_status: UNPAUSED`. A job may still set `schedule.pause_status: UNPAUSED`. Development mode also adds a `dev=<your_short_name>` tag beside `env` and `team`.
* Tasks merge by `task_key`. Job clusters merge by `job_cluster_key`. Job parameters merge by `name`.
* Environment lists append on override. Select another base environment with `environment_key` on a task. You cannot unset a field with an empty override.
* `source_linked_deployment` works in the workspace UI. The CLI warns that it is available only there and deploys file copies.
* `pipelines_development` only affects pipelines. This bundle has none.
* Run `databricks bundle destroy -t <target>` to remove a target.
* The CLI profile must point to the same host as that target's `workspace.host`.
