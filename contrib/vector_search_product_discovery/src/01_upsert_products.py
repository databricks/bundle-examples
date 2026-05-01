# Databricks notebook source
# MAGIC %md
# MAGIC # Upsert Products into Vector Search Index
# MAGIC
# MAGIC Reads the product catalog from the JSON file deployed with the bundle,
# MAGIC embeds each product description, then upserts all records into the Vector
# MAGIC Search index. Re-running is safe — upsert is idempotent on `product_id`.

# COMMAND ----------

dbutils.widgets.text(
    "index_name", "main.product_search.product_index", "Index name (3-part UC name)"
)
dbutils.widgets.text("endpoint_name", "product-search-endpoint", "Endpoint name")
dbutils.widgets.text(
    "embedding_model", "databricks-gte-large-en", "Embedding model endpoint"
)
dbutils.widgets.text("embedding_dimension", "1024", "Embedding dimension")
dbutils.widgets.text("data_path", "", "Path to products.json")

index_name = dbutils.widgets.get("index_name")
endpoint_name = dbutils.widgets.get("endpoint_name")
embedding_model = dbutils.widgets.get("embedding_model")
embedding_dim = int(dbutils.widgets.get("embedding_dimension"))
data_path = dbutils.widgets.get("data_path")

# COMMAND ----------

import json
from mlflow.deployments import get_deploy_client

with open(data_path) as f:
    products = json.load(f)

embed = get_deploy_client("databricks")
descriptions = [p["description"] for p in products]

vectors = []
batch_size = 32
for i in range(0, len(descriptions), batch_size):
    response = embed.predict(
        endpoint=embedding_model,
        inputs={"input": descriptions[i : i + batch_size], "dimensions": embedding_dim},
    )
    vectors.extend(item["embedding"] for item in response["data"])

for product, vector in zip(products, vectors):
    product["description_vector"] = vector

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient(disable_notice=True)
index = vsc.get_index(endpoint_name=endpoint_name, index_name=index_name)
index.upsert(products)

print(f"Upserted {len(products)} products into {index_name}")
