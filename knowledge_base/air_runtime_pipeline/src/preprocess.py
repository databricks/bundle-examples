"""Task 1 (serverless): prepare data before training.

Writes a small dataset file into a shared workspace directory and publishes its
path as a task value for the downstream evaluate task. Job task compute is
ephemeral and not shared between tasks, so intermediate data is written to the
workspace file system (durable), which serverless mounts under /Workspace.
"""

import os
import sys


def main() -> None:
    shared_dir = sys.argv[1]
    epochs = sys.argv[2] if len(sys.argv) > 2 else "1"
    dataset_path = f"{shared_dir}/dataset.csv"

    # A stand-in "prepared dataset". A real job would produce features here.
    rows = ["id,label"] + [f"{i},{i % 2}" for i in range(8)]

    os.makedirs(shared_dir, exist_ok=True)
    with open(dataset_path, "w") as f:
        f.write("\n".join(rows) + "\n")
    print(f"[preprocess] prepared dataset for {epochs} epoch(s): {len(rows) - 1} rows -> {dataset_path}")

    # Publish the path so the evaluate task can read the same file back.
    from pyspark.dbutils import DBUtils
    from pyspark.sql import SparkSession

    dbutils = DBUtils(SparkSession.builder.getOrCreate())
    dbutils.jobs.taskValues.set(key="dataset_path", value=dataset_path)
    print("[preprocess] published task value: dataset_path")
    print("[preprocess] done")


if __name__ == "__main__":
    main()
