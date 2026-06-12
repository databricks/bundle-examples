# Vector Search: Semantic Product Discovery

A Declarative Automation Bundle demonstrating semantic product search using
[Databricks Vector Search](https://docs.databricks.com/en/generative-ai/vector-search.html).
It automates the full setup — the Unity Catalog schema, the Vector Search endpoint and
index, and the jobs that load and query the catalog — so a single `databricks bundle deploy`
gives you a working semantic-search example to explore and adapt.

## How it works

Keyword search fails when shoppers use different words than what appears in product
descriptions. A customer searching for "something to keep my coffee hot all day" won't
match a product described as an "insulated stainless water bottle with double-wall vacuum
insulation" even though it's the right answer. Semantic search using vector embeddings
matches on meaning, not words.

Product descriptions are embedded at upsert time by the setup job using
[`databricks-gte-large-en`](https://docs.databricks.com/en/machine-learning/foundation-models/supported-models.html).
At query time the query is embedded with the same model and the index returns the nearest
products in vector space.

```
data/products.json  (synced to workspace by bundle deploy)
        ↓  embed descriptions → upsert_data()
product_index  (Direct Access Vector Search index)
        ↓  embed query → similarity_search(query_vector=...)
ranked results
```

## Project structure

```
.
├── databricks.yml                       # Bundle name, variables, and the deploy target
├── data/
│   └── products.json                    # Product catalog — synced to the workspace on deploy
├── resources/
│   ├── schema.yml                       # Unity Catalog schema that namespaces the index
│   ├── vector-search-endpoint.yml       # Vector Search endpoint (managed ANN serving)
│   ├── vector-search-index.yml          # Direct Access index — schema defined inline
│   ├── setup-job.yml                    # Job: embed product descriptions and upsert them
│   └── query-job.yml                    # Job: embed a query and return ranked results
└── src/
    ├── 01_upsert_products.py            # Reads products.json, embeds, calls upsert_data
    └── 02_query_demo.py                 # Semantic search — runs as a job or interactively
```

## Prerequisites

- Databricks workspace with Unity Catalog enabled
- Databricks CLI version 1.1.0 or above
- An existing Unity Catalog catalog (default: `main`)

## Usage

1. Authenticate the CLI:
   ```bash
   databricks auth login --host https://your-workspace.cloud.databricks.com
   ```

2. Configure `databricks.yml`. Set the workspace host and any variable overrides.

3. Deploy the bundle. This creates the schema, endpoint, index, jobs, and syncs `data/products.json`.
   ```bash
   databricks bundle deploy
   ```
   This deploys the default `dev` target in development mode, so resources are namespaced
   per user — jobs and the schema get a `[dev you]` prefix and the endpoint is named after
   you — and several people can deploy into the same workspace without colliding. Use
   `databricks bundle deploy --target prod` for the shared production copy.

   > Vector Search endpoint creation takes a few minutes to reach ONLINE status.

4. Load the catalog by running the bundle. This embeds all product descriptions and upserts them into the index.
   ```bash
   databricks bundle run product_discovery_setup
   ```

5. Pass any natural-language query to search.
   ```bash
   databricks bundle run product_discovery_query --params "query=footwear for slippery wet trails"
   ```

   The job returns the ranked results as JSON — view them with
   `databricks jobs get-run-output <run-id>` or on the run page.

6. Or open `src/02_query_demo.py` in your workspace to run queries interactively.

## Configuration

Override variables at deploy time or run time:

```bash
databricks bundle deploy \
  --var catalog=my_catalog \
  --var schema=product_search \
  --var endpoint_name=my-vs-endpoint \
  --var embedding_model=databricks-gte-large-en \
  --var embedding_dimension=1024
```

| Variable | Default | Description |
|---|---|---|
| `catalog` | `main` | Existing Unity Catalog catalog |
| `schema` | `product_search` | Schema created by the bundle |
| `endpoint_name` | `product-search-endpoint` | Vector Search endpoint name. Shared in prod; the `dev` target overrides it per user. |
| `embedding_model` | `databricks-gte-large-en` | Foundation model used for embeddings |
| `embedding_dimension` | `1024` | Vector dimension. Drives both the index and the embedding requests; immutable after the index is created. |

> **Note:** `embedding_dimension` is immutable after the index is created. Set it (via the
> `embedding_dimension` variable) before the first deploy — the index and the upsert/query
> jobs all read from that one variable.

## Index schema

The index schema lives entirely in `resources/vector-search-index.yml`:

```yaml
direct_access_index_spec:
  schema_json: >-
    {"product_id":"int","name":"string","category":"string","brand":"string",
     "price":"float","description":"string","description_vector":"array<float>"}
  embedding_vector_columns:
    - name: description_vector
      embedding_dimension: ${var.embedding_dimension}
```

`schema_json` is a flat `{"column_name": "type"}` JSON string. `description_vector` stores
the pre-computed embedding produced by `01_upsert_products.py`.

## Updating the product catalog

Edit `data/products.json`, then re-deploy and re-run setup:

```bash
databricks bundle deploy
databricks bundle run product_discovery_setup
```

Upserts are idempotent on `product_id` — existing records are updated, new records added.

## Variant: Delta Sync index

This example uses a **Direct Access** index, which gives full control over when and how
records enter the index via `upsert_data`. If you already have a pipeline writing to a
Delta table, a **Delta Sync** index is often simpler — you point the index at the source
table and it keeps itself up to date. Replace `index_type: DIRECT_ACCESS` and
`direct_access_index_spec` with `index_type: DELTA_SYNC` and `delta_sync_index_spec` in
`resources/vector-search-index.yml`, and remove the upsert job.

## Resources

- [Databricks Vector Search](https://docs.databricks.com/en/generative-ai/vector-search.html)
- [Declarative Automation Bundles](https://docs.databricks.com/dev-tools/bundles/)
- [Foundation Models — GTE Large](https://docs.databricks.com/en/machine-learning/foundation-models/supported-models.html)
