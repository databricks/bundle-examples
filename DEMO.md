# Wanderbricks DMS demo — deployment guide

These bundles are wired for the Deployment Metadata Service (DMS) demo. Goal:
populate the **Deployments** page with deployments from **multiple users** and
**multiple commits** (display_name, mode, git_info, versions, operations).

## One-time setup (each person)
1. Get the DMS-enabled CLI (built from `shreyas-goenka/deployment-metadata-service`)
   — grab the shared snapshot binary, put it on PATH (or call by path).
2. `git clone https://github.com/databricks/bundle-examples && cd bundle-examples`
   then `git checkout wanderbricks-demo` (use the **pushed** branch/fork).
3. Authenticate to the demo workspace **as yourself**:
   `databricks auth login --host <demo-workspace-url> -p demo`
   (the bundles don't hardcode a host — it comes from your profile.)
4. The pipelines/SQL job write outputs to `${catalog}.${schema}`; pass a **writable**
   UC catalog: `--var catalog=<your_catalog>`. (`samples` is read-only; the serverless
   reviews job needs no writable catalog.)

## Always deploy with the DMS flags
```sh
DATABRICKS_BUNDLE_MANAGED_STATE=true DATABRICKS_BUNDLE_ENGINE=direct \
  databricks bundle deploy -p demo [--var catalog=<writable_catalog>]
```

## Deploying from DIFFERENT USERS
`created_by` / `completed_by` is always the authenticated identity — it can't be
spoofed; switch who deploys.

- **Many owners across the list:** each person deploys (with their own auth). In
  `dev` mode every deploy is namespaced per user (`[dev <user>]`, root_path under
  your home), so the *same* bundle deployed by N people becomes **N separate
  deployments**, each owned by a different person.
- **Many owners on ONE deployment's history:** deploy a **shared** target
  (`mode: production` with a fixed `root_path`, no per-user prefix) so everyone
  hits the **same `deployment_id`** — the version timeline then shows alternating
  `created_by`/`completed_by`.

## Deploying from DIFFERENT COMMITS
`git_info` (origin/branch/commit) is recorded per version. The commit must be
**pushed** to resolve as a link in the UI (local-only commits won't link).

- Push `wanderbricks-demo` to a shared branch/fork.
- Deploy → version 1 (commit A). Make a small change → commit → push → deploy
  again → version 2 (commit B). Repeat for a timeline of distinct commits.
- Or tag commits and deploy from each `git checkout <tag>`.

## Suggested run-of-show
1. Person A deploys all bundles from commit A (seeds the list, owned by A).
2. Persons B & C each deploy a couple bundles (multiple owners appear).
3. Someone pushes a change and redeploys one bundle → second version with a new
   commit (and a different `created_by` if a different person).
4. Open **Deployments** (`?conf_enable=databricks.fe.dabs.deploymentsUi`) and walk
   through display_name, mode, git_info, versions, and per-resource operations.
