from pyspark.sql import SparkSession, DataFrame

# Create a new Databricks Connect session. If this fails,
# check that you have configured Databricks Connect correctly.
# See https://docs.databricks.com/dev-tools/databricks-connect.html.
def get_spark() -> SparkSession:
  try:
    from databricks.connect import DatabricksSession
    return DatabricksSession.builder.serverless(True).getOrCreate()
  except ImportError:
    return SparkSession.builder.getOrCreate()
  
def get_taxis_data(spark: SparkSession) -> DataFrame:
  """
  Get pre-loaded taxis data from the Databricks workspace.
  """
  return spark.read.table("samples.nyctaxi.trips")