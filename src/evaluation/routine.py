#! /usr/bin/env python3
# coding: utf-8

# Standard library
from os import path

# Local libraries
from configuration import GUROBI_IS_ENABLED
from src.checking.feasibility import check_feasibility
from src.explaining.interacting.explainer import Explainer
from src.explaining.interacting.interface.explainer_web_UI import ExplainerWebGUI
from src.explaining.questioning.questions_templates_bank import *
from src.explaining.writing.explanation import export_multiple_contrastive_explanations_to_json_file
from src.modeling.instance import Instance
from src.modeling.solution import Solution
if GUROBI_IS_ENABLED:
    from src.optimization.IP.WSRPmodel import WSRPIPModel
from src.reading.instance import extract_instance_from_file
from src.reading.solution import extract_solution_from_file
from src.utils.files import get_project_directory_path, get_default_inputs_directory_path, \
    get_paths_of_instances_files_in_given_directory
from src.writing.solution import write_solution


# Global variables
INSTANCES_FOR_EVALUATION_NAMES = \
    ["instance_evaluation_0", "instance_evaluation_1", "instance_evaluation_2", "instance_evaluation_3"]
SOLUTIONS_FOR_EVALUATION_NAMES = \
    [instance_name.replace("instance", "solution") for instance_name in INSTANCES_FOR_EVALUATION_NAMES]
ACTIVATED_QUESTIONS_TEMPLATES_IDS_FOR_EVALUATION = [WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_SWP_1, WHY_NOT_SWP_2A]


#############################################
# Optimizations of instances for evaluation #
#############################################


def get_path_of_instance_for_evaluation_in_default_inputs_directory(instance_index: int):
    """
    Returns the path of the instance for evaluation with given index
    NB: the instance is assumed to be located in the default inputs directory

    :param instance_index: the index of the instance for evaluation
    :return: the path of the instance for evaluation with given index
    """
    if instance_index < 0 or instance_index > len(INSTANCES_FOR_EVALUATION_NAMES):
        raise ValueError(f"The index {instance_index} is not valid")
    return f"{get_default_inputs_directory_path()}/{INSTANCES_FOR_EVALUATION_NAMES[instance_index]}.xlsx"


def get_instance_for_evaluation_in_default_inputs_directory(instance_index: int):
    """
    Returns the instance for evaluation with given index
    NB: the instance is assumed to be located in the default inputs directory

    :param instance_index: the index of the instance for evaluation
    :return: the instance for evaluation with given index
    """
    instance_path = get_path_of_instance_for_evaluation_in_default_inputs_directory(instance_index)
    if not path.exists(instance_path):
        raise ValueError(f"The instance {instance_path} does not exist")
    return extract_instance_from_file(instance_path, True, True, True, True)


def compute_solution_for_evaluation_by_ILP_optimization(instance: Instance, solving_time_limit: int = None,
                                                        mute_process: bool = False):
    """
    Computes a solution of an instance for evaluation via ILP optimization

    :param instance: the instance for evaluation
    :param solving_time_limit: solving time limit in seconds if any
    :param mute_process: if True, the process is muted
    :return: a solution of the instance for evaluation
    """
    model = WSRPIPModel(instance)
    model.update()
    if solving_time_limit is not None:
        model.solving_time_limit = solving_time_limit
    model.optimize(mute=mute_process)
    solution = model.solution
    if not check_feasibility(solution)[0]:
        raise ValueError(f"The solution {solution.name} is not feasible")
    solution.compute_KPIs()
    return solution


#######################################################
# Reading solutions for evaluation - Inputs directory #
#######################################################


def get_path_of_solution_for_evaluation_in_default_inputs_directory(instance_index: int):
    """
    Returns the path of the solution for evaluation with given index
    NB: the solution is assumed to be located in the default inputs directory

    :param instance_index: the index of the solution for evaluation
    :return: the path of the solution for evaluation with given index
    """
    if instance_index < 0 or instance_index > len(INSTANCES_FOR_EVALUATION_NAMES):
        raise ValueError(f"The index {instance_index} is not valid")
    return f"{get_default_inputs_directory_path()}/{SOLUTIONS_FOR_EVALUATION_NAMES[instance_index]}.txt"


def get_solution_for_evaluation_in_default_inputs_directory(instance_index: int):
    """
    Returns the solution for evaluation with given index
    NB: the solution is assumed to be located in the default inputs directory

    :param instance_index: the index of the instance for evaluation
    :return: the solution for evaluation with given index
    """
    solution = extract_solution_from_file(
        get_path_of_solution_for_evaluation_in_default_inputs_directory(instance_index), True, True, True, True, True
    )
    feasible, text = check_feasibility(solution)
    if not feasible:
        raise ValueError(f"The solution {solution.name} is not feasible: {text}")
    return solution


###########################################################
# Reading solutions for evaluation - Evaluation directory #
###########################################################


def get_solutions_for_evaluation_directory_path():
    """
    Returns the path of the directory containing the solutions for evaluation

    :return: the path of the directory containing the solutions for evaluation
    """
    return get_project_directory_path() + "/data/evaluation/solutions"


def get_solution_for_evaluation_path(instance_index: int = None):
    if instance_index is None:
        return f"{get_solutions_for_evaluation_directory_path()}/solution_evaluation.txt"
    else:
        return f"{get_solutions_for_evaluation_directory_path()}/solution_evaluation_{str(instance_index)}.txt"


def get_solution_for_evaluation(instance_index: int = None):
    ignore_instance_version = True
    ignore_solving_method = True
    ignore_employees_unavailabilities = True
    ignore_tasks_unavailabilities = True
    ignore_lunch_breaks = True
    solution = extract_solution_from_file(
        get_solution_for_evaluation_path(instance_index), ignore_employees_unavailabilities,
        ignore_tasks_unavailabilities, ignore_lunch_breaks, ignore_instance_version, ignore_solving_method
    )
    feasible, text = check_feasibility(solution)
    if not feasible:
        raise ValueError(f"The solution {solution.name} is not feasible: {text}")
    return solution


####################################
# Check of explanations negativity #
####################################

def check_explanations_negativity(solution: Solution, only_activated_questions_templates_for_evaluation: bool):
    explainer = Explainer(solution)
    explainer.disable_history()
    explainer.disable_scenario_explanations()
    explainer.disable_counterfactual_explanations()
    explainer.disable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    if only_activated_questions_templates_for_evaluation:
        questions_templates = \
            [QUESTIONS_TEMPLATES[question_template_id]
             for question_template_id in ACTIVATED_QUESTIONS_TEMPLATES_IDS_FOR_EVALUATION]
    else:
        questions_templates = explainer.activated_questions_templates
    for question_template in questions_templates:
        print("Computing explanations related to:", question_template.id)
        all_fields_valid_values = question_template.compute_all_fields_valid_values(solution)
        index = 0
        for fields_values in all_fields_valid_values:
            try:
                index += 1
                explanation = explainer.get_contrastive_explanation(question_template.id, fields_values)
                if explanation.is_positive():
                    print(f"The question {explanation.question.text} leads to a positive explanation")
                    return False
                if '3' in explanation.question.template.id and index % 25 == 0:
                    print(f"Explanation answering to {explanation.question.text} computed")
            except ValueError as error:
                print(f"Error `{error}` raised for question {question_template.id} with fields {fields_values}")
                continue
    return True


###############################
# Computation of explanations #
###############################


def run_explanations_computation(solution: Solution):
    explainer = Explainer(solution)
    explainer.disable_history()
    explainer.disable_scenario_explanations()
    explainer.disable_counterfactual_explanations()
    explainer.disable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    explanations = []
    for question_template_id in ACTIVATED_QUESTIONS_TEMPLATES_IDS_FOR_EVALUATION:
        question_template = QUESTIONS_TEMPLATES[question_template_id]
        if question_template in explainer.activated_questions_templates:
            print("Computing explanations related to:", question_template.id)
            all_fields_valid_values = question_template.compute_all_fields_valid_values(solution)
            for fields_values in all_fields_valid_values:
                explanations.append(explainer.get_contrastive_explanation(question_template.id, fields_values))
    export_multiple_contrastive_explanations_to_json_file(explanations)


#######################################
# Reading explanations for evaluation #
#######################################


def get_explanations_for_evaluation_directory_path():
    return get_project_directory_path() + "/data/evaluation/explanations"


#################################
# User interface for evaluation #
#################################


# TODO: some of the functions below will be deprecated


def prepare_explainer_UI_for_evaluation(solution: Solution):
    explainer = Explainer(solution)
    explainer.set_language(LANGUAGE_FRENCH_KEY)
    explainer.activate_only_questions_templates(ACTIVATED_QUESTIONS_TEMPLATES_IDS_FOR_EVALUATION)
    explainer.disable_history()
    explainer.disable_scenario_explanations()
    explainer.disable_counterfactual_explanations()
    explainer.disable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    return ExplainerWebGUI(explainer)


def prepare_explainer_UI_on_evaluation_solution(instance_index: int = None):
    return prepare_explainer_UI_for_evaluation(get_solution_for_evaluation(instance_index))


def launch_explainer_UI_on_evaluation_solution():
    explainer_UI = prepare_explainer_UI_on_evaluation_solution()
    explainer_UI.launch()
