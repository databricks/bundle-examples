from pyspark import pipelines as dp
from pyspark.sql.functions import count, round as round_, sum as sum_


# Wanderbricks revenue by destination (gold): bookings x properties x destinations.
@dp.table
def revenue_by_destination():
    bookings = spark.read.table("bookings")
    properties = spark.read.table("samples.wanderbricks.properties")
    destinations = spark.read.table("samples.wanderbricks.destinations")
    return (
        bookings.join(properties, "property_id")
        .join(destinations, "destination_id")
        .groupBy("destination", "country")
        .agg(
            count("*").alias("number_of_bookings"),
            round_(sum_("total_amount"), 2).alias("total_revenue"),
        )
    )
