# Databricks notebook source
from pyspark.sql.types import DecimalType, NumericType, StringType, StructField, StructType


# Simulated monetary amounts use a fixed-point decimal (not float) to avoid binary floating-point rounding drift.
observed_source_schema = StructType(
    [
        StructField("transaction_id", StringType(), False),
        StructField("amount", DecimalType(12, 2), False),
    ]
)


def validate_amount_schema(schema):
    """Raise TypeError if the schema's amount field is not numeric."""
    amount_type = schema["amount"].dataType
    if not isinstance(amount_type, NumericType):
        raise TypeError(
            "Schema contract violation in simulated source schema (no source table): "
            f"expected amount to be numeric, found {amount_type.simpleString()}; "
            f"observed schema {schema.simpleString()}"
        )


validate_amount_schema(observed_source_schema)
