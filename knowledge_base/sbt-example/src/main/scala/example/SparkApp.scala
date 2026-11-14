import org.apache.spark.sql.SparkSession

object SparkApp {
  def main(args: Array[String]): Unit = {
    val spark = SparkSession.builder().getOrCreate()

    import spark.implicits._

    val data = Seq("Hello", "World").toDF("word")
    data.show()
  }
}
