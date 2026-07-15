"""Task 3 (serverless): evaluate after training.

Reads back the dataset the preprocess task wrote (proving cross-task data flow
through a durable workspace location), and stands in for a post-training eval or
model-registration step.
"""

from pyspark.dbutils import DBUtils
from pyspark.sql import SparkSession


def main() -> None:
    dbutils = DBUtils(SparkSession.builder.getOrCreate())
    dataset_path = dbutils.jobs.taskValues.get(taskKey="preprocess", key="dataset_path")
    print(f"[evaluate] reading dataset from {dataset_path}")

    with open(dataset_path) as f:
        rows = f.read().splitlines()

    num_examples = max(len(rows) - 1, 0)  # minus the header
    print(f"[evaluate] scored model on {num_examples} examples")
    print("[evaluate] eval_accuracy=0.91")
    print("[evaluate] done")


if __name__ == "__main__":
    main()
