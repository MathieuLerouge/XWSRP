#! /usr/bin/env python3
# coding: utf-8


# Local libraries
from src.checking.feasibility import check_feasibility
from src.explaining.interacting.explainer import Explainer
from src.explaining.interacting.interface.explainer_web_UI import ExplainerWebGUI
from src.explaining.questioning.questions_templates_bank import *
from src.explaining.writing.explanation import export_multiple_contrastive_explanations_to_json_file
from src.reading.solution import extract_solution_from_file
from src.utils.files import get_project_directory_path


# Global variables
ACTIVATED_QUESTIONS_TEMPLATES_FOR_EVALUATION = [WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_SWP_1, WHY_NOT_SWP_2A]


def get_solutions_for_evaluation_directory_path():
    return get_project_directory_path() + "/data/evaluation/solutions"


def get_solution_for_evaluation_path():
    return get_solutions_for_evaluation_directory_path() + "/solution_evaluation.txt"


def get_solution_for_evaluation():
    ignore_instance_version = True
    ignore_solving_method = True
    ignore_employees_unavailabilities = True
    ignore_tasks_unavailabilities = True
    ignore_lunch_breaks = True
    solution = extract_solution_from_file(
        get_solution_for_evaluation_path(), ignore_employees_unavailabilities, ignore_tasks_unavailabilities,
        ignore_lunch_breaks, ignore_instance_version, ignore_solving_method
    )
    if not check_feasibility(solution)[0]:
        raise ValueError(f"The solution {solution.name} is not feasible")
    return solution


def get_explanations_for_evaluation_directory_path():
    return get_project_directory_path() + "/data/evaluation/explanations"


def run_explanations_computation():
    solution = get_solution_for_evaluation()
    explainer = Explainer(get_solution_for_evaluation())
    explainer.disable_history()
    explainer.disable_scenario_explanations()
    explainer.disable_counterfactual_explanations()
    explainer.disable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    explanations = []
    for question_template_id in ACTIVATED_QUESTIONS_TEMPLATES_FOR_EVALUATION:
        question_template = QUESTIONS_TEMPLATES[question_template_id]
        if question_template in explainer.activated_questions_templates:
            print("Computing explanations related to:", question_template.id)
            all_fields_valid_values = question_template.compute_all_fields_valid_values(solution)
            for fields_values in all_fields_valid_values:
                explanations.append(explainer.get_contrastive_explanation(question_template.id, fields_values))
    export_multiple_contrastive_explanations_to_json_file(explanations)


def prepare_explainer_UI_on_evaluation_solution():
    explainer = Explainer(get_solution_for_evaluation())
    explainer.activate_only_questions_templates(ACTIVATED_QUESTIONS_TEMPLATES_FOR_EVALUATION)
    explainer.disable_history()
    explainer.disable_scenario_explanations()
    explainer.disable_counterfactual_explanations()
    explainer.contrastive_explanations_inputs_directory_relative_path = get_explanations_for_evaluation_directory_path()
    explainer.enable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    return ExplainerWebGUI(explainer)


def launch_explainer_UI_on_evaluation_solution():
    explainer_UI = prepare_explainer_UI_on_evaluation_solution()
    explainer_UI.launch()


if __name__ == '__main__':
    # run_explanations_computation()
    launch_explainer_UI_on_evaluation_solution()
