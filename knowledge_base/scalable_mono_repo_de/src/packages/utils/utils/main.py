from pyspark.sql import DataFrame
from pyspark.sql.functions import current_timestamp

def add_processing_timestamp(df: DataFrame = None) -> DataFrame:
  """
  Function that returns the current datetime.
  """
  return df.withColumn('processing_timestamp', current_timestamp())