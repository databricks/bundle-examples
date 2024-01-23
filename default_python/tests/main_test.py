from databricks.connect import DatabricksSession as SparkSession
from default_python import main
from pytest import fixture

# Create a new Databricks Connect session. If this fails,
# check that you have configured Databricks Connect correctly.
# See https://docs.databricks.com/dev-tools/databricks-connect.html.

@fixture(scope="session")
def spark():
    return SparkSession.builder.getOrCreate()

def test_main(spark):
    taxis = main.get_taxis(spark)
    assert taxis.count() > 5
