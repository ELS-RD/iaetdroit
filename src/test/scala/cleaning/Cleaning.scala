package cleaning

import org.scalatest.{FlatSpec, Matchers}
import utils.Common


class Cleaning extends FlatSpec with Matchers{

  "Text" should "be divided in several parts of a specific length" in {
    val originalText = "This is a long line of text, where should I cut?"

    val result = Common.wordWrap(originalText, 12)
    (result should have).length(5)
    result.forall(_.length <= 12) shouldBe true
  }
}

//testOnly *Cleaning