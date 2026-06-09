# Wanderbricks DMS demo

Six **domain data products** built on the `samples.wanderbricks` dataset (a fictional
vacation-rental marketplace). Each bundle is an owned, deployable unit — the realistic
"one bundle per domain/team" shape — and together they populate the **Deployments** page
across resource types, targets, owners, and commits.

| Bundle (`wanderbricks/…`) | Owner | Resources | Deploy vars |
|---|---|---|---|
| `revenue` | Analytics Eng | Lakeflow pipeline (medallion) + SQL summary job | `catalog`, `warehouse_id` |
| `reviews` | Trust & Quality | Lakeflow Python pipeline | `catalog` |
| `host_analytics` | Supply | SQL warehouse job (host KPIs) | `catalog`, `warehouse_id` |
| `guest_analytics` | Growth | serverless Python job (segmentation) | `catalog` |
| `demand_ml` | Data Science | MLflow experiment + training job | — |
| `platform` | Platform | all-purpose cluster + secret scope | — |

## One-time setup (each person)
1. Get the DMS-enabled CLI (built from `shreyas-goenka/deployment-metadata-service`).
2. `git clone https://github.com/databricks/bundle-examples && cd bundle-examples && git checkout wanderbricks-demo`
3. Authenticate **as yourself**: `databricks auth login --host <workspace> -p demo` (no host is committed).
4. Have a **writable UC catalog** for outputs and a **SQL warehouse** id for the warehouse jobs.

## Deploy (run inside each `wanderbricks/<bundle>` folder)
```sh
DATABRICKS_BUNDLE_MANAGED_STATE=true DATABRICKS_BUNDLE_ENGINE=direct \
  databricks bundle deploy -t <dev|staging|prod> -p demo \
  [--var catalog=<your_catalog>] [--var warehouse_id=<your_wh>]
```

## Making the deployments page rich
- **Different users** — each person deploys with their own auth → `created_by` varies. `dev` mode namespaces per user (separate deployments); a shared `prod`/`staging` target (production mode, `/Workspace/Shared/...`) gives multiple owners on one deployment's version history.
- **Different commits** — push the branch, then deploy → edit → push → deploy for a version timeline with distinct, resolvable commits.
- **Different targets/modes** — `dev` (DEVELOPMENT) vs `staging`/`prod` (PRODUCTION).
- **A failure to debug** — flip `platform`'s cluster `node_type_id` to an AWS type (`i3.xlarge`) on this Azure workspace: deploy fails with `Node type i3.xlarge is not supported. Supported: Standard_DS…`, a one-line fix the in-workspace AI assistant resolves.
