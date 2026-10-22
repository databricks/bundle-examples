import sys
from datetime import datetime, timezone

import mlflow
import pandas as pd
from databricks.connect import DatabricksSession
from mlflow import MlflowClient
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

experiment_name, model_name, inference_table = sys.argv[1:4]

mlflow.set_registry_uri("databricks-uc")
mlflow.set_experiment(experiment_name)

X, y = load_iris(return_X_y=True, as_frame=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

with mlflow.start_run():
    model = LogisticRegression(max_iter=200).fit(X_train, y_train)
    mlflow.log_metric("accuracy", model.score(X_test, y_test))
    info = mlflow.sklearn.log_model(
        model,
        name="model",
        input_example=X_train.head(5),
        registered_model_name=model_name,
    )

# Point the "champion" alias at the new version.
version = info.registered_model_version
MlflowClient().set_registered_model_alias(model_name, "champion", version)
print(f"Registered {model_name} version {version} as champion")

# Write scored test rows to the inference table that the monitor watches.
predictions = pd.DataFrame(
    {
        "timestamp": datetime.now(timezone.utc),
        "model_version": str(version),
        "prediction": model.predict(X_test).astype(int),
        "label": y_test.astype(int).to_numpy(),
    }
)
spark = DatabricksSession.builder.getOrCreate()
spark.createDataFrame(predictions).write.mode("append").saveAsTable(inference_table)
print(f"Wrote predictions to {inference_table}")
