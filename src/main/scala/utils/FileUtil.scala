package utils

import java.io._
import java.nio.file.{Files, Paths, StandardCopyOption}

import scala.annotation.tailrec
import scala.io.Source

object FileUtil {

  /**
    * Delete any file in the provided directory
    */
  def deleteFileRecursively(file: File): Boolean = {

    if (file.exists())
      require(
        file.isDirectory,
        s"The directory to make empty is a file [${file.getAbsolutePath}]")

    def getFiles(file: File): List[File] =
      Option(file.listFiles()).getOrElse(Array.empty).toList

    @tailrec
    def loop(files: List[File]): Boolean = files match {
      case (Nil) ⇒ true

      case (head :: tail) if head.isDirectory && head.listFiles().nonEmpty ⇒
        loop(getFiles(head) ++ tail ++ List(head))

      case (head :: tail) ⇒
        head.delete()
        loop(tail)
    }
    if (!file.exists()) false else loop(getFiles(file))
  }

  private def deleteFile(file: File) =
    if (file.exists()) {
      println(s"Delete ${file.getAbsolutePath}")
      file.delete()
    }

  def deleteFiles(files: File*): Unit = files.foreach(deleteFile)

  def deleteFilesFromPath(paths: String*): Unit =
    paths.toArray.map(new File(_)).foreach(deleteFile)

  /**
    * Merge several text files in one.
    *
    * @param inputFiles files to merge
    * @param outFile    final file. Deleted if exists
    */
  def concatenateFile(inputFiles: Seq[File], outFile: File): Unit = {
    if (outFile.exists()) outFile.delete()
    val bw = new BufferedWriter(new FileWriter(outFile))
    inputFiles
      .find(!_.exists())
      .foreach(file =>
        throw new IOException(file.getAbsoluteFile + " doesn't exist."))
    for (file <- inputFiles) {
      val source = Source.fromFile(file).getLines()
      source.foreach { line =>
        bw.write(line + System.lineSeparator)
      }
    }
    bw.close()
  }

  /**
    * Write a String to a file
    */
  def writeText(path: String, content: String): Unit = {
    val file = new File(path)
    if (file.exists()) file.delete()
    file.createNewFile()
    val bw = new BufferedWriter(new FileWriter(file))
    bw.write(content)
    bw.close()
  }

  /**
    * Write a String to a file
    */
  def writeText(path: File, content: String): Unit =
    writeText(path.getAbsolutePath, content)

  /**
    * Copy a file to a destination
    * Overwrite file
    */
  def copy(source: String, destination: String): Unit = {
    val sourcePath = Paths.get(source)
    require(Files.exists(sourcePath), "File to copy doesn't exist!")
    val destinationPath = Paths.get(destination)
    Files.copy(sourcePath,
               destinationPath,
               StandardCopyOption.REPLACE_EXISTING)
  }
}
