# Vector Search: Semantic Product Discovery

A Declarative Automation Bundle demonstrating **semantic product search** using
[Databricks Vector Search](https://docs.databricks.com/en/generative-ai/vector-search.html).

## The problem

Keyword search fails when shoppers use different words than what appears in product
descriptions. A customer searching for *"something to keep my coffee hot all day"* won't
match a product described as an *"insulated stainless water bottle with double-wall vacuum
insulation"* — even though it's the right answer.

Semantic search using vector embeddings matches on **meaning**, not words.

## How it works

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

## Bundle resources

| Resource | Type | Description |
|---|---|---|
| `product_search_schema` | `schemas` | Unity Catalog schema that namespaces the index |
| `product_search_endpoint` | `vector_search_endpoints` | Managed ANN serving endpoint |
| `product_index` | `vector_search_indexes` | Direct Access index — schema defined in `resources/index.yml` |
| `product_discovery_setup` | `jobs` | Embeds product descriptions and upserts into the index |
| `product_discovery_query` | `jobs` | Embeds a query and returns ranked results |

## Prerequisites

- Databricks workspace with Unity Catalog enabled
- Databricks CLI that supports `vector_search_endpoints` / `vector_search_indexes` as bundle resources
- An existing Unity Catalog catalog (default: `main`)

## Quick start

1. **Authenticate**
   ```bash
   databricks auth login --host https://your-workspace.cloud.databricks.com
   ```

2. **Configure** `databricks.yml` — set the workspace host and any variable overrides

3. **Deploy** — creates the schema, endpoint, index, jobs, and syncs `data/products.json`
   ```bash
   databricks bundle deploy
   ```
   > Vector Search endpoint creation takes a few minutes to reach ONLINE status.

4. **Load the catalog** — embeds all product descriptions and upserts them into the index
   ```bash
   databricks bundle run product_discovery_setup
   ```

5. **Search** — pass any natural-language query
   ```bash
   databricks bundle run product_discovery_query --params "query=footwear for slippery wet trails"
   ```

6. **Or open** `src/02_query_demo.py` in your workspace to run queries interactively

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
| `endpoint_name` | `product-search-endpoint` | Vector Search endpoint name (must be unique per workspace) |
| `embedding_model` | `databricks-gte-large-en` | Foundation model used for embeddings |
| `embedding_dimension` | `1024` | Vector dimension — must match `embedding_dimension` in `resources/index.yml` |

> **Note:** `embedding_dimension` in `resources/index.yml` is hardcoded to `1024` because
> it is immutable after index creation. If you need a different dimension, change the value
> in `index.yml` before the first deploy.

## Index schema

The index schema lives entirely in `resources/index.yml`:

```yaml
direct_access_index_spec:
  schema_json: >-
    {"product_id":"int","name":"string","category":"string","brand":"string",
     "price":"float","description":"string","description_vector":"array<float>"}
  embedding_vector_columns:
    - name: description_vector
      embedding_dimension: 1024
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
`resources/index.yml`, and remove the upsert job.

## Project structure

```
.
├── databricks.yml
├── data/
│   └── products.json               # Product catalog — synced to workspace on deploy
├── resources/
│   ├── schema.yml                  # Unity Catalog schema
│   ├── endpoint.yml                # Vector Search endpoint
│   ├── index.yml                   # Direct Access index
│   ├── setup_job.yml               # Embed + upsert job
│   └── query_demo.yml              # Query job (--params "query=...")
└── src/
    ├── 01_upsert_products.py       # Reads products.json, embeds, calls upsert_data
    └── 02_query_demo.py            # Semantic search — runs as job or interactively
```

## Resources

- [Databricks Vector Search](https://docs.databricks.com/en/generative-ai/vector-search.html)
- [Declarative Automation Bundles](https://docs.databricks.com/dev-tools/bundles/)
- [Foundation Models — GTE Large](https://docs.databricks.com/en/machine-learning/foundation-models/supported-models.html)
