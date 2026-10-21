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
2. Validate: `databricks bundle validate -t dev`
3. Deploy: `databricks bundle deploy -t dev`
4. Repeat steps 2–3 with `-t staging` and `-t prod`.
5. Check prefixed names:

```bash
databricks bundle validate -t dev -o json | jq -r '.resources.jobs.presets_demo.name'
```

| Target | Name prefix | Pause status | Concurrency |
| --- | --- | --- | --- |
| `dev` | `[dev presets <user>]` | `PAUSED` | `4` |
| `staging` | `[staging]` | `PAUSED` | `2` |
| `prod` | `[prod]` | `UNPAUSED` | `1` |

## Notes

* The bundle deploys under `/Workspace/bundle-examples`. Create that folder and limit who can manage it, or change `root_path`.
* Environment lists append on override. Select another base environment with `environment_key` on a task.
* The CLI profile must point to the same host as that target's `workspace.host`.
