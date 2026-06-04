import pytest
from pyspark.sql import SparkSession, DataFrame
from src.packages.get_taxis_data.get_taxis_data.main import get_spark
from src.packages.utils.utils.main import *


@pytest.fixture
def init_spark():
    return get_spark()


@pytest.fixture
def generate_dataframe(init_spark: SparkSession):
    return init_spark.createDataFrame([(1, "foo"), (2, "bar")], ["id", "name"])


def test_processing_timestamp(generate_dataframe: DataFrame):
    df = add_processing_timestamp(df=generate_dataframe)
    assert "processing_timestamp" in df.columns