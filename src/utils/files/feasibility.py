# Standard library
from typing import Optional

# Local libraries
from src.modeling.solution import Solution
from src.utils.constants import DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH
from src.utils.files.general import make_absolute_path_from_relative_one


###################################
# Solution feasibility check file #
###################################


def create_solution_feasibility_check_file_path(solution: Solution,
                                                 outputs_directory_relative_path: Optional[str] = None):
    """
    Creates a file path for the text file of the solution feasibility check.

    Args:
        solution: Solution to check.
        outputs_directory_relative_path: Relative path to the outputs directory. Defaults to
            DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH.

    Returns:
        The file path.
    """
    if outputs_directory_relative_path is None:
        outputs_directory_relative_path = DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH
    return make_absolute_path_from_relative_one(f"{outputs_directory_relative_path}/{solution.name}Checks.txt")


def create_multiple_solution_feasibility_checks_file_path(outputs_directory_relative_path: Optional[str] = None):
    """
    Creates a file path for the text file of multiple solution feasibility checks.

    Args:
        outputs_directory_relative_path: Relative path to the outputs directory. Defaults to
            DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH.

    Returns:
        The file path.
    """
    if outputs_directory_relative_path is None:
        outputs_directory_relative_path = DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH
    return make_absolute_path_from_relative_one(f"{outputs_directory_relative_path}/SolutionsChecks.txt")
