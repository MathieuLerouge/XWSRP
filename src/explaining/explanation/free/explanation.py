# Standard library
from typing import Any, Optional

# Local libraries
from src.explaining.computing.neighborhood.facts import ConflictFacts, ExplanationFacts
from src.explaining.explanation.explanation import Explanation
from src.explaining.question.free.question import FreeTextQuestion
from src.explaining.question.question import Question
from src.modeling.solution import Solution

# Keys of the dictionary a free-text explanation is serialized to.
QUESTION_KEY = 'question'
SUPPORT_SOLUTION_KEY = 'support solution'
FACTS_KEY = 'facts'
TEXT_KEY = 'text'
LLM_MODEL_KEY = 'llm model'
COMPUTATION_MODE_KEY = 'computation_mode'
COMPUTATION_TIME_KEY = 'computation_time'


#######################
# FreeTextExplanation #
#######################

class FreeTextExplanation(Explanation):
    """
    An answer to a question, worded by an LLM from the ExplanationFacts of the solved neighborhood.

    Only its text comes from the LLM: whether it is positive, and whether its support solution is feasible,
    are read off the facts, which were computed deterministically.
    """

    def __init__(
            self, question: Question, support_solution: Solution, facts: ExplanationFacts, text: str,
            llm_model: Optional[str] = None,
            computation_mode: Optional[str] = None, computation_time: Optional[float] = None
    ):
        """
        Args:
            question: The question being answered.
            support_solution: The solution found while answering it, backing the explanation.
            facts: The facts the explanation was worded from.
            text: The explanation as worded from the facts.
            llm_model: The instructor model string ("provider/model-name") the text was worded with,
                or None if not available.
            computation_mode: The mode in which the explanation is computed, or None if not available.
            computation_time: The computation time in seconds, or None if not available.
        """
        self._facts = facts
        self._written_text = text
        self._llm_model = llm_model
        super().__init__(question, support_solution, computation_mode=computation_mode,
                         computation_time=computation_time)

    @property
    def facts(self) -> ExplanationFacts:
        """The facts the explanation was worded from."""
        return self._facts

    @property
    def conflict(self) -> Optional[ConflictFacts]:
        """Why the support solution is infeasible, or None when it is feasible."""
        return self._facts.conflict

    @property
    def llm_model(self) -> Optional[str]:
        """The instructor model string the text was worded with, if available."""
        return self._llm_model

    @property
    def support_solution_is_feasible(self) -> bool:
        """Whether the support solution is a feasible one."""
        return self._facts.support_solution_is_feasible

    def is_positive(self) -> bool:
        """Whether the explanation confirms what the question asked about is possible and worthwhile."""
        return self._facts.is_positive

    def is_negative(self) -> bool:
        """Whether the explanation reports what the question asked about as impossible or not worthwhile."""
        return not self._facts.is_positive

    def _compute_text(self, with_bold_emphasis: bool = False) -> str:
        """
        Returns the text as worded by the LLM.

        Args:
            with_bold_emphasis: Ignored: the text is plain, emphasis being left for a future improvement.
        """
        return self._written_text

    def to_dict(self) -> dict[str, Any]:
        """Return this explanation as a dictionary, as read back by from_dict."""
        return {
            QUESTION_KEY: self.question.to_dict(),
            SUPPORT_SOLUTION_KEY: self.support_solution.to_dict(with_sequences=True),
            FACTS_KEY: self._facts.to_dict(),
            TEXT_KEY: self._written_text,
            LLM_MODEL_KEY: self._llm_model,
            COMPUTATION_MODE_KEY: self.mode,
            COMPUTATION_TIME_KEY: self.computation_time,
        }

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any], solution: Solution) -> "FreeTextExplanation":
        """
        Rebuilds the explanation a previously exported dictionary describes, without calling any LLM.

        Args:
            dictionary: The dictionary to rebuild the explanation from, as produced by to_dict.
            solution: The solution the question was asked about.

        Returns:
            The rebuilt explanation.
        """
        return cls(
            FreeTextQuestion.from_dict(dictionary[QUESTION_KEY], solution),
            Solution.from_dict(dictionary[SUPPORT_SOLUTION_KEY], solution.instance),
            ExplanationFacts.from_dict(dictionary[FACTS_KEY]),
            dictionary[TEXT_KEY],
            dictionary.get(LLM_MODEL_KEY),
            dictionary.get(COMPUTATION_MODE_KEY),
            dictionary.get(COMPUTATION_TIME_KEY),
        )
