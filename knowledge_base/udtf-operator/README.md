# User-Defined Table Functions in Unity Catalog

This project demonstrates how to create and register a Python User-Defined Table Function (UDTF) in Unity Catalog using Databricks Asset Bundles. Once registered, the UDTF becomes available to analysts and other users across your Databricks workspace, callable directly from SQL queries.

**Learn more:** [Introducing Python UDTFs in Unity Catalog](https://www.databricks.com/blog/introducing-python-user-defined-table-functions-udtfs-unity-catalog)

## Concrete example: Definition and Usage

This project includes a k-means clustering algorithm as a UDTF.

### Python Implementation

The UDTF is defined in [`src/kmeans_udtf.py`](src/kmeans_udtf.py) as follows:

```python
class SklearnKMeans:
    def __init__(self, id_column: str, columns: list, k: int):
        self.id_column = id_column
        self.columns = columns
        self.k = k
        self.data = []

    def eval(self, row: Row):
        # Process each input row
        self.data.append(row)

    def terminate(self):
        # Perform computation and yield results
        # ... clustering logic ...
        for record in results:
            yield (record.id, record.cluster)
```

### SQL Usage

Once registered, any analyst or SQL user in your workspace can call the UDTF from SQL queries:

```sql
SELECT * FROM main.your_schema.k_means(
    input_data => TABLE(SELECT * FROM my_data),
    id_column => 'id',
    columns => array('feature1', 'feature2', 'feature3'),
    k => 3
)
```

The UDTF integrates seamlessly with:
- SQL queries in notebooks
- Databricks SQL dashboards
- Any tool that connects to your Databricks workspace via SQL

See [`src/sample_notebook.ipynb`](src/sample_notebook.ipynb) for complete examples.

## Getting Started With This Project

### Prerequisites

* Databricks workspace with Unity Catalog enabled
* Databricks CLI installed and configured
* Python with `uv` package manager

### Setup and Testing

1. Install dependencies:
   ```bash
   uv sync --dev
   ```

2. Run tests (registers and executes the UDTF):
   ```bash
   uv run pytest
   ```

### Deployment

Deploy to dev:
```bash
databricks bundle deploy --target dev
databricks bundle run register_udtf_job --target dev
```

Deploy to production:
```bash
databricks bundle deploy --target prod
databricks bundle run register_udtf_job --target prod
```

The UDTF will be registered at `main.your_username.k_means` (dev) or `main.prod.k_means` (prod).

## Advanced Topics

**CI/CD Integration:**
- Set up CI/CD for Databricks Asset Bundles following the [CI/CD documentation](https://docs.databricks.com/dev-tools/bundles/ci-cd.html)
- To automatically register the UDTF on deployment, add `databricks bundle run -t prod register_udtf_job` to your deployment script after `databricks bundle deploy -t prod` (alternatively, the job in `resources/udtf_job.yml` can use a schedule for registration)

**Serverless compute vs. clusters:** The job uses serverless compute by default. Customize catalog/schema in `databricks.yml` or via job parameters.

## Learn More

- [Introducing Python UDTFs in Unity Catalog](https://www.databricks.com/blog/introducing-python-user-defined-table-functions-udtfs-unity-catalog) - Blog post covering UDTF concepts and use cases
- [Python UDTFs Documentation](https://docs.databricks.com/udf/udtf-unity-catalog.html) - Official documentation
- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/index.html) - CI/CD and deployment framework
- [Unity Catalog Functions](https://docs.databricks.com/udf/unity-catalog.html) - Governance and sharing
