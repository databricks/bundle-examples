from pyspark import pipelines as dp
from pyspark.sql.functions import col, expr

source_path = spark.conf.get("source_path")


@dp.temporary_view
def customers_changes():
    """Read the change feed incrementally with Auto Loader."""
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.maxFilesPerTrigger", 1)
        .schema("id INT, name STRING, city STRING, operation STRING, seq INT")
        .load(source_path)
    )


# SCD Type 1: one row per key with the latest values. Deleted keys are removed.
dp.create_streaming_table("customers_scd1")
dp.create_auto_cdc_flow(
    target="customers_scd1",
    source="customers_changes",
    keys=["id"],
    sequence_by=col("seq"),
    apply_as_deletes=expr("operation = 'DELETE'"),
    except_column_list=["operation", "seq"],
    stored_as_scd_type=1,
)

# SCD Type 2: full history with __START_AT and __END_AT columns.
dp.create_streaming_table("customers_scd2")
dp.create_auto_cdc_flow(
    target="customers_scd2",
    source="customers_changes",
    keys=["id"],
    sequence_by=col("seq"),
    apply_as_deletes=expr("operation = 'DELETE'"),
    except_column_list=["operation", "seq"],
    stored_as_scd_type=2,
)
