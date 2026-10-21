# Prints the identity that runs this task.
# In dev this is the user who deployed the bundle; in prod it is the run_as service principal.
from databricks.sdk import WorkspaceClient
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
sql_user = spark.sql("SELECT current_user() AS user").first()["user"]

me = WorkspaceClient().current_user.me()

print(f"current_user():        {sql_user}")
print(f"SDK user_name:         {me.user_name}")
print(f"SDK display_name:      {me.display_name}")
