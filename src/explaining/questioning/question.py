# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.questioning.questions_templates_bank import QUESTIONS_TEMPLATES
from src.modeling.instance import Instance
from src.modeling.solution import Solution


# Global variables
QUESTION_TYPE_KEY = 'type'


# Class Question
class Question:

    def __init__(self, solution: Solution, question_template_id: str, fields_values: list[str]):
        self._solution = solution
        self._template = QUESTIONS_TEMPLATES[question_template_id]
        self._template.check_fields_values_validity(solution, fields_values, raise_error=True)
        self._fields_values = fields_values
        self._text = self._template.complete_text_with_fields_values(fields_values)

    def __repr__(self):
        return self._text

    @property
    def solution(self):
        return self._solution

    @property
    def template(self):
        return self._template

    @property
    def fields_values(self):
        return self._fields_values

    @property
    def text(self):
        return self._text

    def set_language(self, language_key: str):
        self.template.set_language(language_key)
        self._text = self._template.complete_text_with_fields_values(self.fields_values)

    @property
    def language(self):
        return self.template.language

    @language.setter
    def language(self, language_key: str):
        self.set_language(language_key)

    @property
    def language_is_english(self):
        return self.template.language_is_english

    @property
    def language_is_french(self):
        return self.template.language_is_french

    def to_dict(self):
        return {'solution': self.solution.to_dict(with_tasks_performances=False),
                'template id': self.template.id, 'fields values': self.fields_values}

    @classmethod
    def from_dict(cls, dictionary, solution: Solution):
        if dictionary[QUESTION_TYPE_KEY] == 'contrastive':
            return ContrastiveQuestion.from_dict(dictionary, solution)
        else:
            raise ValueError("The question must be of type contrastive")


# Class ContrastiveQuestion
class ContrastiveQuestion(Question):

    def __init__(self, solution: Solution, question_template_id: str, fields_values: list[str]):
        super().__init__(solution, question_template_id, fields_values)

    def to_dict(self):
        dictionary = super().to_dict()
        dictionary[QUESTION_TYPE_KEY] = 'contrastive'
        return dictionary

    @classmethod
    def from_dict(cls, dictionary, solution: Solution):
        return cls(solution, dictionary['template id'], dictionary['fields values'])


# Class ScenarioQuestion
class ScenarioQuestion(Question):

    def __init__(self, contrastive_question: ContrastiveQuestion, instance: Instance):
        super().__init__(contrastive_question.solution, contrastive_question.template.id,
                         contrastive_question.fields_values)
        self._contrastive_question = contrastive_question
        self._scenario_instance = instance

    @property
    def scenario_instance(self):
        return self._scenario_instance

    @property
    def text(self):
        if self._contrastive_question.language_is_english:
            return "What if the instance is changed? " + self._contrastive_question.text
        elif self._contrastive_question.language_is_french:
            return "Et si l'instance est modifiée ? " + self._contrastive_question.text
        else:
            raise NotImplementedError(f"Language {self.language} not supported")

    def set_language(self, language_key):
        self._contrastive_question.set_language(language_key)


# Class CounterfactualQuestion
class CounterfactualQuestion(Question):

    def __init__(self, contrastive_question: ContrastiveQuestion, instance_slacks: InstanceChanges = None):
        super().__init__(contrastive_question.solution, contrastive_question.template.id,
                         contrastive_question.fields_values)
        self._contrastive_question = contrastive_question
        self._instance_slacks = instance_slacks

    @property
    def instance_slacks(self):
        return self._instance_slacks

    @property
    def text(self):
        if self._contrastive_question.language_is_english:
            return "How to change the instance to make it possible? " + self._contrastive_question.text
        elif self._contrastive_question.language_is_french:
            return "Comment modifier l'instance pour que cela soit possible ? " + self._contrastive_question.text
        else:
            raise NotImplementedError(f"Language {self.language} not supported")

    def set_language(self, language_key):
        self._contrastive_question.set_language(language_key)
