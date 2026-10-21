# Presets and multi-workspace targets

This Declarative Automation Bundles example shows `presets` on `dev`, `staging`, and `prod` targets with different `workspace.host` placeholders and optional `profile` values. It also shows target overrides for tasks, environments, and a staging-only job parameter.

For more information, see the [deployment modes documentation](https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes).

## Prerequisites

* Databricks CLI v0.236.0 or above
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

* `mode: development` adds its own defaults. Presets override most of them. Schedules stay paused in development mode.
* Tasks merge by `task_key`. Job clusters merge by `job_cluster_key`.
* Environment lists append on override. Select another base environment with `environment_key` on a task.
* You cannot unset a field with an empty override. Omit the key, or set a new value.
* `source_linked_deployment` applies only to workspace UI deploys. The CLI ignores it.
