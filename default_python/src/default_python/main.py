from pyspark.sql import SparkSession

def get_taxis(spark: SparkSession):    
  return spark.read.table("samples.nyctaxi.trips")

def main():
  from databricks.connect import DatabricksSession as SparkSession
  spark = SparkSession.builder.getOrCreate()
  get_taxis(spark).show(5)

if __name__ == '__main__':
  main()
