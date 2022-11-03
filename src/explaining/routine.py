#! /usr/bin/env python3
# coding: utf-8


# Local libraries
from src.checking.feasibility import check_feasibility
from src.explaining.interacting.explainer import Explainer
from src.explaining.interacting.interface.explainer_web_UI import ExplainerWebGUI
from src.explaining.questioning.questions_templates_bank import WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, \
    WHY_NOT_INS_2C, WHY_NOT_INS_3, WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3, \
    QUESTIONS_TEMPLATES
from src.explaining.writing.explanation import export_multiple_explanations_to_json_file
from src.reading.solution import extract_solution_from_file
from src.utils.constants import INPUTS_DIRECTORY_RELATIVE_PATH
from src.utils.files import get_solutions_files_paths


def prepare_explainer():
    try:
        solution_file_name = get_solutions_files_paths()[0]
    except IndexError:
        raise FileNotFoundError(f"There are no solutions files found in directory {INPUTS_DIRECTORY_RELATIVE_PATH}")
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
    return Explainer(solution)


def launch_explanation_UI():
    explainer = prepare_explainer()
    explainer.contrastive_explanations_directory = "data/demo/explanations"
    explainer.export_contrastive_explanations = False
    explainer.use_already_computed_contrastive_explanations = True
    explainer_UI = ExplainerWebGUI(explainer)
    explainer_UI.launch()


def run_explanations_computation_routine():
    explainer = prepare_explainer()
    solution = explainer.current_solution
    explanations = []
    questions_templates_ids = [
        WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
        WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3
    ]
    for question_template_id in questions_templates_ids:
        question_template = QUESTIONS_TEMPLATES[question_template_id]
        if question_template in explainer.activated_questions_templates:
            print("Computing explanations related to:", question_template.id)
            all_fields_valid_values = question_template.compute_all_fields_valid_values(solution)
            for fields_values in all_fields_valid_values:
                explanations.append(explainer.compute_contrastive_explanation(question_template.id, fields_values))
    export_multiple_explanations_to_json_file(explanations)


def apply_explanation_routine():
    launch_explanation_UI()


if __name__ == '__main__':
    launch_explanation_UI()
    # run_explanations_computation_routine()
