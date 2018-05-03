package extraction

import java.io.File
import java.nio.file.{Files, Paths}
import java.time.LocalDate

import akka.actor.ActorSystem
import akka.stream.scaladsl.{Sink, Source}
import akka.stream.{ActorMaterializer, ActorMaterializerSettings}
import utils.{Common, FileUtil}

import scala.collection.JavaConverters._
import scala.collection.immutable
import scala.concurrent.ExecutionContext.Implicits.global
import scala.concurrent.Future
import scala.xml.{Elem, XML}
import com.typesafe.config.ConfigFactory

/**
  * Extract court of appeal decisions.
  * Write their content to Brat format
  * (flat text + .ann empty file).
  * Max size of a line is a parameter.
  */
object LoadDecisionsToBratFiles extends App {

  lazy implicit val system: ActorSystem = ActorSystem()
  implicit val materializer: ActorMaterializer =
    ActorMaterializer(
      ActorMaterializerSettings(system)
        .withSupervisionStrategy(Common.printException)
    )

  val config = ConfigFactory.load

  private val extension         = "\\.[^.]*$".r
  private val destinationFolder = new File(config.getString("output_path"))

  FileUtil.deleteFileRecursively(destinationFolder)

  private val workers     = config.getInt("nb_worker")
  private val maxLineSize = config.getInt("max_line_size")
  private val minYear     = config.getInt("min_year")

  private val files: Iterator[File] =
    Files
      .find(Paths.get(config.getString("input_path")),
            999,
            (path, _) => path.toString.endsWith(".xml"))
      .iterator()
      .asScala
      .map(_.toFile)

  Source
    .fromIterator(() => files)
    .mapAsyncUnordered(workers) { file =>
      Future { AppealCourtContainer(file) }
    }
    .filter(_.date.getYear >= minYear) // for the annotation it was == 2016
    .grouped(10)
    .sliding(2)
    .map {
      case Seq(first, second) =>
        first ++ second.take(2)
    }
    .zipWithIndex
    .mapAsyncUnordered(workers) {
      case (decisions, index) =>
        val groupFolder =
          new File(destinationFolder, "lot_" + "%04d".format(index + 1) + "/")
        groupFolder.mkdir() // create new folders
        val futures = decisions.map { decision =>
          Future {
            val textToWrite = decision.getParagraphString(maxLineSize) +
              "\n\n\n" +
              "---------------------------------------------------\n\n" +
              "L'annotation de cette décision vous a semblé [NOTE]\n\n"

            val fileNameNoExtension =
              extension.replaceAllIn(decision.file.getName, "")
            val xmlPath =
              new File(groupFolder, fileNameNoExtension + ".txt")
            val annFilePath =
              new File(groupFolder, fileNameNoExtension + ".ann")
            // create empty ann file
            annFilePath.createNewFile()
            // write XML file
            FileUtil.writeText(xmlPath, textToWrite)
            // copy original XML file
            val destination =
              new File(groupFolder.getAbsolutePath, decision.file.getName)
            FileUtil.copy(decision.file.getAbsolutePath,
                          destination.getAbsolutePath)
          }
        }
        Future.sequence(futures)
    }
    .runWith(Sink.ignore)
    .onComplete(_ => system.terminate())
}

protected case class AppealCourtContainer(file: File) {
  val xml: Elem = XML.loadFile(file)

  val date: LocalDate = LocalDate.parse(
    (xml \ "META" \ "META_SPEC" \ "META_JURI" \ "DATE_DEC").text,
    Common.dateTimeFormatter)
  private lazy val paragraphs: immutable.Seq[String] =
    (xml \ "TEXTE" \ "BLOC_TEXTUEL" \ "CONTENU").map(_.text)

  def getParagraphString(maxLineSize: Int): String =
    paragraphs
      .filter(_.nonEmpty)
      .flatMap(_.split("\n").filter(_.nonEmpty).map(_.trim))
      .map(text => Common.splitLines(text, maxLineSize))
      .filter(_.nonEmpty)
      .mkString("\n\n")
}
