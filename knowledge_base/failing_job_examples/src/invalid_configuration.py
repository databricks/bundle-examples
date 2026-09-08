# Databricks notebook source
batch_size_value = dbutils.widgets.get("batch_size")

try:
    batch_size = int(batch_size_value)
except ValueError:
    raise ValueError(
        f"Invalid job configuration: batch_size must be an integer, found {batch_size_value!r}"
    ) from None

if batch_size <= 0:
    raise ValueError(
        f"Invalid job configuration: batch_size must be greater than zero, found {batch_size}"
    )
