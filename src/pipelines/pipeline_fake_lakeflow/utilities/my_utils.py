"""
The 'utilities' folder contains Python modules.
Keeping them separate provides a clear overview
of utilities you can reuse across your transformations.
"""
from pyspark.sql.functions import udf
from pyspark.sql.types import BooleanType
import re

@udf(returnType=BooleanType())
def is_valid_email(email):
    """
    This function checks if the given email address has a valid format using regex.
    Returns True if valid, False otherwise.

    Example usage:

    from pyspark import pipelines as dp
    from pyspark.sql.functions import col
    from utilities import new_utils

    @dp.table
    def my_table():
        return (
            spark.read.table("samples.wanderbricks.users")
            .withColumn("valid_email", new_utils.is_valid_email(col("email")))
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if email is None:
        return False
    return re.match(pattern, email) is not None