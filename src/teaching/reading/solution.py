# Standard library
from os import path

# Local libraries
from src.reading.solution import complete_solution_from_file
from src.teaching.optimization.solution import SolutionForTeaching
from src.teaching.reading.instance import extract_teaching_instance_from_file
from src.utils.constants import META_DATA_SOLVING_METHOD_KEY
from src.utils.files import find_instance_file_path_corresponding_to_solution, identify_meta_data_in_solution_file_path


def extract_solution_for_teaching_from_file(solution_file_path: str):
    """
    Extract a teaching solution from the path of a solution file.

    :param solution_file_path: the path of the solution file (str)
    :return: the teaching solution (SolutionForTeaching)
    """
    if not path.exists(solution_file_path):
        raise FileNotFoundError(f"The given solution file {solution_file_path} does not exists")
    instance_file_path = find_instance_file_path_corresponding_to_solution(solution_file_path)
    instance = extract_teaching_instance_from_file(instance_file_path)
    meta_data = identify_meta_data_in_solution_file_path(solution_file_path)
    solution = SolutionForTeaching(instance, solving_method_id=meta_data[META_DATA_SOLVING_METHOD_KEY])
    return complete_solution_from_file(solution, solution_file_path)
