# Local libraries
from src.explaining.answering.explanation import *
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.modeling.instance import EditableInstance
from src.explaining.modeling.solution import EditableSolution
from src.explaining.interacting.history import History
from src.explaining.questioning.question import ContrastiveQuestion, CounterfactualQuestion
from src.explaining.questioning.questions_templates_bank import *
from src.explaining.reading.explanation import import_explanation_from_json_file, check_explanation_json_file_existence
from src.explaining.transforming.transformation import apply_induced_transformation, apply_induced_transformation_bis
from src.explaining.writing.explanation import define_explanation_json_file_name, export_explanation_to_json_file
from src.modeling.instance import Instance
from src.modeling.solution import Solution
from src.utils.constants import OUTPUTS_DIRECTORY_RELATIVE_PATH


# Class Explainer
class Explainer:
    _selected_questions_templates_ids = [
        WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
        WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3
    ]

    def __init__(self, solution: Solution):
        self._questions_templates = dict([(id, QUESTIONS_TEMPLATES[id]) for id in QUESTIONS_TEMPLATES.keys()
                                          if id in self._selected_questions_templates_ids])
        self._root_solution = EditableSolution.from_Solution(solution)
        solution = self._root_solution.copy(solution.name + ".1.1")
        solution.instance = self._root_solution.instance.copy(name=solution.instance.name + ".1")
        self._history = History(solution)
        self._current_solution = solution
        self._contrastive_explanations_directory = OUTPUTS_DIRECTORY_RELATIVE_PATH
        self._export_contrastive_explanations = False
        self._use_already_computed_contrastive_explanations = False
        self._last_contrastive_explanation = None
        self._last_scenario_explanation = None
        self._last_counterfactual_explanation = None

    @property
    def questions_templates(self):
        return self._questions_templates.values()

    @property
    def current_solution(self):
        return self._current_solution

    @current_solution.setter
    def current_solution(self, solution: Solution):
        if not isinstance(solution, EditableSolution):
            solution = EditableSolution.from_Solution(solution)
        if solution not in self._history:
            self._history.store_solution(solution)
        self._current_solution = solution

    @property
    def current_instance(self):
        return self._current_solution.instance

    ###########
    # History #
    ###########

    @property
    def nb_instances(self):
        return self._history.nb_instances

    @property
    def instances(self):
        return self._history.instances

    @property
    def instances_names(self):
        return self._history.instances_names

    @property
    def solutions(self):
        return self._history.solutions

    @property
    def solutions_names(self):
        return self._history.solutions_names

    def get_instance_by_name(self, instance_name: str):
        return self._history.get_instance_by_name(instance_name)

    def get_solution_by_name(self, solution_name: str):
        return self._history.get_solution_by_name(solution_name)

    def get_solutions_of_instance(self, instance: Instance):
        return self._history.get_solutions_of_instance(instance)

    def get_solutions_of_instance_by_name(self, instance_name: str):
        return self._history.get_solutions_of_instance_by_name(instance_name)

    def store_solution(self, solution: Solution):
        if not isinstance(solution, EditableSolution):
            solution = EditableSolution.from_Solution(solution)
        self._history.store_solution(solution)

    ###########################
    # Contrastive explanation #
    ###########################

    @property
    def contrastive_explanations_directory(self):
        return self._contrastive_explanations_directory

    @contrastive_explanations_directory.setter
    def contrastive_explanations_directory(self, directory_path: bool):
        self._contrastive_explanations_directory = directory_path

    @property
    def export_contrastive_explanations(self):
        return self._export_contrastive_explanations

    @export_contrastive_explanations.setter
    def export_contrastive_explanations(self, export: bool):
        self._export_contrastive_explanations = export

    @property
    def use_already_computed_contrastive_explanations(self):
        return self._use_already_computed_contrastive_explanations

    @use_already_computed_contrastive_explanations.setter
    def use_already_computed_contrastive_explanations(self, use: bool):
        self._use_already_computed_contrastive_explanations = use

    def _create_contrastive_question(self, question_template_id: str, fields_values: list[str]):
        if question_template_id not in self._questions_templates:
            raise ValueError(f"The template {question_template_id} is not handled by this explainer")
        return ContrastiveQuestion(self._current_solution, question_template_id, fields_values)

    def compute_contrastive_explanation(self, question_template_id: str, fields_values: list[str]):
        contrastive_question = self._create_contrastive_question(question_template_id, fields_values)
        contrastive_explanation = None
        if self.use_already_computed_contrastive_explanations:
            file_name = define_explanation_json_file_name(contrastive_question)
            if check_explanation_json_file_existence(file_name, self.contrastive_explanations_directory):
                contrastive_explanation = \
                    import_explanation_from_json_file(file_name, contrastive_question.solution,
                                                      self.contrastive_explanations_directory)
        if contrastive_explanation is None:
            contrastive_support_solution, infeasibility, description_of_applied_transformation = \
                apply_induced_transformation(self.current_solution, contrastive_question)
            contrastive_explanation = create_explanation(contrastive_question, contrastive_support_solution,
                                                         infeasibility, description_of_applied_transformation)
            if self.export_contrastive_explanations:
                export_explanation_to_json_file(contrastive_explanation, self.contrastive_explanations_directory)
        self._last_contrastive_explanation = contrastive_explanation
        self._last_scenario_explanation = None
        self._last_counterfactual_explanation = None
        return contrastive_explanation

    def _get_name_for_contrastive_support_solution(self):
        current_instance_name = self.current_solution.instance.name
        index = current_instance_name.rindex('.')
        return f"{self._root_solution.name}.{current_instance_name[(index+1):]}" \
               f".{str(len(self.get_solutions_of_instance_by_name(current_instance_name)) + 1)}"

    @property
    def last_contrastive_explanation(self):
        if not isinstance(self._last_contrastive_explanation, Explanation):
            raise PermissionError("There is no last contrastive explanation")
        return self._last_contrastive_explanation

    def save_last_contrastive_support_solution(self):
        last_contrastive_support_solution = self.last_contrastive_explanation.support_solution
        if self.last_contrastive_explanation.support_solution_is_feasible:
            last_contrastive_support_solution.name = self._get_name_for_contrastive_support_solution()
            self.store_solution(last_contrastive_support_solution)
        else:
            raise PermissionError("Cannot save the last contrastive support solution as it is not feasible")

    def export_last_contrastive_explanation(self):
        print(f"Exporting explanation to the question: {self.last_contrastive_explanation.question.text}")
        export_explanation_to_json_file(self.last_contrastive_explanation)

    ########################
    # Scenario explanation #
    ########################

    def _create_scenario_question(self, scenario_instance: EditableInstance):
        return ScenarioQuestion(self.last_contrastive_explanation.question, scenario_instance)

    def compute_scenario_explanation(self, scenario_instance: EditableInstance):
        scenario_question = self._create_scenario_question(scenario_instance)
        current_solution = self.current_solution
        scenario_current_solution = current_solution.copy(current_solution.name + "_scenario")
        scenario_current_solution.instance = scenario_instance
        scenario_support_solution, infeasibility, description_of_applied_transformation = \
            apply_induced_transformation(scenario_current_solution, scenario_question)
        scenario_explanation = create_explanation(scenario_question, scenario_support_solution, infeasibility,
                                                  description_of_applied_transformation)
        self._last_scenario_explanation = scenario_explanation
        return scenario_explanation

    def _get_name_for_scenario_support_solution_instance(self):
        return f"{self._root_solution.instance.name}.{str(self.nb_instances + 1)}"

    def _get_name_for_scenario_support_solution(self):
        return f"{self._root_solution.name}.{str(self.nb_instances + 1)}.1"

    @property
    def last_scenario_explanation(self):
        if not isinstance(self._last_scenario_explanation, Explanation):
            raise PermissionError("There is no last scenario explanation")
        return self._last_scenario_explanation

    def save_last_scenario_support_solution(self):
        last_scenario_support_solution = self.last_scenario_explanation.support_solution
        if self.last_scenario_explanation.support_solution_is_feasible:
            last_scenario_support_solution.instance.name = self._get_name_for_scenario_support_solution_instance()
            last_scenario_support_solution.name = self._get_name_for_scenario_support_solution()
            self.store_solution(last_scenario_support_solution)
        else:
            raise PermissionError("Cannot save the last scenario support solution as it is not feasible")

    ##############################
    # Counterfactual explanation #
    ##############################

    def _create_counterfactual_question(self, instance_slacks: InstanceChanges = None):
        return CounterfactualQuestion(self.last_contrastive_explanation.question, instance_slacks)

    def compute_counterfactual_explanation(self, instance_slacks: InstanceChanges = None):
        counterfactual_question = self._create_counterfactual_question(instance_slacks)
        current_solution = self.current_solution
        counterfactual_solution = self.current_solution.copy(current_solution.name + "_counterfactual")
        (counterfactual_support_solution, infeasibility,
         description_of_applied_transformation, instance_alterations) = \
            apply_induced_transformation_bis(counterfactual_solution, counterfactual_question)
        counterfactual_explanation = create_explanation(counterfactual_question, counterfactual_support_solution,
                                                        infeasibility, description_of_applied_transformation,
                                                        instance_alterations)
        self._last_counterfactual_explanation = counterfactual_explanation
        return counterfactual_explanation

    def _get_name_for_counterfactual_support_solution_instance(self):
        return self._get_name_for_scenario_support_solution_instance()

    def _get_name_for_counterfactual_support_solution(self):
        return self._get_name_for_scenario_support_solution()

    @property
    def last_counterfactual_explanation(self):
        if not isinstance(self._last_counterfactual_explanation, Explanation):
            raise PermissionError("There is no last counterfactual explanation")
        return self._last_counterfactual_explanation

    def save_last_counterfactual_support_solution(self):
        last_counterfactual_support_solution = self.last_counterfactual_explanation.support_solution
        if self.last_counterfactual_explanation.support_solution_is_feasible:
            last_counterfactual_support_solution.instance.name = self._get_name_for_scenario_support_solution_instance()
            last_counterfactual_support_solution.name = self._get_name_for_scenario_support_solution()
            self.store_solution(last_counterfactual_support_solution)
        else:
            raise PermissionError("Cannot save the last counterfactual support solution as it is not feasible")
