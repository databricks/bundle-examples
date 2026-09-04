# Databricks notebook source
from pyspark.sql.types import StringType, StructField, StructType


schema = StructType(
    [
        StructField("transaction_id", StringType(), False),
        StructField("amount", StringType(), False),
    ]
)
amount_type = schema["amount"].dataType.simpleString()
numeric_types = {"byte", "short", "int", "bigint", "float", "double"}

if amount_type not in numeric_types and not amount_type.startswith("decimal"):
    raise TypeError(
        f"Schema drift detected: expected amount to be numeric, found {amount_type}"
    )
