# Databricks notebook source
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import DoubleType, StringType, StructField, StructType


spark = SparkSession.builder.getOrCreate()
schema = StructType(
    [
        StructField("transaction_id", StringType(), False),
        StructField("customer", StringType(), True),
        StructField("amount", DoubleType(), False),
    ]
)

transactions = spark.createDataFrame(
    [
        ("txn-001", "Acme", 150.0),
        ("txn-001", "Acme", 150.0),
        ("txn-002", None, 75.0),
        ("txn-003", "Globex", -10.0),
    ],
    schema,
)

duplicate_ids = (
    transactions.groupBy("transaction_id").count().where(F.col("count") > 1).count()
)
null_customers = transactions.where(F.col("customer").isNull()).count()
non_positive_amounts = transactions.where(F.col("amount") <= 0).count()

failures = {
    "duplicate_transaction_ids": duplicate_ids,
    "null_customers": null_customers,
    "non_positive_amounts": non_positive_amounts,
}
failed_checks = {name: count for name, count in failures.items() if count > 0}

if failed_checks:
    details = ", ".join(f"{name}={count}" for name, count in failed_checks.items())
    raise ValueError(f"Data quality checks failed: {details}")
