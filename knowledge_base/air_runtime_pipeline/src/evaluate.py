"""Task 3 (serverless): evaluate after training.

Reads the dataset path published by the preprocess task (cross-task data flow)
and stands in for a post-training eval / model-registration step.
"""


def main() -> None:
    dataset_path = "<unknown>"
    try:
        from pyspark.dbutils import DBUtils
        from pyspark.sql import SparkSession

        dbutils = DBUtils(SparkSession.builder.getOrCreate())
        dataset_path = dbutils.jobs.taskValues.get(
            taskKey="preprocess", key="dataset_path", default="<none>", debugValue="<debug>"
        )
    except Exception as e:  # noqa: BLE001
        print(f"[evaluate] could not read task value (non-fatal): {e}")

    print(f"[evaluate] scoring model trained on {dataset_path}")
    print("[evaluate] eval_accuracy=0.91")
    print("[evaluate] done")


if __name__ == "__main__":
    main()
