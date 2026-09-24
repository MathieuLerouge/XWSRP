# Standard libraries
import json
from os import path
from typing import Optional

# Local libraries
from src.optimization.heuristics.solution import SolutionForHeuristics
from src.importing.instance import extract_instance_from_file
from src.modeling.instance import Instance
from src.modeling.solution import Solution, INSTANCE_KEY
from src.utils.constants import META_DATA_CORE_KEY, SOLUTION_NAME_PREFIX, META_DATA_SOLVING_METHOD_KEY, \
    HEURISTICS_SOLVING_METHODS, JSON_FILE_EXTENSION, SOLUTION_FILE_EXTENSION
from src.utils.files import find_instance_file_path_corresponding_to_solution, \
    identify_meta_data_in_solution_file_path, does_solution_file_path_mention_solving_method, \
    get_solving_method_in_solution_file_path
from src.utils.time import convert_time_string_to_nb_minutes


###########
# Helpers #
###########

def find_instance_of_solution_file(
        solution_file_path: str, ignore_employees_unavailabilities: bool = False,
        ignore_tasks_unavailabilities: bool = False, ignore_lunch_breaks: bool = False
) -> Instance:
    """
    Extracts the instance that the given solution file is a solution of.

    The instance file is located from the solution file's own name, which records the instance's core name and version.

    Args:
        solution_file_path: The path of the solution file.
        ignore_employees_unavailabilities: Whether the employees' unavailabilities must be ignored.
        ignore_tasks_unavailabilities: Whether the tasks' unavailabilities must be ignored.
        ignore_lunch_breaks: Whether the lunch breaks must be ignored.

    Returns:
        The instance the solution is built for.

    Raises:
        FileNotFoundError: If the given solution file does not exist.
    """
    if not path.exists(solution_file_path):
        raise FileNotFoundError(f"The given solution file {solution_file_path} does not exists")
    instance_file_path = find_instance_file_path_corresponding_to_solution(solution_file_path)
    return extract_instance_from_file(
        instance_file_path, ignore_employees_unavailabilities, ignore_tasks_unavailabilities, ignore_lunch_breaks
    )


def initialize_solution_from_file(
        solution_file_path: str, ignore_employees_unavailabilities: bool = False,
        ignore_tasks_unavailabilities: bool = False, ignore_lunch_breaks: bool = False
):
    """
    Creates an empty solution of the instance that the given solution file is a solution of.

    The returned solution has no task performed yet: it is meant to be filled in by complete_solution_from_file.

    Args:
        solution_file_path: The path of the solution file.
        ignore_employees_unavailabilities: Whether the employees' unavailabilities must be ignored.
        ignore_tasks_unavailabilities: Whether the tasks' unavailabilities must be ignored.
        ignore_lunch_breaks: Whether the lunch breaks must be ignored.

    Returns:
        The empty solution, named after the solution file.
    """
    instance = find_instance_of_solution_file(
        solution_file_path, ignore_employees_unavailabilities, ignore_tasks_unavailabilities, ignore_lunch_breaks
    )
    meta_data = identify_meta_data_in_solution_file_path(solution_file_path)
    solution = Solution(instance, SOLUTION_NAME_PREFIX + meta_data[META_DATA_CORE_KEY])
    return solution


def complete_solution_from_file(solution: Solution, solution_file_path: str):
    """
    Fills in the given solution with the tasks performances recorded in the given .txt file.

    Args:
        solution: The solution to fill in, which must be a solution of the instance the file refers to.
        solution_file_path: The path of the solution file.

    Returns:
        The filled-in solution, whose sequences have been recomputed from its tasks performances.

    Raises:
        ValueError: If the file mentions a task that is not among the instance's tasks.
    """
    # Define some variable
    instance = solution.instance
    # Read lines of the solution file
    with open(solution_file_path, 'r') as file:
        file_lines = [line for line in file]
    # Check the header of the paragraph about tasks
    line_index = 0
    first_word = file_lines[line_index].split(';')[0]
    if first_word != "taskId":
        if first_word in instance.tasks_names:
            print("The header of the paragraph about tasks is missing")
        else:
            print("The header of the paragraph about tasks is wrong")
            line_index += 1
    else:
        line_index += 1
    # Read the data in paragraph about tasks
    while (line_index < len(file_lines)) and (len(file_lines[line_index]) > 4):
        words = file_lines[line_index].split(';')
        task_name = words[0]
        if not (task_name in instance.tasks_names):
            raise ValueError(f"The task {task_name} is not in the tasks set")
        else:
            task = instance.get_task_by_name(task_name)
            task_is_realized = int(words[1]) == 1
            solution.set_task_performance_status(task, task_is_realized)
            if task_is_realized:
                solution.set_task_assignee(task, instance.get_employee_by_name(words[2]))
                if not (":" in words[3]):
                    solution.set_task_start_time(task, int(float(words[3])))
                else:
                    print("The format of the tasks' start times is wrong")
                    solution.set_task_start_time(task, convert_time_string_to_nb_minutes(words[3]))
        line_index += 1
    solution.compute_sequences_based_on_tasks_performances()
    return solution


def extract_solution_for_heuristics_from_file(solution_file_path: str):
    """
    Extracts a solution for heuristics from the path of a solution file.

    Args:
        solution_file_path: The path of the solution file, whose name must mention the solving method.

    Returns:
        The solution for heuristics.
    """
    instance = find_instance_of_solution_file(solution_file_path)
    meta_data = identify_meta_data_in_solution_file_path(solution_file_path)
    solution = SolutionForHeuristics(instance, heuristic_id=meta_data[META_DATA_SOLVING_METHOD_KEY])
    return complete_solution_from_file(solution, solution_file_path)


###########################
# Import from a json file #
###########################

def import_solution_from_json_file(
        solution_file_path: str, instance: Optional[Instance] = None, ignore_employees_unavailabilities: bool = False,
        ignore_tasks_unavailabilities: bool = False, ignore_lunch_breaks: bool = False
) -> Solution:
    """
    Imports the solution stored in the given .json file.

    The instance the solution is built for is taken from the instance argument if one is given, then from the
    instance embedded in the file if it holds one, and otherwise from the instance file that the solution
    file's name points to.

    Args:
        solution_file_path: The path of the solution file, extension included.
        instance: The instance the solution is built for. Defaults to the instance embedded in the file, or,
            failing that, to the one extracted from the corresponding instance file.
        ignore_employees_unavailabilities: Whether the employees' unavailabilities must be ignored. Only used
            when the instance has to be extracted from its own file.
        ignore_tasks_unavailabilities: Whether the tasks' unavailabilities must be ignored. Only used when the
            instance has to be extracted from its own file.
        ignore_lunch_breaks: Whether the lunch breaks must be ignored. Only used when the instance has to be
            extracted from its own file.

    Returns:
        The imported solution.

    Raises:
        FileNotFoundError: If the given file path does not have a json extension.
    """
    if JSON_FILE_EXTENSION not in solution_file_path:
        raise FileNotFoundError(f"The given file path {solution_file_path} does not have a json extension")
    with open(solution_file_path) as json_file:
        solution_dictionary = json.load(json_file)
    if instance is None and INSTANCE_KEY not in solution_dictionary:
        instance = find_instance_of_solution_file(
            solution_file_path, ignore_employees_unavailabilities, ignore_tasks_unavailabilities,
            ignore_lunch_breaks
        )
    return Solution.from_dict(solution_dictionary, instance)


##########################
# Import from a txt file #
##########################

def import_solution_from_txt_file(
        solution_file_path: str, ignore_employees_unavailabilities: bool = False,
        ignore_tasks_unavailabilities: bool = False, ignore_lunch_breaks: bool = False
) -> Solution:
    """
    Imports the solution stored in the given .txt file.

    The instance the solution is built for is extracted from the instance file that the solution file's name
    points to.

    Args:
        solution_file_path: The path of the solution file, extension included.
        ignore_employees_unavailabilities: Whether the employees' unavailabilities must be ignored.
        ignore_tasks_unavailabilities: Whether the tasks' unavailabilities must be ignored.
        ignore_lunch_breaks: Whether the lunch breaks must be ignored.

    Returns:
        The imported solution, as a SolutionForHeuristics when the file's name mentions a heuristic solving
        method, and as a plain Solution otherwise.
    """
    if does_solution_file_path_mention_solving_method(solution_file_path):
        solving_method = get_solving_method_in_solution_file_path(solution_file_path)
        if solving_method in HEURISTICS_SOLVING_METHODS:
            return extract_solution_for_heuristics_from_file(solution_file_path)
    solution = initialize_solution_from_file(solution_file_path, ignore_employees_unavailabilities,
                                             ignore_tasks_unavailabilities, ignore_lunch_breaks)
    return complete_solution_from_file(solution, solution_file_path)


####################################
# Import from a json or a txt file #
####################################

def import_solution(
        solution_file_path: str, instance: Optional[Instance] = None, ignore_employees_unavailabilities: bool = False,
        ignore_tasks_unavailabilities: bool = False, ignore_lunch_breaks: bool = False
) -> Solution:
    """
    Imports the solution stored in the given file, which may be a .json or a .txt one.

    Args:
        solution_file_path: The path of the solution file, extension included.
        instance: The instance the solution is built for. Only used for a .json file, whose .txt counterpart
            has no way of carrying an instance.
        ignore_employees_unavailabilities: Whether the employees' unavailabilities must be ignored.
        ignore_tasks_unavailabilities: Whether the tasks' unavailabilities must be ignored.
        ignore_lunch_breaks: Whether the lunch breaks must be ignored.

    Returns:
        The imported solution.

    Raises:
        ValueError: If the file is neither a json nor a txt one.
    """
    if JSON_FILE_EXTENSION in solution_file_path:
        return import_solution_from_json_file(solution_file_path, instance, ignore_employees_unavailabilities,
                                              ignore_tasks_unavailabilities, ignore_lunch_breaks)
    elif SOLUTION_FILE_EXTENSION in solution_file_path:
        return import_solution_from_txt_file(solution_file_path, ignore_employees_unavailabilities,
                                             ignore_tasks_unavailabilities, ignore_lunch_breaks)
    else:
        raise ValueError("The file must be a JSON or TXT file")
