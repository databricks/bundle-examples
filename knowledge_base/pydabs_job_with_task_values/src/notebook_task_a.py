# Databricks notebook source
val = [42, 12, 1812]
dbutils.jobs.taskValues.set(key="my_key", value=val)
