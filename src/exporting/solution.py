# Standard libraries
import json
from typing import Optional

# Local libraries
from src.modeling.solution import Solution
from src.utils.constants import *
from src.utils.files import make_absolute_path_from_relative_one


##########################
# Export as a json file  #
##########################

def export_solution_as_json_file(
        solution: Solution, outputs_directory_relative_path: Optional[str] = None,
        with_sequences: bool = False, with_kpis: bool = False, with_instance: bool = False
) -> str:
    """
    Exports the solution to a .json file named after the solution.

    Args:
        solution: The solution to export.
        outputs_directory_relative_path: The relative path of the directory where to export the solution.
            Defaults to the project's default outputs directory.
        with_sequences: If True, also record each employee's ordered list of performed task names.
        with_kpis: If True, also record the solution's KPIs.
        with_instance: If True, also embed the whole instance, so that the exported file is self-contained
            and can be imported back without access to the instance's own file.

    Returns:
        The path of the exported file.
    """
    file_path = _create_solution_file_path(solution, outputs_directory_relative_path, JSON_FILE_EXTENSION)
    solution_dictionary = solution.to_dict(
        with_sequences=with_sequences, with_kpis=with_kpis, with_instance=with_instance
    )
    with open(file_path, "w") as file:
        json.dump(solution_dictionary, file, indent=4)
    return file_path


#########################
# Export as a txt file  #
#########################

def export_solution_as_txt_file(solution: Solution, outputs_directory_relative_path: Optional[str] = None) -> str:
    """
    Exports the solution to a .txt file named after the solution.

    The file holds one semicolon-separated line per task of the instance, recording whether the task is performed and,
    when it is, its assignee and its start time in minutes since midnight.

    Args:
        solution: The solution to export.
        outputs_directory_relative_path: The relative path of the directory where to export the solution.
            Defaults to the project's default outputs directory.

    Returns:
        The path of the exported file.
    """
    file_path = _create_solution_file_path(solution, outputs_directory_relative_path, SOLUTION_FILE_EXTENSION)
    with open(file_path, "w") as file:
        file.write("taskId;performed;employee_name;start_time;" + LINE_BREAK_STRING)
        for task in solution.instance.tasks:
            line_string = task.name + ";"
            if solution.get_task_performance_status(task):
                line_string += "1;"
                line_string += solution.get_task_assignee(task).name + ";"
                line_string += str(solution.get_task_start_time(task)) + ";"
            else:
                line_string += "0;;;"
            file.write(line_string + LINE_BREAK_STRING)
    return file_path


###################################
# Export as a json or a txt file  #
###################################

def export_solution(
        solution: Solution, outputs_directory_relative_path: Optional[str] = None, as_json: bool = True,
        with_sequences: bool = False, with_kpis: bool = False, with_instance: bool = False
) -> str:
    """
    Exports the solution to a .json file, or to a .txt one.

    Args:
        solution: The solution to export.
        outputs_directory_relative_path: The relative path of the directory where to export the solution.
            Defaults to the project's default outputs directory.
        as_json: If True, export as a .json file. If False, export as a .txt file, which records nothing
            beyond the tasks performances, and so ignores the three options below.
        with_sequences: If True, also record each employee's ordered list of performed task names.
        with_kpis: If True, also record the solution's KPIs.
        with_instance: If True, also embed the whole instance, so that the exported file is self-contained
            and can be imported back without access to the instance's own file.

    Returns:
        The path of the exported file.
    """
    if as_json:
        return export_solution_as_json_file(
            solution, outputs_directory_relative_path, with_sequences, with_kpis, with_instance
        )
    return export_solution_as_txt_file(solution, outputs_directory_relative_path)


def _create_solution_file_path(
        solution: Solution, outputs_directory_relative_path: Optional[str], file_extension: str
) -> str:
    """
    Returns the absolute path of the file to export the given solution to.

    Args:
        solution: The solution to export.
        outputs_directory_relative_path: The relative path of the directory where to export the solution.
            Defaults to the project's default outputs directory.
        file_extension: The extension of the file, leading dot included.

    Returns:
        The absolute path of the file.
    """
    if outputs_directory_relative_path is None:
        outputs_directory_relative_path = DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH
    return make_absolute_path_from_relative_one(
        f"{outputs_directory_relative_path}/{solution.name}{file_extension}"
    )
