# Local libraries
from src.checking.feasibility import check_feasibility
from src.explaining.interacting.explainer import Explainer
from src.explaining.interacting.interface.explainer_web_UI import ExplainerWebGUI
from src.explaining.questioning.questions_templates_bank import *
from src.explaining.writing.explanation import export_multiple_contrastive_explanations_to_json_file
from src.reading.solution import extract_solution_from_file
from src.utils.constants import INPUTS_DIRECTORY_RELATIVE_PATH
from src.utils.files import get_project_directory_path, get_paths_of_solutions_files_in_given_directory


#################
# Demo solution #
#################


def get_demo_solution_path():
    """
    Returns the path of the solution for demo.

    :return: the path of the solution for demo (str)
    """
    return f"{get_project_directory_path()}/data/demo/solutions/solution_demo.txt"


def get_demo_solution():
    """
    Returns the solution for demo.

    :return: the solution for demo (Solution)
    """
    solution = extract_solution_from_file(get_demo_solution_path(), True, True, True)
    if not check_feasibility(solution)[0]:
        raise ValueError(f"The solution {solution.name} is not feasible")
    return solution


def compute_contrastive_explanations_about_demo_solution_in_separate_files(questions_templates_ids: list[str] = None):
    """
    Compute contrastive explanations in separate .json files.

    :param questions_templates_ids: the IDs of the questions templates to use (list of str),
    if None, all activated questions templates are computed
    :return: None
    """
    solution = get_demo_solution()
    explainer = Explainer(solution)
    explainer.disable_history()
    explainer.disable_scenario_explanations()
    explainer.disable_counterfactual_explanations()
    explainer.disable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    explanations = []
    if questions_templates_ids is None:
        questions_templates_ids = explainer.activated_questions_templates_ids
    for question_template_id in questions_templates_ids:
        question_template = QUESTIONS_TEMPLATES[question_template_id]
        if question_template in explainer.activated_questions_templates:
            print("Computing explanations related to:", question_template.id)
            all_fields_valid_values = question_template.compute_all_fields_valid_values(solution)
            for fields_values in all_fields_valid_values:
                explanations.append(explainer.get_contrastive_explanation(question_template.id, fields_values))
    export_multiple_contrastive_explanations_to_json_file(explanations)


def compute_contrastive_explanations_about_demo_solution_in_one_file(questions_templates_ids: list[str] = None):
    """
    Compute contrastive explanations in one .json file.

    :param questions_templates_ids: the IDs of the questions templates to use (list of str),
    if None, all activated questions templates are computed
    :return: None
    """
    solution = get_demo_solution()
    explainer = Explainer(solution)
    explainer.disable_history()
    explainer.disable_scenario_explanations()
    explainer.disable_counterfactual_explanations()
    explainer.enable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    if questions_templates_ids is None:
        questions_templates_ids = explainer.activated_questions_templates_ids
    for question_template_id in questions_templates_ids:
        question_template = QUESTIONS_TEMPLATES[question_template_id]
        if question_template in explainer.activated_questions_templates:
            print("Computing explanations related to:", question_template.id)
            all_fields_valid_values = question_template.compute_all_fields_valid_values(solution)
            for fields_values in all_fields_valid_values:
                explainer.get_contrastive_explanation(question_template.id, fields_values)
    explainer.export_all_already_computed_contrastive_explanations()


def launch_explainer_UI_on_demo_solution(language: str = LANGUAGE_ENGLISH_KEY, enable_history: bool = True,
                                         enable_scenario_explanations: bool = True,
                                         enable_counterfactual_explanations: bool = True,
                                         enable_using_already_computed_contrastive_explanations: bool = True):
    """
    Launch the explainer UI on the demo solution.

    :param language: the language to use (str)
    :param enable_history: whether to enable the history (bool)
    :param enable_scenario_explanations: whether to enable the scenario explanations (bool)
    :param enable_counterfactual_explanations: whether to enable the counterfactual explanations (bool)
    :param enable_using_already_computed_contrastive_explanations:
    whether to enable using already computed contrastive explanations (bool)
    :return: None
    """
    explainer = Explainer(get_demo_solution())
    explainer.set_language(language)
    if enable_history:
        explainer.enable_history()
    if enable_scenario_explanations:
        explainer.enable_scenario_explanations()
    if enable_counterfactual_explanations:
        explainer.enable_counterfactual_explanations()
    if enable_using_already_computed_contrastive_explanations:
        explainer.contrastive_explanations_inputs_directory_relative_path = "data/demo/explanations"
        explainer.enable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    explainer_UI = ExplainerWebGUI(explainer)
    explainer_UI.launch()


####################
# Default solution #
####################


def get_default_solution():
    """
    Returns the solution in the default inputs directory.
    If several solutions are found in the default inputs directory, the first one is returned.

    :return: the solution in the default inputs directory (Solution)
    """
    try:
        solution_file_path = get_paths_of_solutions_files_in_given_directory()[0]
    except IndexError:
        raise FileNotFoundError(f"There are no solutions files found in directory {INPUTS_DIRECTORY_RELATIVE_PATH}")
    solution = extract_solution_from_file(solution_file_path, True, True, True)
    if not check_feasibility(solution)[0]:
        raise ValueError(f"The solution {solution.name} is not feasible")
    return solution


def launch_explainer_UI_on_default_solution(language: str, enable_history: bool = True,
                                            enable_scenario_explanations: bool = True,
                                            enable_counterfactual_explanations: bool = True):
    """
    Launch the explainer UI on the default solution.

    :param language: the language to use (str)
    :param enable_history: whether to enable the history (bool)
    :param enable_scenario_explanations: whether to enable the scenario explanations (bool)
    :param enable_counterfactual_explanations: whether to enable the counterfactual explanations (bool)
    :return: None
    """
    explainer = Explainer(get_demo_solution())
    explainer.set_language(language)
    if enable_history:
        explainer.enable_history()
    if enable_scenario_explanations:
        explainer.enable_scenario_explanations()
    if enable_counterfactual_explanations:
        explainer.enable_counterfactual_explanations()
    explainer.disable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    explainer_UI = ExplainerWebGUI(explainer)
    explainer_UI.launch()


########
# Main #
########


if __name__ == '__main__':
    # run_explanations_computation()
    launch_explainer_UI_on_demo_solution()
    # launch_explainer_UI_on_default_solution()
