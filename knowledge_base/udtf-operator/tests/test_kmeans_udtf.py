"""Unit tests for k_means UDTF"""

import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from kmeans_udtf import register


def test_kmeans_udtf(spark, load_fixture):
    """Test k_means UDTF registration and execution"""

    load_fixture("titanic_sample.csv").createOrReplaceTempView("titanic_sample")

    try:
        spark.sql("CREATE SCHEMA IF NOT EXISTS main.test")
        fn = register("main", "test", "test_k_means")
        assert fn == "main.test.test_k_means"

        result = spark.sql(
            """
            SELECT * FROM main.test.test_k_means(
                input_data => TABLE(SELECT * FROM titanic_sample),
                id_column => 'PassengerId',
                columns => array('Age', 'Pclass', 'Survived'),
                k => 3
            )
        """
        ).collect()

        assert len(result) == 8
        assert all(hasattr(r, "id") and hasattr(r, "cluster_id") for r in result)

        cluster_ids = {r.cluster_id for r in result}
        assert len(cluster_ids) <= 3
        assert all(0 <= cid < 3 for cid in cluster_ids)
    finally:
        spark.sql(f"DROP FUNCTION IF EXISTS {fn}")
