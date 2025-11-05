/*
This project is a simple example of how to use the Databricks Connect Scala client to run on
serverless or on a Databricks cluster.
 */
package com.examples

import com.databricks.connect.DatabricksSession
import org.apache.spark.sql.{SparkSession, functions => F}
import org.apache.spark.sql.functions.udf

object Main {
  def main(args: Array[String]): Unit = {
    println("Hello, World!")

    val catalog = getFromArgs(args, "catalog").getOrElse("samples")
    val schema = getFromArgs(args, "schema").getOrElse("nyctaxi")

    println(s"Using catalog: $catalog, schema: $schema")

    val spark = getSession()
    println("Showing range ...")
    spark.range(3).show()

    println("Showing nyctaxi trips ...")
    val nycTaxi = new NycTaxi(spark, catalog, schema)
    val df = nycTaxi.trips()
    df.show()
  }

  private def getFromArgs(args: Array[String], key: String): Option[String] = {
    args.sliding(2, 2).collectFirst {
      case Array(k, v) if k == s"--$key" => v
    }
  }

  def getSession(): SparkSession = {
    // Get DATABRICKS_RUNTIME_VERSION environment variable
    if (sys.env.contains("DATABRICKS_RUNTIME_VERSION")) {
      println("Running in a Databricks cluster")
      SparkSession.active
    } else {
      println("Running outside Databricks")
      DatabricksSession.builder()
        .serverless()
        .validateSession(false)
        .addCompiledArtifacts(Main.getClass.getProtectionDomain.getCodeSource.getLocation.toURI)
        .getOrCreate()
    }
  }
}
