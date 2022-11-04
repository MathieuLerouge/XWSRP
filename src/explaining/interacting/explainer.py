# Local libraries
from src.explaining.answering.explanation import *
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.modeling.instance import EditableInstance
from src.explaining.modeling.solution import EditableSolution
from src.explaining.interacting.history import History
from src.explaining.questioning.question import ContrastiveQuestion, CounterfactualQuestion
from src.explaining.questioning.questions_templates_bank import *
from src.explaining.reading.explanation import import_single_explanation_from_json_file, \
    import_multiple_explanations_from_json_file
from src.utils.files import check_inputs_file_existence
from src.explaining.transforming.transformation import apply_induced_transformation, apply_induced_transformation_bis
from src.explaining.writing.explanation import define_single_contrastive_explanation_json_file_name, \
    export_single_contrastive_explanation_to_json_file, define_multiple_contrastive_explanations_json_file_name, \
    export_multiple_contrastive_explanations_to_json_file
from src.modeling.instance import Instance
from src.modeling.solution import Solution
from src.utils.constants import INPUTS_DIRECTORY_RELATIVE_PATH, OUTPUTS_DIRECTORY_RELATIVE_PATH


# Class Explainer
class Explainer:

    _available_questions_templates_ids = [
        WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
        WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3
    ]

    def __init__(self, solution: Solution):
        self._activated_questions_templates = dict([(id, QUESTIONS_TEMPLATES[id]) for id in QUESTIONS_TEMPLATES.keys()
                                                    if id in self._available_questions_templates_ids])
        self._root_solution = EditableSolution.from_Solution(solution)
        self._history_is_enabled = False
        self._history = History(self._root_solution)
        self._current_solution = self._root_solution
        self._contrastive_explanations_inputs_directory_relative_path = INPUTS_DIRECTORY_RELATIVE_PATH
        self._contrastive_explanations_outputs_directory_relative_path = OUTPUTS_DIRECTORY_RELATIVE_PATH
        self._automatically_exporting_single_contrastive_explanations_is_enabled = False
        self._using_already_computed_contrastive_explanations_is_enabled = False
        self._already_computed_contrastive_explanations = dict()
        self._last_contrastive_explanation = None
        self._scenario_explanations_are_enabled = False
        self._last_scenario_explanation = None
        self._counterfactual_explanations_are_enabled = False
        self._last_counterfactual_explanation = None

    #################################
    # Current instance and solution #
    #################################

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

    #####################
    # Question template #
    #####################

    @property
    def activated_questions_templates(self):
        return list(self._activated_questions_templates.values())

    def activate_question_template(self, question_template_id: str):
        if question_template_id in self._available_questions_templates_ids:
            self._activated_questions_templates[question_template_id] = QUESTIONS_TEMPLATES[question_template_id]

    def activate_questions_templates(self, questions_templates_ids: list[str]):
        for question_template_id in questions_templates_ids:
            self.activate_question_template(question_template_id)

    def activate_only_questions_templates(self, questions_templates_ids: list[str]):
        self.deactivate_all_questions_templates()
        self.activate_questions_templates(questions_templates_ids)

    def deactivate_question_template(self, question_template_id: str):
        if question_template_id in self._activated_questions_templates.keys():
            del self._activated_questions_templates[question_template_id]

    def deactivate_questions_templates(self, questions_templates_ids: list[str]):
        for question_template_id in questions_templates_ids:
            self.deactivate_question_template(question_template_id)

    def deactivate_all_questions_templates(self):
        self._activated_questions_templates = dict()

    ###########
    # History #
    ###########

    @property
    def history_is_enabled(self):
        return self._history_is_enabled

    @property
    def history_is_disabled(self):
        return not self._history_is_enabled

    def enable_history(self):
        self._history_is_enabled = True
        solution = self._root_solution.copy(name=f"{self._root_solution.name}.1.1")
        solution.instance = self._root_solution.instance.copy(name=f"{solution.instance.name}.1")
        self._history = History(solution)
        self._current_solution = solution

    def disable_history(self):
        self._history_is_enabled = False
        self._history = History(self._root_solution)
        self._current_solution = self._root_solution

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
        if self._history_is_enabled:
            if not isinstance(solution, EditableSolution):
                solution = EditableSolution.from_Solution(solution)
            self._history.store_solution(solution)
        else:
            raise PermissionError("Historizing is disabled")

    #############################################
    # Contrastive explanation - Import / export #
    #############################################

    @property
    def contrastive_explanations_inputs_directory_relative_path(self):
        return self._contrastive_explanations_inputs_directory_relative_path

    @contrastive_explanations_inputs_directory_relative_path.setter
    def contrastive_explanations_inputs_directory_relative_path(self, directory_relative_path: bool):
        self._contrastive_explanations_inputs_directory_relative_path = directory_relative_path

    @property
    def contrastive_explanations_outputs_directory_relative_path(self):
        return self._contrastive_explanations_outputs_directory_relative_path

    @contrastive_explanations_outputs_directory_relative_path.setter
    def contrastive_explanations_outputs_directory_relative_path(self, directory_relative_path: bool):
        self._contrastive_explanations_outputs_directory_relative_path = directory_relative_path

    def enable_exporting_automatically_single_contrastive_explanations(self):
        self._automatically_exporting_single_contrastive_explanations_is_enabled = True

    def disable_exporting_automatically_single_contrastive_explanations(self):
        self._automatically_exporting_single_contrastive_explanations_is_enabled = False

    @property
    def automatically_export_single_contrastive_explanations(self):
        return self._automatically_exporting_single_contrastive_explanations_is_enabled

    @automatically_export_single_contrastive_explanations.setter
    def automatically_export_single_contrastive_explanations(self, export: bool):
        if export:
            self.enable_exporting_automatically_single_contrastive_explanations()
        else:
            self.disable_exporting_automatically_single_contrastive_explanations()

    def export_all_already_computed_contrastive_explanations(self, outputs_directory_relative_path: str = None):
        export_multiple_contrastive_explanations_to_json_file(self.already_computed_contrastive_explanations,
                                                              outputs_directory_relative_path)

    #####################################################
    # Contrastive explanation - Manage already computed #
    #####################################################

    @property
    def already_computed_contrastive_explanations(self):
        explanations = []
        for template_id in self._already_computed_contrastive_explanations.keys():
            for explanation in self._already_computed_contrastive_explanations[template_id].values():
                explanations.append(explanation)
        return explanations

    def _add_contrastive_explanation_to_already_computed_ones(self, explanation: Explanation):
        if not explanation.is_contrastive:
            raise ValueError("Given explanation is not contrastive")
        if not self._using_already_computed_contrastive_explanations_is_enabled:
            raise PermissionError("Storing any contrastive explanation in already computed ones is not allowed"
                                  "as using already computed contrastive explanations is disabled")
        template_id = explanation.question.template.id
        if template_id not in self._already_computed_contrastive_explanations.keys():
            self._already_computed_contrastive_explanations[template_id] = dict()
        fields_values_str = str(explanation.question.fields_values)
        if fields_values_str not in self._already_computed_contrastive_explanations[template_id]:
            self._already_computed_contrastive_explanations[template_id][fields_values_str] = explanation

    def _add_contrastive_explanations_to_already_computed_ones(self, explanations: list[Explanation]):
        for explanation in explanations:
            self._add_contrastive_explanation_to_already_computed_ones(explanation)

    def _check_if_contrastive_explanation_is_in_already_computed_ones(self, contrastive_question: ContrastiveQuestion):
        template_id = contrastive_question.template.id
        if template_id not in self._already_computed_contrastive_explanations.keys():
            return False
        fields_values_str = str(contrastive_question.fields_values)
        return fields_values_str in self._already_computed_contrastive_explanations[template_id]

    def _get_already_computed_contrastive_explanation(self, contrastive_question: ContrastiveQuestion):
        if not self._check_if_contrastive_explanation_is_in_already_computed_ones(contrastive_question):
            raise ValueError("Explanation associated to given question is not already computed")
        template_id, fields_values_str = contrastive_question.template.id, str(contrastive_question.fields_values)
        return self._already_computed_contrastive_explanations[template_id][fields_values_str]

    def enable_using_already_computed_contrastive_explanations(self):
        self._using_already_computed_contrastive_explanations_is_enabled = True
        multiple_explanations_json_file_name = \
            define_multiple_contrastive_explanations_json_file_name(self._current_solution)
        if check_inputs_file_existence(multiple_explanations_json_file_name,
                                       self.contrastive_explanations_inputs_directory_relative_path):
            self._add_contrastive_explanations_to_already_computed_ones(
                import_multiple_explanations_from_json_file(
                    multiple_explanations_json_file_name, self._current_solution,
                    self.contrastive_explanations_inputs_directory_relative_path
                )
            )

    def disable_using_already_computed_contrastive_explanations(self):
        self._using_already_computed_contrastive_explanations_is_enabled = False

    @property
    def is_using_already_computed_contrastive_explanations(self):
        return self._using_already_computed_contrastive_explanations_is_enabled

    @is_using_already_computed_contrastive_explanations.setter
    def is_using_already_computed_contrastive_explanations(self, use: bool):
        if use:
            self.enable_using_already_computed_contrastive_explanations()
        else:
            self.disable_using_already_computed_contrastive_explanations()

    #####################################
    # Contrastive explanation - Compute #
    #####################################

    def _create_contrastive_question(self, question_template_id: str, fields_values: list[str]):
        if question_template_id not in self._activated_questions_templates:
            raise ValueError(f"The template {question_template_id} is not handled by this explainer")
        return ContrastiveQuestion(self._current_solution, question_template_id, fields_values)

    def _compute_contrastive_explanation(self, contrastive_question: ContrastiveQuestion):
        contrastive_support_solution, infeasibility, description_of_applied_transformation = \
            apply_induced_transformation(self.current_solution, contrastive_question)
        contrastive_explanation = create_explanation(contrastive_question, contrastive_support_solution,
                                                     infeasibility, description_of_applied_transformation)
        if self.is_using_already_computed_contrastive_explanations:
            self._add_contrastive_explanation_to_already_computed_ones(contrastive_explanation)
        if self.automatically_export_single_contrastive_explanations:
            export_single_contrastive_explanation_to_json_file(
                contrastive_explanation, self.contrastive_explanations_outputs_directory_relative_path
            )
        return contrastive_explanation

    #################################
    # Contrastive explanation - Get #
    #################################

    def get_contrastive_explanation(self, question_template_id: str, fields_values: list[str]):
        contrastive_question = self._create_contrastive_question(question_template_id, fields_values)
        contrastive_explanation = None
        if self.is_using_already_computed_contrastive_explanations:
            if self._check_if_contrastive_explanation_is_in_already_computed_ones(contrastive_question):
                contrastive_explanation = self._get_already_computed_contrastive_explanation(contrastive_question)
            else:
                file_name = define_single_contrastive_explanation_json_file_name(contrastive_question)
                if check_inputs_file_existence(file_name, self.contrastive_explanations_inputs_directory_relative_path):
                    contrastive_explanation = import_single_explanation_from_json_file(
                        file_name, contrastive_question.solution,
                        self.contrastive_explanations_inputs_directory_relative_path
                    )
                    self._add_contrastive_explanation_to_already_computed_ones(contrastive_explanation)
        if contrastive_explanation is None:
            contrastive_explanation = self._compute_contrastive_explanation(contrastive_question)
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
        export_single_contrastive_explanation_to_json_file(
            self.last_contrastive_explanation, self.contrastive_explanations_outputs_directory_relative_path
        )

    ########################
    # Scenario explanation #
    ########################

    @property
    def scenario_explanations_are_enabled(self):
        return self._scenario_explanations_are_enabled

    @property
    def scenario_explanations_are_disabled(self):
        return not self._scenario_explanations_are_enabled

    def enable_scenario_explanations(self):
        self._scenario_explanations_are_enabled = True

    def disable_scenario_explanations(self):
        self._scenario_explanations_are_enabled = False

    def _create_scenario_question(self, scenario_instance: EditableInstance):
        return ScenarioQuestion(self.last_contrastive_explanation.question, scenario_instance)

    def compute_scenario_explanation(self, scenario_instance: EditableInstance):
        if self.scenario_explanations_are_enabled:
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
        else:
            raise PermissionError("Scenario explanations are not enabled")

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

    @property
    def counterfactual_explanations_are_enabled(self):
        return self._counterfactual_explanations_are_enabled

    @property
    def counterfactual_explanations_are_disabled(self):
        return not self._counterfactual_explanations_are_enabled

    def enable_counterfactual_explanations(self):
        self._counterfactual_explanations_are_enabled = True

    def disable_counterfactual_explanations(self):
        self._counterfactual_explanations_are_enabled = False

    def _create_counterfactual_question(self, instance_slacks: InstanceChanges = None):
        return CounterfactualQuestion(self.last_contrastive_explanation.question, instance_slacks)

    def compute_counterfactual_explanation(self, instance_slacks: InstanceChanges = None):
        if self.counterfactual_explanations_are_enabled:
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
        else:
            raise PermissionError("Counterfactual explanations")

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
