"""
Ingest data from custom Faker data source into bronze layer.
"""
import dlt
from pyspark.sql import SparkSession
from pyspark.sql.datasource import DataSource, DataSourceReader
from pyspark.sql.types import StructType
from framework.config import Config
from framework.utils import add_metadata_columns


# Configuration
config = Config.from_spark_config()
spark = SparkSession.getActiveSession()

# # Custom Faker data source implementation
# class FakeDataSourceReader(DataSourceReader):

#     def __init__(self, schema, options):
#         self.schema: StructType = schema
#         self.options = options

#     def read(self, partition):
#         # Library imports must be within the method.
#         from faker import Faker
#         fake = Faker()

#         # Every value in this `self.options` dictionary is a string.
#         num_rows = int(self.options.get("numRows", 3))
#         for _ in range(num_rows):
#             row = []
#             for field in self.schema.fields:
#                 value = getattr(fake, field.name)()
#                 row.append(value)
#             yield tuple(row)


# class FakeDataSource(DataSource):
#     """
#     An example data source for batch query using the `faker` library.
#     """

#     @classmethod
#     def name(cls):
#         return "fake"

#     def schema(self):
#         return "name string, date string, zipcode string, state string"

#     def reader(self, schema: StructType):
#         return FakeDataSourceReader(schema, self.options)


# # Register the data source
# spark.dataSource.register(FakeDataSource)


# Table definition
@dlt.table(
    name=f"{config.bronze_catalog}.{config.bronze_schema}.fake_data",
    comment="Bronze layer table with synthetic data from Faker data source",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def fake_data():
    """
    Reads synthetic data from custom Faker data source.
    Schema: name, date, zipcode, state
    
    Returns:
        DataFrame: Raw fake data with metadata columns
    """
    # Read from custom Faker data source
    df = spark.read.format("fake").option("numRows", "1000").load()
    
    # Add metadata columns
    df = add_metadata_columns(df)
    
    return df

