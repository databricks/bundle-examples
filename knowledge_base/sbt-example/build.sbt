name := "sbt-example"

version := "0.1.0-SNAPSHOT"

scalaVersion := "2.12.19"

libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-core" % "3.5.0",
  "org.apache.spark" %% "spark-sql" % "3.5.0"
)
