# Databricks notebook source
from databricks.sdk.runtime import dbutils

items = [1, 2, 3]
dbutils.jobs.taskValues.set(key="items", value=items)
