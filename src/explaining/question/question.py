# Standard library
from abc import ABC, abstractmethod

# Local libraries
from src.modeling.solution import Solution
from src.utils.language import check_if_language_is_english, check_if_language_is_french


############
# Question #
############

class Question(ABC):
    """
    Any question an end user may ask about a solution, whatever the pipeline answering it.

    It carries only what every kind of question has: the solution it is asked about,
    the text it reads as, and the language that text is phrased in.
    """

    def __init__(self, solution: Solution):
        """
        Args:
            solution: The solution the question is asked about.
        """
        self._solution = solution

    def __repr__(self):
        return self.text

    @property
    def solution(self) -> Solution:
        """The solution the question is asked about."""
        return self._solution

    @property
    @abstractmethod
    def text(self) -> str:
        """The question as the end user reads it, in the language it is currently phrased in."""

    @property
    @abstractmethod
    def language(self) -> str:
        """Key of the language the question is currently phrased in."""

    @abstractmethod
    def set_language(self, language_key: str):
        """
        Rephrases the question in the given language.

        Args:
            language_key: Key of the language to phrase the question in.
        """

    @language.setter
    def language(self, language_key: str):
        self.set_language(language_key)

    @property
    def language_is_english(self) -> bool:
        """Whether the question is currently phrased in English."""
        return check_if_language_is_english(self.language)

    @property
    def language_is_french(self) -> bool:
        """Whether the question is currently phrased in French."""
        return check_if_language_is_french(self.language)
