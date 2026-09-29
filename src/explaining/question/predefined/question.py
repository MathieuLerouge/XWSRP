# Standard library
from typing import Optional

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.question.predefined.bank import QUESTIONS_TEMPLATES
from src.explaining.question.question import Question
from src.modeling.instance import Instance
from src.modeling.solution import Solution


# Global variables
QUESTION_TYPE_KEY = 'type'


######################
# PredefinedQuestion #
######################

class PredefinedQuestion(Question):
    """
    A question picked from the predefined catalogue, i.e. a QuestionTemplate with its fields filled in.

    Its text is the template's sentence completed with the given field values,
    which is also what ties it to the transformation answering it and to the explanation phrasing that answer:
    both are looked up by template id.
    """

    def __init__(self, solution: Solution, question_template_id: str, fields_values: list[str]):
        """
        Args:
            solution: The solution the question is asked about.
            question_template_id: Id of the template in QUESTIONS_TEMPLATES the question instantiates.
            fields_values: Value of each of the template's fields, in the order the template declares them.
        """
        super().__init__(solution)
        self._template = QUESTIONS_TEMPLATES[question_template_id]
        self._template.check_fields_values_validity(solution, fields_values, raise_error=True)
        self._fields_values: list[str] = fields_values
        self._text = self._template.complete_text_with_fields_values(fields_values)

    @property
    def template(self):
        """The template the question instantiates."""
        return self._template

    @property
    def fields_values(self) -> list[str]:
        """Value of each of the template's fields, in the order the template declares them."""
        return self._fields_values

    @property
    def text(self) -> str:
        """The question as the end user reads it, in the language it is currently phrased in."""
        return self._text

    @property
    def language(self) -> str:
        """Key of the language the question is currently phrased in."""
        return self.template.language

    def set_language(self, language_key: str):
        """
        Rephrases the question in the given language.

        Args:
            language_key: Key of the language to phrase the question in.
        """
        self.template.set_language(language_key)
        self._text = self._template.complete_text_with_fields_values(self.fields_values)

    @language.setter
    def language(self, language_key: str):
        self.set_language(language_key)

    def to_dict(self):
        return {'solution': self.solution.to_dict(with_tasks_performances=False),
                'template id': self.template.id, 'fields values': self.fields_values}

    @classmethod
    def from_dict(cls, dictionary, solution: Solution):
        """
        Rebuilds the question a previously exported dictionary describes.

        Args:
            dictionary: The dictionary to rebuild the question from.
            solution: The solution the question was asked about.

        Returns:
            The rebuilt question.

        Raises:
            ValueError: if the dictionary describes anything but a contrastive question.
        """
        if dictionary[QUESTION_TYPE_KEY] == 'contrastive':
            return ContrastiveQuestion.from_dict(dictionary, solution)
        else:
            raise ValueError("The question must be of type contrastive")


#######################
# ContrastiveQuestion #
#######################

class ContrastiveQuestion(PredefinedQuestion):
    """
    A "why not" question, contrasting the solution at hand with the one the end user expected instead.
    """

    def __init__(self, solution: Solution, question_template_id: str, fields_values: list[str]):
        """
        Args:
            solution: The solution the question is asked about.
            question_template_id: Id of the template in QUESTIONS_TEMPLATES the question instantiates.
            fields_values: Value of each of the template's fields, in the order the template declares them.
        """
        super().__init__(solution, question_template_id, fields_values)

    def to_dict(self):
        dictionary = super().to_dict()
        dictionary[QUESTION_TYPE_KEY] = 'contrastive'
        return dictionary

    @classmethod
    def from_dict(cls, dictionary, solution: Solution):
        """
        Rebuilds the question a previously exported dictionary describes.

        Args:
            dictionary: The dictionary to rebuild the question from.
            solution: The solution the question was asked about.

        Returns:
            The rebuilt question.
        """
        return cls(solution, dictionary['template id'], dictionary['fields values'])


####################
# ScenarioQuestion #
####################

class ScenarioQuestion(PredefinedQuestion):
    """
    A contrastive question asked about an instance the end user altered, to see what the change would allow.
    """

    def __init__(self, contrastive_question: ContrastiveQuestion, instance: Instance):
        """
        Args:
            contrastive_question: The contrastive question being asked.
            instance: The altered instance to ask it about.
        """
        super().__init__(contrastive_question.solution, contrastive_question.template.id,
                         contrastive_question.fields_values)
        self._contrastive_question = contrastive_question
        self._scenario_instance = instance

    @property
    def scenario_instance(self) -> Instance:
        """The altered instance the contrastive question is asked about."""
        return self._scenario_instance

    @property
    def text(self) -> str:
        """
        The question as the end user reads it, in the language it is currently phrased in.

        Raises:
            NotImplementedError: if the question is phrased in a language this prefix has no wording for.
        """
        if self._contrastive_question.language_is_english:
            return "What if the instance is changed? " + self._contrastive_question.text
        elif self._contrastive_question.language_is_french:
            return "Et si l'instance est modifiée ? " + self._contrastive_question.text
        else:
            raise NotImplementedError(f"Language {self.language} not supported")

    def set_language(self, language_key: str):
        """
        Rephrases the question in the given language.

        Args:
            language_key: Key of the language to phrase the question in.
        """
        self._contrastive_question.set_language(language_key)


##########################
# CounterfactualQuestion #
##########################

class CounterfactualQuestion(PredefinedQuestion):
    """
    A contrastive question turned around: rather than why the expected solution was not picked,
    it asks which instance alterations would make it possible.
    """

    def __init__(self, contrastive_question: ContrastiveQuestion,
                 instance_parameter_alteration_bounds: Optional[InstanceChanges] = None):
        """
        Args:
            contrastive_question: The contrastive question being turned around.
            instance_parameter_alteration_bounds: How far each instance parameter may be altered,
                or None to leave the search unbounded.
        """
        super().__init__(contrastive_question.solution, contrastive_question.template.id,
                         contrastive_question.fields_values)
        self._contrastive_question = contrastive_question
        self._instance_parameter_alteration_bounds = instance_parameter_alteration_bounds

    @property
    def instance_parameter_alteration_bounds(self) -> Optional[InstanceChanges]:
        """How far each instance parameter may be altered, or None when the search is unbounded."""
        return self._instance_parameter_alteration_bounds

    @property
    def text(self) -> str:
        """
        The question as the end user reads it, in the language it is currently phrased in.

        Raises:
            NotImplementedError: if the question is phrased in a language this prefix has no wording for.
        """
        if self._contrastive_question.language_is_english:
            return "How to change the instance to make it possible? " + self._contrastive_question.text
        elif self._contrastive_question.language_is_french:
            return "Comment modifier l'instance pour que cela soit possible ? " + self._contrastive_question.text
        else:
            raise NotImplementedError(f"Language {self.language} not supported")

    def set_language(self, language_key: str):
        """
        Rephrases the question in the given language.

        Args:
            language_key: Key of the language to phrase the question in.
        """
        self._contrastive_question.set_language(language_key)
