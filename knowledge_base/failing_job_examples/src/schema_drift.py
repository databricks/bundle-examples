# Databricks notebook source
from pyspark.sql.types import DecimalType, NumericType, StringType, StructField, StructType


observed_source_schema = StructType(
    [
        StructField("transaction_id", StringType(), False),
        StructField("amount", DecimalType(12, 2), False),
    ]
)
amount_type = observed_source_schema["amount"].dataType

if not isinstance(amount_type, NumericType):
    raise TypeError(
        "Schema contract violation in simulated source schema (no source table): "
        f"expected amount to be numeric, found {amount_type.simpleString()}; "
        f"observed schema {observed_source_schema.simpleString()}"
    )
