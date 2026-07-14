"""Training entrypoint that reads hyperparameters and logs to MLflow.

Shipped inside the code_source tarball. Reads the hyperparameters sidecar via
$HYPERPARAMETERS_PATH and logs a couple of values so the run is observable in the
MLflow experiment configured on the task.
"""

import os

import yaml


def load_hyperparameters() -> dict:
    path = os.environ.get("HYPERPARAMETERS_PATH")
    if path and os.path.exists(path):
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}


def main() -> None:
    rank = os.environ.get("NODE_RANK", "0")
    hp = load_hyperparameters()
    print(f"[train.py] rank={rank} hyperparameters={hp}")

    if rank in ("0", ""):
        try:
            import mlflow

            with mlflow.start_run():
                for key, value in hp.items():
                    if isinstance(value, (int, float, str)):
                        mlflow.log_param(key, value)
                mlflow.log_metric("final_loss", 0.123)
            print("[train.py] logged params + metric to MLflow")
        except Exception as e:  # noqa: BLE001 - demo: never fail on logging
            print(f"[train.py] MLflow logging skipped: {e}")

    print("[train.py] training complete")


if __name__ == "__main__":
    main()
