# Presets and multi-workspace targets

## What this example shows

This example shows `presets` on three targets: `dev`, `staging`, and `prod`.

Each target uses a different `workspace.host` placeholder. You can set an optional `profile`.

The bundle defines one job with two tasks. The job uses serverless environments with `environment_version`. The job has a schedule.

Target overrides show:

1. A task override by `task_key` (list merge).
2. An environment selection override on a task (`environment_key`). Job clusters merge by `job_cluster_key` the same way tasks merge by `task_key`.
3. A staging-only job parameter change.

`mode: development` sets defaults such as a name prefix and paused schedules. Most `presets` values override those defaults. In development mode, schedules stay paused even if you set `trigger_pause_status: UNPAUSED`.

## Prerequisites

* Databricks CLI v0.236.0 or above (`source_linked_deployment` needs this version or later).
* Three Databricks workspaces, or one workspace for a dry run.
* Matching profiles in `~/.databrickscfg` when you use `profile`.

## Configure

1. Open `databricks.yml`.
2. Set `workspace.host` under `dev` to your development workspace URL.
3. Set `workspace.host` under `staging` to your staging workspace URL.
4. Set `workspace.host` under `prod` to your production workspace URL.
5. Set `workspace.root_path` under `prod` to a user or principal path you own.
6. Uncomment and set `profile` under a target when that target must use a named profile.
7. Confirm each `profile` name exists in `~/.databrickscfg`.

## Deploy to each target

1. Validate the default target: `databricks bundle validate -t dev`
2. Deploy development: `databricks bundle deploy -t dev`
3. Validate staging: `databricks bundle validate -t staging`
4. Deploy staging: `databricks bundle deploy -t staging`
5. Validate production: `databricks bundle validate -t prod`
6. Deploy production: `databricks bundle deploy -t prod`

## What changes per target

| Setting | `dev` | `staging` | `prod` |
| --- | --- | --- | --- |
| Job name | `[dev presets <user>] presets_demo` | `[staging] presets_demo` | `[prod] presets_demo` |
| Tags | `env=dev`, `team=examples` (plus development `dev` tag) | `env=staging`, `team=examples` | `env=prod`, `team=examples` |
| Schedule pause status | `PAUSED` (development mode) | `PAUSED` (preset) | `UNPAUSED` (preset) |
| `max_concurrent_runs` | `4` | `2` | `1` |
| `pipelines_development` | `true` | `false` | `false` |
| `source_linked_deployment` | `true` (dev only) | unset | unset |
| `batch_size` parameter | `100` | `50` | `100` |
| `process` `timeout_seconds` | unset | `1800` | `3600` |
| `process` `environment_key` | `default` (`environment_version` `4`) | `default` (`4`) | `heavy` (`5`) |

## How target overrides merge

* Lists of tasks merge by `task_key`. Matching keys join fields. New keys append.
* Lists of job clusters merge by `job_cluster_key`.
* Lists of environments do not key-merge. Select another environment from the base list with `environment_key` on a task.
* Maps join by key. The target value replaces the top-level value for the same key.
* Scalars in the target replace top-level scalars.
* You cannot unset a field with an empty target value. Omit the override, or set an explicit new value.

## See the result

After you set real hosts (and profiles if needed), run:

```bash
databricks bundle validate -t dev -o json | jq -r '.resources.jobs.presets_demo.name'
databricks bundle validate -t staging -o json | jq -r '.resources.jobs.presets_demo.name'
databricks bundle validate -t prod -o json | jq -r '.resources.jobs.presets_demo.name'
```

Expected names:

* `dev`: `[dev presets <your_short_name>] presets_demo`
* `staging`: `[staging] presets_demo`
* `prod`: `[prod] presets_demo`

Inspect pause status and concurrency:

```bash
databricks bundle validate -t dev -o json | jq '.resources.jobs.presets_demo | {name, max_concurrent_runs, schedule, tags, parameters}'
databricks bundle validate -t staging -o json | jq '.resources.jobs.presets_demo | {name, max_concurrent_runs, schedule, tags, parameters, tasks}'
databricks bundle validate -t prod -o json | jq '.resources.jobs.presets_demo | {name, max_concurrent_runs, schedule, tags, parameters, tasks, environments}'
```

## Edge cases

* **Development mode vs presets:** Presets override most development defaults. Development mode still forces paused schedules and triggers. A custom `name_prefix` in development mode must include your username or `${workspace.current_user.short_name}`.
* **Resource pause vs presets:** If a job sets `schedule.pause_status: UNPAUSED`, that value overrides the `trigger_pause_status` preset.
* **`source_linked_deployment`:** Use this preset only on `dev`. It applies to workspace UI deploys. The CLI `databricks bundle deploy` command ignores it.
* **Wrong profile or host:** A profile that points to a different host than `workspace.host` causes auth or deploy errors. Align `profile` and `host` for each target.
* **Production `root_path`:** `mode: production` requires `workspace.root_path` so only one copy of the bundle is deployed.
* **Serverless:** This job uses serverless environments. Classic `job_clusters` merge by `job_cluster_key`.

## Clean up

1. Destroy development: `databricks bundle destroy -t dev`
2. Destroy staging: `databricks bundle destroy -t staging`
3. Destroy production: `databricks bundle destroy -t prod`

Confirm each prompt. Destroy removes only resources that this bundle owns for that target.
