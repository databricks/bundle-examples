# Databricks notebook source
config = {
    "batch_size": 0,
    "checkpoint_path": "",
    "mode": "incremental",
}

errors = []
if config["batch_size"] <= 0:
    errors.append("batch_size must be greater than zero")
if config["mode"] == "incremental" and not config["checkpoint_path"]:
    errors.append("checkpoint_path is required in incremental mode")

if errors:
    raise ValueError(f"Invalid job configuration: {'; '.join(errors)}")
