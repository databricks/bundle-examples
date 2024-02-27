from databricks.connect import DatabricksSession as SparkSession
from pytest import fixture
from default_python import main
from pytest import fixture

@fixture(scope="session")
def spark():
    spark = SparkSession.builder.getOrCreate()
    yield spark
    spark.stop()


def test_main(spark: SparkSession):
    taxis = main.get_taxis(spark)
    assert taxis.count() > 5
