# Databricks notebook source
# MAGIC %pip install faker

# COMMAND ----------

# Get input parameters from job
dbutils.widgets.get("bronze_catalog")
dbutils.widgets.get("bronze_schema")
dbutils.widgets.get("bronze_volume")

volume_folder = f"/Volumes/{bronze_catalog}/{bronze_schema}/{bronze_volume}"

# COMMAND ----------

from pyspark.sql import functions as F
from faker import Faker
from collections import OrderedDict
import uuid
fake = Faker()
import random

fake_firstname = F.udf(fake.first_name)
fake_lastname = F.udf(fake.last_name)
fake_email = F.udf(fake.ascii_company_email)
fake_date = F.udf(lambda:fake.date_time_this_month().strftime("%m-%d-%Y %H:%M:%S"))
fake_address = F.udf(fake.address)
operations = OrderedDict([("APPEND", 0.5),("DELETE", 0.1),("UPDATE", 0.3),(None, 0.01)])
fake_operation = F.udf(lambda:fake.random_elements(elements=operations, length=1)[0])
fake_id = F.udf(lambda: str(uuid.uuid4()) if random.uniform(0, 1) < 0.98 else None)

df = spark.range(0, 100000).repartition(100)
df = df.withColumn("id", fake_id())
df = df.withColumn("firstname", fake_firstname())
df = df.withColumn("lastname", fake_lastname())
df = df.withColumn("email", fake_email())
df = df.withColumn("address", fake_address())
df = df.withColumn("operation", fake_operation())
df_customers = df.withColumn("operation_date", fake_date())
df_customers.repartition(100).write.format("json").mode("overwrite").save(volume_folder+"/customers")
