#! /usr/bin/env python3
# coding: utf-8


# Local libraries
from src.checking.feasibility import check_feasibility
from src.explaining.interacting.explainer import Explainer
from src.explaining.interacting.interface.explainer_web_UI import ExplainerWebGUI
from src.explaining.questioning.questions_templates_bank import WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, \
    WHY_NOT_INS_2C, WHY_NOT_INS_3, WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3, \
    QUESTIONS_TEMPLATES
from src.explaining.writing.explanation import export_multiple_contrastive_explanations_to_json_file
from src.reading.solution import extract_solution_from_file
from src.utils.constants import INPUTS_DIRECTORY_RELATIVE_PATH, LANGUAGE_FRENCH_KEY
from src.utils.files import get_project_directory_path, get_solutions_files_paths, make_absolute_path


def get_demo_solution_path():
    return f"{get_project_directory_path()}/data/demo/solutions/solution_demo.txt"


def get_demo_solution():
    ignore_instance_version = True
    ignore_solving_method = True
    ignore_employees_unavailabilities = True
    ignore_tasks_unavailabilities = True
    ignore_lunch_breaks = True
    solution = extract_solution_from_file(
        get_demo_solution_path(), ignore_employees_unavailabilities, ignore_tasks_unavailabilities, ignore_lunch_breaks,
        ignore_instance_version, ignore_solving_method
    )
    if not check_feasibility(solution)[0]:
        raise ValueError(f"The solution {solution.name} is not feasible")
    return solution


def get_default_solution():
    try:
        solution_file_path = get_solutions_files_paths()[0]
    except IndexError:
        raise FileNotFoundError(f"There are no solutions files found in directory {INPUTS_DIRECTORY_RELATIVE_PATH}")
    ignore_instance_version = True
    ignore_solving_method = True
    ignore_employees_unavailabilities = True
    ignore_tasks_unavailabilities = True
    ignore_lunch_breaks = True
    solution = extract_solution_from_file(
        solution_file_path, ignore_employees_unavailabilities, ignore_tasks_unavailabilities, ignore_lunch_breaks,
        ignore_instance_version, ignore_solving_method
    )
    if not check_feasibility(solution)[0]:
        raise ValueError(f"The solution {solution.name} is not feasible")
    return solution


def launch_explainer_UI_on_demo_solution():
    explainer = Explainer(get_demo_solution())
    explainer.set_language(LANGUAGE_FRENCH_KEY)
    explainer.enable_history()
    explainer.enable_scenario_explanations()
    explainer.enable_counterfactual_explanations()
    explainer.contrastive_explanations_inputs_directory_relative_path = "data/demo/explanations"
    explainer.enable_using_already_computed_contrastive_explanations()
    explainer_UI = ExplainerWebGUI(explainer)
    explainer_UI.launch()


def run_explanations_computation():
    solution = get_demo_solution()
    explainer = Explainer(solution)
    explainer.disable_history()
    explainer.disable_scenario_explanations()
    explainer.disable_counterfactual_explanations()
    explainer.disable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    explanations = []
    # questions_templates_ids = [
    #     WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
    #     WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3
    # ]
    questions_templates_ids = [WHY_NOT_INS_1]
    for question_template_id in questions_templates_ids:
        question_template = QUESTIONS_TEMPLATES[question_template_id]
        if question_template in explainer.activated_questions_templates:
            print("Computing explanations related to:", question_template.id)
            all_fields_valid_values = question_template.compute_all_fields_valid_values(solution)
            for fields_values in all_fields_valid_values:
                explanations.append(explainer.get_contrastive_explanation(question_template.id, fields_values))
    export_multiple_contrastive_explanations_to_json_file(explanations)


def run_explanations_computation_bis():
    solution = get_demo_solution()
    explainer = Explainer(solution)
    explainer.disable_history()
    explainer.disable_scenario_explanations()
    explainer.disable_counterfactual_explanations()
    explainer.enable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    # questions_templates_ids = [
    #     WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
    #     WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3
    # ]
    questions_templates_ids = [WHY_NOT_INS_1]
    for question_template_id in questions_templates_ids:
        question_template = QUESTIONS_TEMPLATES[question_template_id]
        if question_template in explainer.activated_questions_templates:
            print("Computing explanations related to:", question_template.id)
            all_fields_valid_values = question_template.compute_all_fields_valid_values(solution)
            for fields_values in all_fields_valid_values:
                explainer.get_contrastive_explanation(question_template.id, fields_values)
    explainer.export_all_already_computed_contrastive_explanations()


def apply_explanation_routine():
    launch_explainer_UI_on_demo_solution()


if __name__ == '__main__':
    launch_explainer_UI_on_demo_solution()
    # run_explanations_computation()
    # run_explanations_computation_bis()
