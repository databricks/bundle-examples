# Databricks notebook source
# MAGIC %md
# MAGIC # Semantic Product Search Demo
# MAGIC
# MAGIC Queries the Vector Search index to find products that match a natural-language
# MAGIC description. Try queries that would fail keyword search — e.g. *"something to
# MAGIC keep my coffee hot all day"* or *"gear for sleeping outside in freezing weather"*.

# COMMAND ----------

dbutils.widgets.text(
    "index_name", "main.product_search.product_index", "Index name (3-part UC name)"
)
dbutils.widgets.text("endpoint_name", "product-search-endpoint", "Endpoint name")
dbutils.widgets.text(
    "embedding_model", "databricks-gte-large-en", "Embedding model endpoint"
)
dbutils.widgets.text("embedding_dimension", "1024", "Embedding dimension")
dbutils.widgets.text(
    "query", "warm insulated jacket for cold mountain weather", "Search query"
)
dbutils.widgets.text("num_results", "5", "Number of results")

index_name = dbutils.widgets.get("index_name")
endpoint_name = dbutils.widgets.get("endpoint_name")
embedding_model = dbutils.widgets.get("embedding_model")
embedding_dim = int(dbutils.widgets.get("embedding_dimension"))
query = dbutils.widgets.get("query")
num_results = int(dbutils.widgets.get("num_results"))

# COMMAND ----------

from mlflow.deployments import get_deploy_client
from databricks.vector_search.client import VectorSearchClient

embed = get_deploy_client("databricks")
vsc = VectorSearchClient(disable_notice=True)
index = vsc.get_index(endpoint_name=endpoint_name, index_name=index_name)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run a query

# COMMAND ----------

import pandas as pd

# Direct access indexes don't auto-embed queries — embed the query text first.
query_vector = embed.predict(
    endpoint=embedding_model,
    inputs={"input": [query], "dimensions": embedding_dim},
)["data"][0]["embedding"]

results = index.similarity_search(
    query_vector=query_vector,
    columns=["product_id", "name", "category", "brand", "price", "description"],
    num_results=num_results,
)

result_columns = [
    "product_id",
    "name",
    "category",
    "brand",
    "price",
    "description",
    "score",
]
rows = results["result"]["data_array"]
df = pd.DataFrame(rows, columns=result_columns)
df.index += 1
print(df.to_string())

# Surface the ranked results to `databricks bundle run` / `jobs get-run-output`.
# (The print above stays for interactive notebook use.)
dbutils.notebook.exit(df.to_json(orient="records"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Example queries to try
# MAGIC
# MAGIC These queries use different vocabulary than the product descriptions, demonstrating
# MAGIC that semantic search finds the right products even without exact keyword matches.
# MAGIC
# MAGIC | Query | Expected top results |
# MAGIC |---|---|
# MAGIC | `jacket built for mountaineering in sub-zero conditions` | Alpine Thermal Jacket |
# MAGIC | `something to keep beverages hot or cold all day` | Insulated Stainless Water Bottle |
# MAGIC | `footwear for slippery wet trails` | Waterproof Mid Hiking Boot |
# MAGIC | `staying warm overnight in below-freezing temperatures outdoors` | 20°F Down Sleeping Bag |
# MAGIC | `grinding beans at home for a fresh espresso` | Burr Coffee Grinder |
# MAGIC | `lightweight shelter for a solo overnight trip` | Ultralight Backpacking Tent |
# MAGIC | `reduce muscle soreness after a hard workout` | Vibrating Foam Roller |
# MAGIC | `improve posture while working at a computer` | Portable Laptop Stand |

# COMMAND ----------

# MAGIC %md
# MAGIC ## Batch comparison across several queries

# COMMAND ----------

example_queries = [
    "jacket built for mountaineering in sub-zero conditions",
    "footwear for slippery wet trails",
    "staying warm overnight in below-freezing temperatures outdoors",
    "grinding beans at home for a fresh espresso",
    "reduce muscle soreness after a hard workout",
]

print(f"{'Query':<55} {'Top result'}")
print("-" * 90)

for q in example_queries:
    qv = embed.predict(
        endpoint=embedding_model,
        inputs={"input": [q], "dimensions": embedding_dim},
    )["data"][0]["embedding"]
    r = index.similarity_search(
        query_vector=qv, columns=["name", "category"], num_results=1
    )
    top = r["result"]["data_array"]
    top_name = top[0][0] if top else "—"
    top_cat = top[0][1] if top else ""
    print(f"{q:<55} {top_name} ({top_cat})")
