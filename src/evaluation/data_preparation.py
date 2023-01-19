# Standard library
from os import path

# Local libraries
from main_configuration import GUROBI_IS_ENABLED
from src.checking.feasibility import check_feasibility
from src.evaluation.constants import INSTANCES_FOR_EVALUATION_NAMES, SOLUTIONS_FOR_EVALUATION_NAMES, \
    ACTIVATED_QUESTIONS_TEMPLATES_IDS_FOR_EVALUATION
from src.explaining.interacting.explainer import Explainer
from src.explaining.questioning.questions_templates_bank import *
from src.explaining.writing.explanation import export_multiple_contrastive_explanations_to_json_file
from src.modeling.instance import Instance
from src.modeling.solution import Solution
if GUROBI_IS_ENABLED:
    from src.optimization.IP.WSRPmodel import WSRPIPModel
from src.reading.instance import extract_instance_from_file
from src.reading.solution import extract_solution_from_file
from src.utils.files import get_default_inputs_directory_path


#############################################
# Optimizations of instances for evaluation #
#############################################


def get_path_of_instance_for_evaluation_in_default_inputs_directory(instance_index: int):
    """
    Returns the path of the instance for evaluation with given index
    NB: the instance is assumed to be located in the default inputs directory

    :param instance_index: the index of the instance for evaluation (int)
    :return: the path of the instance for evaluation with given index
    """
    if instance_index < 0 or instance_index > len(INSTANCES_FOR_EVALUATION_NAMES):
        raise ValueError(f"The index {instance_index} is not valid")
    return f"{get_default_inputs_directory_path()}/{INSTANCES_FOR_EVALUATION_NAMES[instance_index]}.xlsx"


def get_instance_for_evaluation_in_default_inputs_directory(instance_index: int):
    """
    Returns the instance for evaluation with given index
    NB: the instance is assumed to be located in the default inputs directory

    :param instance_index: the index of the instance for evaluation (int)
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

    :param instance: the instance for evaluation (Instance)
    :param solving_time_limit: solving time limit in seconds if any (int)
    :param mute_process: if True, the process is muted (bool)
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


################################################################
# Reading solutions for evaluation located in inputs directory #
################################################################


def get_path_of_solution_for_evaluation_in_default_inputs_directory(instance_index: int):
    """
    Returns the path of the solution for evaluation with given index
    NB: the solution is assumed to be located in the default inputs directory

    :param instance_index: the index of the solution for evaluation (int)
    :return: the path of the solution for evaluation with given index
    """
    if instance_index < 0 or instance_index > len(INSTANCES_FOR_EVALUATION_NAMES):
        raise ValueError(f"The index {instance_index} is not valid")
    return f"{get_default_inputs_directory_path()}/{SOLUTIONS_FOR_EVALUATION_NAMES[instance_index]}.txt"


def get_solution_for_evaluation_in_default_inputs_directory(instance_index: int):
    """
    Returns the solution for evaluation with given index
    NB: the solution is assumed to be located in the default inputs directory

    :param instance_index: the index of the instance for evaluation (int)
    :return: the solution for evaluation with given index
    """
    solution = extract_solution_from_file(
        get_path_of_solution_for_evaluation_in_default_inputs_directory(instance_index), True, True, True, True, True
    )
    feasible, text = check_feasibility(solution)
    if not feasible:
        raise ValueError(f"The solution {solution.name} is not feasible: {text}")
    return solution


####################################
# Check of explanations negativity #
####################################

def check_explanations_negativity(solution: Solution, only_activated_questions_templates_for_evaluation: bool):
    """
    Checks that the explanations about a solution are all negative

    :param solution: solution for evaluation which explanations are checked (Solution)
    :param only_activated_questions_templates_for_evaluation: if True, only activated questions templates for evaluation
    are considered (bool)
    :return:
    """
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
        print("Checking explanations related to:", question_template.id)
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
                    print(f"Now checking explanation answering to {explanation.question.text} computed")
            except ValueError as error:
                print(f"Error `{error}` raised for question {question_template.id} with fields {fields_values}")
                continue
    return True


###############################
# Computation of explanations #
###############################


def compute_and_export_contrastive_explanations(solution: Solution,
                                                only_activated_questions_templates_for_evaluation: bool,
                                                only_ILP_based_computation: bool = False):
    """
    Computes and exports all contrastive explanations about a solution
    NB: the explanations are exported in the default outputs directory

    :param solution: solution for evaluation which explanations are computed (Solution)
    :param only_activated_questions_templates_for_evaluation: if True, only activated questions templates for evaluation
    are considered (bool)
    :param only_ILP_based_computation: if True, only questions which explanations computation is based on solving
    an ILP model are considered (bool)
    :return: None
    """
    explainer = Explainer(solution)
    explainer.disable_history()
    explainer.disable_scenario_explanations()
    explainer.disable_counterfactual_explanations()
    explainer.disable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    explanations = []
    if only_activated_questions_templates_for_evaluation:
        questions_templates = \
            [QUESTIONS_TEMPLATES[question_template_id]
             for question_template_id in ACTIVATED_QUESTIONS_TEMPLATES_IDS_FOR_EVALUATION]
    else:
        questions_templates = explainer.activated_questions_templates
    for question_template in questions_templates:
        if (not only_ILP_based_computation or
                (only_ILP_based_computation and question_template.id in ILP_BASED_COMPUTATION_QUESTIONS_TEMPLATES_IDS)):
            if question_template in explainer.activated_questions_templates:
                print("Computing explanations related to:", question_template.id)
                all_fields_valid_values = question_template.compute_all_fields_valid_values(solution)
                for fields_values in all_fields_valid_values:
                    explanations.append(explainer.get_contrastive_explanation(question_template.id, fields_values))
    export_multiple_contrastive_explanations_to_json_file(explanations)
