"""K-Means UDTF for Unity Catalog"""

import inspect
from pyspark.sql import SparkSession


class SklearnKMeans:
    """K-means clustering UDTF handler"""

    def __init__(self):
        self.id_col = None
        self.feature_cols = None
        self.k = None
        self.rows = []
        self.features = []

    def eval(self, row, id_column, columns, k):
        """Process each row"""
        if self.id_col is None:
            self.id_col = id_column
            self.feature_cols = columns
            self.k = max(1, int(k))

        row_dict = row.asDict(recursive=False)
        self.rows.append(row_dict)

        feats = [float(row_dict.get(c) or 0.0) for c in self.feature_cols]
        self.features.append(feats)

    def terminate(self):
        """Emit cluster assignments"""
        if not self.rows:
            return

        import numpy as np
        from sklearn.cluster import KMeans

        X = np.asarray(self.features, dtype=float)
        n_clusters = min(self.k, X.shape[0])

        model = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        labels = model.fit_predict(X)

        for row_dict, label in zip(self.rows, labels):
            yield str(row_dict[self.id_col]), int(label)


def register(catalog: str, schema: str, name: str = "k_means"):
    """Register k_means UDTF in Unity Catalog"""
    spark = SparkSession.builder.getOrCreate()
    source = inspect.getsource(SklearnKMeans)

    spark.sql(f"""
        CREATE OR REPLACE FUNCTION {catalog}.{schema}.{name}(
            input_data TABLE,
            id_column STRING,
            columns ARRAY<STRING>,
            k INT
        )
        RETURNS TABLE (id STRING, cluster_id INT)
        LANGUAGE PYTHON
        HANDLER 'SklearnKMeans'
        AS $$
{source}
        $$
    """)

    return f"{catalog}.{schema}.{name}"
