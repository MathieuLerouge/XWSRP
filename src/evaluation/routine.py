#! /usr/bin/env python3
# coding: utf-8

# Local libraries
from src.checking.feasibility import check_feasibility
from src.explaining.interacting.explainer import Explainer
from src.explaining.interacting.interface.explainer_web_UI import ExplainerWebGUI
from src.explaining.questioning.questions_templates_bank import *
from src.reading.solution import extract_solution_from_file
from src.utils.files import get_project_directory_path


def get_solutions_for_evaluation_directory_path():
    return get_project_directory_path() + "/data/evaluation/solutions"


def get_solution_for_evaluation_path():
    return get_solutions_for_evaluation_directory_path() + "/solution_evaluation.txt"


def get_explanations_for_evaluation_directory_path():
    return get_project_directory_path() + "/data/evaluation/explanations"


def prepare_explainer():
    solution_file_name = get_solution_for_evaluation_path()
    ignore_instance_version = True
    ignore_solving_method = True
    ignore_employees_unavailabilities = True
    ignore_tasks_unavailabilities = True
    ignore_lunch_breaks = True
    solution = extract_solution_from_file(
        solution_file_name, ignore_employees_unavailabilities, ignore_tasks_unavailabilities, ignore_lunch_breaks,
        ignore_instance_version, ignore_solving_method
    )
    if not check_feasibility(solution)[0]:
        raise ValueError(f"The solution {solution.name} is not feasible")
    explainer = Explainer(solution)
    explainer.contrastive_explanations_directory = get_explanations_for_evaluation_directory_path()
    explainer.enable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_contrastive_explanations()
    explainer.activate_only_questions_templates([WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_SWP_1, WHY_NOT_SWP_2A])
    explainer.disable_history()
    explainer.disable_scenario_explanations()
    explainer.disable_counterfactual_explanations()
    return explainer


def prepare_explainer_UI():
    explainer = prepare_explainer()
    explainer_UI = ExplainerWebGUI(explainer)
    return explainer_UI


def launch_explanation_UI():
    explainer_UI = prepare_explainer_UI()
    explainer_UI.launch()


if __name__ == '__main__':
    launch_explanation_UI()
