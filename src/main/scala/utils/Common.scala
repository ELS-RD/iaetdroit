package utils

import java.time.format.DateTimeFormatter

import akka.stream.Supervision


object Common {
  // Strategy to print Exception in Akka
  lazy val printException: Supervision.Decider = {
    case e: Exception =>
      e.printStackTrace()
      Supervision.Stop // stop if Exception is raised
  }

  val dateTimeFormatter: DateTimeFormatter =
    DateTimeFormatter.ofPattern("yyyy-MM-dd")

  /**
    * Divides a String in substrings of `maxLength`.
    * Avoids cutting in the middle of a word
    * @param s original string
    * @param maxLength maximum size of each line (<=)
    */
  def wordWrap(s: String, maxLength: Int): Array[String] =
    s.split(" ")
      .foldLeft(Array(""))((out, word) => {
        if ((out.last + " " + word).length > maxLength)
          out :+ word
        else out.updated(out.length - 1, out.last + " " + word)
      })
}
