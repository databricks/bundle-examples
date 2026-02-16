# Databricks notebook source
from databricks.sdk.runtime import dbutils

val = dbutils.jobs.taskValues.get(taskKey="producer", key="answer", debugValue=None)
print(f"Got value: {val}")