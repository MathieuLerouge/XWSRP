# Local libraries
from explaining.explorationpart.instance_changes import InstanceChanges
from explaining.questionpart.questions_templates_bank import QUESTIONS_TEMPLATES
from model.instance import Instance
from model.solution import Solution


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

    # @solution.setter
    # def solution(self, solution: Solution):
    #     self._template.check_fields_values_validity(solution, self._fields_values, raise_error=True)
    #     self._solution = solution

    @property
    def template(self):
        return self._template

    @property
    def fields_values(self):
        return self._fields_values

    # @fields_values.setter
    # def fields_values(self, fields_values: list[str]):
    #     self._template.check_fields_values_validity(self._solution, fields_values, raise_error=True)
    #     self._fields_values = fields_values

    @property
    def text(self):
        return self._text


# Class ContrastiveQuestion
class ContrastiveQuestion(Question):

    def __init__(self, solution: Solution, question_template_id: str, fields_values: list[str]):
        super().__init__(solution, question_template_id, fields_values)


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
        return "What if the instance is changed? " + self._contrastive_question.text


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
        return "How to change the instance to make it possible? " + self._contrastive_question.text
