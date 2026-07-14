"""Task 1 (serverless): prepare data before training.

Stands in for a data-prep step and publishes a dataset path as a task value that
the downstream evaluate task consumes — data flow a single-task submit can't
express.
"""

import sys


def main() -> None:
    epochs = sys.argv[1] if len(sys.argv) > 1 else "1"
    dataset_path = "/tmp/air_runtime_pipeline/dataset"
    print(f"[preprocess] preparing dataset for {epochs} epoch(s) -> {dataset_path}")

    try:
        from pyspark.dbutils import DBUtils
        from pyspark.sql import SparkSession

        dbutils = DBUtils(SparkSession.builder.getOrCreate())
        dbutils.jobs.taskValues.set(key="dataset_path", value=dataset_path)
        print("[preprocess] published task value: dataset_path")
    except Exception as e:  # noqa: BLE001 - task values best-effort in the demo
        print(f"[preprocess] could not set task value (non-fatal): {e}")

    print("[preprocess] done")


if __name__ == "__main__":
    main()
