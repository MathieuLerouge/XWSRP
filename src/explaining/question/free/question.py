# Local libraries
from src.explaining.question.question import Question, QuestioningModes
from src.modeling.solution import Solution
from src.utils.language import LANGUAGE_ENGLISH_KEY


####################
# FreeTextQuestion #
####################

class FreeTextQuestion(Question):
    """
    A question the end user phrased themselves, in their own words, rather than picking it from the catalogue.

    It holds no template: its text is what the end user typed, and nothing rewrites it.
    Setting its language therefore only records which language that text is in - it does not translate it -
    so that the explanation answering it can be phrased in the same language.
    """

    def __init__(self, solution: Solution, text: str, language_key: str = LANGUAGE_ENGLISH_KEY):
        """
        Args:
            solution: The solution the question is asked about.
            text: The question as the end user typed it.
            language_key: Key of the language the end user typed it in.
        """
        super().__init__(solution, QuestioningModes.FREE_TEXT.value)
        self._text = text
        self._language_key = language_key

    @property
    def text(self) -> str:
        """The question as the end user typed it."""
        return self._text

    @property
    def language(self) -> str:
        """Key of the language the question is phrased in."""
        return self._language_key

    def set_language(self, language_key: str):
        """
        Records which language the question's text is in.

        Args:
            language_key: Key of the language the question is phrased in.
        """
        self._language_key = language_key

    @language.setter
    def language(self, language_key: str):
        self.set_language(language_key)
