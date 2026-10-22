"""Train a small scikit-learn model and register it in Unity Catalog.

Each run creates a new model version and moves the alias to that version.
"""

import argparse

import mlflow
from mlflow import MlflowClient
from mlflow.models import infer_signature
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression

parser = argparse.ArgumentParser()
parser.add_argument("--model-full-name", required=True)
parser.add_argument("--alias", default="champion")
parser.add_argument("--experiment-name", required=True)
args = parser.parse_args()

mlflow.set_registry_uri("databricks-uc")
mlflow.set_experiment(args.experiment_name)

X, y = load_iris(return_X_y=True, as_frame=True)
model = LogisticRegression(max_iter=200).fit(X, y)

# Unity Catalog requires a model signature.
signature = infer_signature(X, model.predict(X))

with mlflow.start_run():
    model_info = mlflow.sklearn.log_model(
        sk_model=model,
        name="model",
        signature=signature,
        input_example=X.head(2),
        registered_model_name=args.model_full_name,
    )

version = model_info.registered_model_version
MlflowClient().set_registered_model_alias(args.model_full_name, args.alias, version)

print(f"Registered {args.model_full_name} version {version} with alias '{args.alias}'.")
print(f"Deploy this version with: --var model_version={version}")
