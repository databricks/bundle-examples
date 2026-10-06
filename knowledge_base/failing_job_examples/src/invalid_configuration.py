# Databricks notebook source
def parse_positive_batch_size(value):
    """Parse *value* as a positive integer batch size.

    Raises ValueError with a descriptive message if *value* cannot be
    converted to an integer or is not greater than zero.
    """
    try:
        batch_size = int(value)
    except ValueError:
        raise ValueError(
            f"Invalid job configuration: batch_size must be an integer, found {value!r}"
        ) from None

    if batch_size <= 0:
        raise ValueError(
            f"Invalid job configuration: batch_size must be greater than zero, found {batch_size}"
        )

    return batch_size


batch_size_value = dbutils.widgets.get("batch_size")
batch_size = parse_positive_batch_size(batch_size_value)
