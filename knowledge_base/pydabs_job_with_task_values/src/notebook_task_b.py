# Databricks notebook source
val = dbutils.jobs.taskValues.get(taskKey="task_a", key="my_key")
print(val)
