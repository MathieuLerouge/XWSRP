# Standard libraries
from abc import ABC, abstractmethod
from typing import Optional

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.question.question import Question
from src.modeling.solution import Solution
from src.utils.constants import LINE_BREAK_STRING
from src.utils.language import check_if_language_is_english, check_if_language_is_french
from src.utils.time import get_hour_format_associated_with_language


###############
# Explanation #
###############

class Explanation(ABC):
    """
    An answer to a question about a solution, phrased for the end user.

    It carries what every explanation has whichever pipeline produced it:
    the question answered, the support solution found while answering it,
    the instance alterations that support solution needed, and the resulting text.
    How that text is worded is left to the subclasses,
    since it is what the tailored and free-text branches disagree on.
    """

    def __init__(self, question: Question, support_solution: Solution,
                 instance_alterations: Optional[InstanceChanges] = None):
        """
        Args:
            question: The question being answered.
            support_solution: The solution found while answering it, backing the explanation.
            instance_alterations: The instance parameter changes the support solution needed to become feasible,
                or None when the question called for no alteration.
        """
        self._question = question
        self._support_solution = support_solution
        self._instance_alterations = instance_alterations
        self._text = self._compute_text()

    ############
    # Language #
    ############

    @property
    def language(self) -> str:
        """Key of the language the explanation is phrased in, which is the one its question is phrased in."""
        return self._question.language

    @property
    def language_is_english(self) -> bool:
        """Whether the explanation is phrased in English."""
        return check_if_language_is_english(self.language)

    @property
    def language_is_french(self) -> bool:
        """Whether the explanation is phrased in French."""
        return check_if_language_is_french(self.language)

    @property
    def _hour_format(self) -> str:
        """The format times are spelled in, in the explanation's language."""
        return get_hour_format_associated_with_language(self.language)

    #########################
    # Question and solutions #
    #########################

    @property
    def question(self) -> Question:
        """The question being answered."""
        return self._question

    @property
    def current_solution(self) -> Solution:
        """The solution the question was asked about."""
        return self._question.solution

    @property
    def support_solution(self) -> Solution:
        """The solution found while answering the question, backing the explanation."""
        return self._support_solution

    @property
    def new_solution(self) -> Solution:
        """The solution found while answering the question, backing the explanation."""
        return self.support_solution

    @property
    @abstractmethod
    def support_solution_is_feasible(self) -> bool:
        """Whether the support solution is a feasible one."""

    @abstractmethod
    def is_positive(self):
        """Whether the explanation confirms what the question asked about is possible."""

    @abstractmethod
    def is_negative(self):
        """Whether the explanation reports what the question asked about as impossible or not worthwhile."""

    ########
    # Text #
    ########

    @property
    def text(self) -> str:
        """The explanation as the end user reads it."""
        return self._text

    @abstractmethod
    def _compute_text(self, with_bold_emphasis: bool = False):
        """
        Words the explanation, in the language its question is phrased in.

        Args:
            with_bold_emphasis: Whether to wrap the emphasized parts in bold markup.
        """

    @property
    def _activity(self) -> str:
        """
        How to call a single step of a route, in the explanation's language.

        An instance with employee unavailabilities holds more than tasks, so the wider word is used there.

        Raises:
            NotImplementedError: if the explanation is phrased in a language this word has no wording for.
        """
        if self.language_is_english:
            if self.support_solution.instance.has_employee_unavailabilities:
                return "activity"
            else:
                return "task"
        elif self.language_is_french:
            if self.support_solution.instance.has_employee_unavailabilities:
                return "activité"
            else:
                return "tâche"
        else:
            raise NotImplementedError("Non-supported language")

    @property
    def _activities(self) -> str:
        """
        How to call several steps of a route, in the explanation's language.

        Raises:
            NotImplementedError: if the explanation is phrased in a language this word has no wording for.
        """
        if self.language_is_english:
            if self.support_solution.instance.has_employee_unavailabilities:
                return "activities"
            else:
                return "tasks"
        elif self.language_is_french:
            if self.support_solution.instance.has_employee_unavailabilities:
                return "activités"
            else:
                return "tâches"
        else:
            raise NotImplementedError("Non-supported language")

    @property
    def _assume_the_current_is_altered(self) -> str:
        """
        The clause introducing the instance alterations the support solution needed,
        in the explanation's language.
        """
        if self.language_is_english:
            return f"assume that the following change" \
                   f"{'s are ' if self._instance_alterations.nb_changes > 1 else ' is '}" \
                   f"applied to the current instance: " \
                   f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}" \
                   f"{self._instance_alterations.as_string(language=self.language)}" \
                   f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"
        elif self.language_is_french:
            return f"supposons que " \
                   f"{'les changements' if self._instance_alterations.nb_changes > 1 else 'le changement'} " \
                   f"suivant{'s' if self._instance_alterations.nb_changes > 1 else ''} " \
                   f"soi{'en' if self._instance_alterations.nb_changes > 1 else ''}t " \
                   f"appliqué{'s' if self._instance_alterations.nb_changes > 1 else ''} à l'instance : " \
                   f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}" \
                   f"{self._instance_alterations.as_string(language=self.language)}" \
                   f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"

    @property
    def _Assume_the_current_is_altered(self) -> str:
        """The same clause, capitalized to open a sentence."""
        if self.language_is_english:
            return "A" + self._assume_the_current_is_altered[1:]
        elif self.language_is_french:
            return "S" + self._assume_the_current_is_altered[1:]

    def _compare_total_working_duration(self, start_with_cap: bool = False, without_new_solution: bool = False):
        """
        Words how the support solution's total working duration compares with the current solution's.

        Args:
            start_with_cap: Whether the sentence opens a new one, and so starts with a capital letter.
            without_new_solution: Whether to refer to the support solution as "it" rather than by name.

        Returns:
            The comparison sentence, in the explanation's language.

        Raises:
            AttributeError: if the support solution is infeasible, leaving nothing to compare.
        """
        if not self.support_solution_is_feasible:
            raise AttributeError("Current and new solutions cannot be compared as new solution is infeasible.")
        current_solution = self._question.solution
        new_solution = self.support_solution
        text = ""
        if self.language_is_english:
            if without_new_solution:
                text += f"{'Its' if start_with_cap else 'its'} total working duration "
            else:
                text += f"{'The' if start_with_cap else 'the'} total working duration of the new solution "
            text += f" is {new_solution.total_working_duration}min, which is "
            if new_solution.total_working_duration < current_solution.total_working_duration:
                text += "shorter than "
            elif new_solution.total_working_duration > current_solution.total_working_duration:
                text += "longer than "
            else:
                text += "equal to "
            text += f"the one of the current solution {current_solution.total_working_duration}min"
        elif self.language_is_french:
            if without_new_solution:
                text += f"{'Sa' if start_with_cap else 'sa'} durée totale de travail "
            else:
                text += f"{'La' if start_with_cap else 'la'} durée totale de travail de la nouvelle solution "
            text += f" est de {new_solution.total_working_duration}min, soit une durée "
            if new_solution.total_working_duration < current_solution.total_working_duration:
                text += "inférieure "
            elif new_solution.total_working_duration > current_solution.total_working_duration:
                text += "supérieure "
            else:
                text += "égale "
            text += f"à celle de la solution courante qui est de {current_solution.total_working_duration}min"
        return text

    def _compare_total_traveling_duration(self, start_with_cap: bool = False, without_new_solution: bool = False):
        """
        Words how the support solution's total traveling duration compares with the current solution's.

        Args:
            start_with_cap: Whether the sentence opens a new one, and so starts with a capital letter.
            without_new_solution: Whether to refer to the support solution as "it" rather than by name.

        Returns:
            The comparison sentence, in the explanation's language.

        Raises:
            AttributeError: if the support solution is infeasible, leaving nothing to compare.
        """
        if not self.support_solution_is_feasible:
            raise AttributeError("Current and new solutions cannot be compared as new solution is infeasible.")
        current_solution = self._question.solution
        new_solution = self.support_solution
        text = ""
        if self.language_is_english:
            if without_new_solution:
                text += f"{'Its' if start_with_cap else 'its'} total traveling duration "
            else:
                text += f"{'The' if start_with_cap else 'the'} total traveling duration of the new solution "
            text += f"is {new_solution.total_traveling_duration}min, which is "
            if new_solution.total_traveling_duration < current_solution.total_traveling_duration:
                text += "shorter than "
            elif new_solution.total_traveling_duration > current_solution.total_traveling_duration:
                text += "longer than "
            else:
                text += "equal to "
            text += f"the one of the current solution {current_solution.total_traveling_duration}min"
        elif self.language_is_french:
            if without_new_solution:
                text += f"{'Sa' if start_with_cap else 'sa'} durée totale de déplacement "
            else:
                text += f"{'La' if start_with_cap else 'la'} durée totale de déplacement de la nouvelle solution "
            text += f" est de {new_solution.total_traveling_duration}min, soit une durée "
            if new_solution.total_traveling_duration < current_solution.total_traveling_duration:
                text += "inférieure "
            elif new_solution.total_traveling_duration > current_solution.total_traveling_duration:
                text += "supérieure "
            else:
                text += "égale "
            text += f"à celle de la solution courante qui est de {current_solution.total_traveling_duration}min"
        return text

    @abstractmethod
    def to_dict(self):
        """
        Returns the dictionary describing the explanation, for serialization.
        """
