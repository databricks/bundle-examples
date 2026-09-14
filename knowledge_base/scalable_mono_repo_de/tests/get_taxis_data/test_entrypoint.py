import pytest
from pyspark.sql import SparkSession
from src.packages.get_taxis_data.get_taxis_data.main import *

@pytest.fixture
def init_spark():
    return get_spark()

def test_entrypoint(init_spark: SparkSession):
    taxis = get_taxis_data(init_spark)
    assert taxis.count() > 5