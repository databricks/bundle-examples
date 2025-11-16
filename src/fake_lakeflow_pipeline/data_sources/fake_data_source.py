from pyspark.sql.datasource import DataSource, DataSourceReader
from pyspark.sql.types import StructType

%pip install faker

class FakeDataSourceReader(DataSourceReader):

    def __init__(self, schema, options):
        self.schema: StructType = schema
        self.options = options

    def read(self, partition):
        # Library imports must be within the method.
        from faker import Faker
        fake = Faker()

        # Every value in this `self.options` dictionary is a string.
        num_rows = int(self.options.get("numRows", 3))
        for _ in range(num_rows):
            row = []
            for field in self.schema.fields:
                value = getattr(fake, field.name)()
                row.append(value)
            yield tuple(row)


class FakeDataSource(DataSource):
    """
    An example data source for batch query using the `faker` library.
    """

    @classmethod
    def name(cls):
        return "fake"

    def schema(self):
        return "name string, date string, zipcode string, state string"

    def reader(self, schema: StructType):
        return FakeDataSourceReader(schema, self.options)
    
# Register data source
spark.dataSource.register(FakeDataSource)
