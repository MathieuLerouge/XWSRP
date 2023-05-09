# Local libraries
from src.checking.feasibility import check_feasibility
from src.evaluation.constants import INSTANCES_FOR_EVALUATION_NAMES
from src.explaining.writing.explanation import define_multiple_contrastive_explanations_json_file_name
from src.optimization.heuristics.solution import SolutionForHeuristics
from src.reading.solution import extract_solution_from_file
from src.utils.files import get_project_directory_path


######################################################################
# Reading solutions for evaluation (located in evaluation directory) #
######################################################################


def get_solutions_for_evaluation_directory_path():
    """
    Returns the path of the directory containing the solutions for evaluation.

    :return: the path of the directory containing the solutions for evaluation
    """
    return get_project_directory_path() + "/data/evaluation/solutions"


def get_solution_for_evaluation_path(instance_index: int = 0):
    """
    Returns the path of the solution for evaluation corresponding to the given instance index.
    NB: the solution for evaluation is assumed to be located in the evaluation directory.

    :param instance_index: the index of the instance for evaluation
    :return: the path of the solution for evaluation corresponding to the given instance index
    """
    if instance_index < 0 or instance_index >= len(INSTANCES_FOR_EVALUATION_NAMES):
        raise ValueError(f"The instance index {instance_index} is not valid, "
                         f"it must be between 0 and {len(INSTANCES_FOR_EVALUATION_NAMES) - 1}")
    return f"{get_solutions_for_evaluation_directory_path()}/solution_evaluation_{str(instance_index)}.txt"


def get_solution_for_evaluation(instance_index: int = 0):
    """
    Returns the solution for evaluation corresponding to the given instance index.
    NB: the solution for evaluation is assumed to be located in the evaluation directory.

    :param instance_index: the index of the instance for evaluation
    :return: the solution for evaluation corresponding to the given instance index
    """
    solution_path = get_solution_for_evaluation_path(instance_index)
    solution = extract_solution_from_file(solution_path, True, True, True)
    feasible, text = check_feasibility(solution)
    if not feasible:
        raise ValueError(f"The solution {solution.name} is not feasible: {text}")
    solution = SolutionForHeuristics.from_Solution(solution)
    solution.tighten_times()
    return solution


#########################################################################
# Reading explanations for evaluation (located in evaluation directory) #
#########################################################################


def get_explanations_for_evaluation_directory_path():
    """
    Returns the path of the directory containing the explanations for evaluation.

    :return: the path of the directory containing the explanations for evaluation
    """
    return get_project_directory_path() + "/data/evaluation/explanations"


def get_explanations_for_evaluation_path(instance_index: int = 0):
    """
    Returns the path of the explanations for evaluation corresponding to the given instance index.
    NB: the explanations for evaluation are assumed to be located in the evaluation directory.

    :param instance_index: the index of the instance for evaluation
    :return: the path of the explanations for evaluation corresponding to the given instance index
    """
    if instance_index < 0 or instance_index >= len(INSTANCES_FOR_EVALUATION_NAMES):
        raise ValueError(f"The instance index {instance_index} is not valid, "
                         f"it must be between 0 and {len(INSTANCES_FOR_EVALUATION_NAMES) - 1}")
    return f"{get_explanations_for_evaluation_directory_path()}/" \
           f"{define_multiple_contrastive_explanations_json_file_name(get_solution_for_evaluation(instance_index))}"
