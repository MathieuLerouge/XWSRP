# Local libraries
from src.modeling.solution import Solution
from src.utils.constants import *
from src.utils.files import make_absolute_path_from_relative_one


############################
# Writing solution content #
############################

def write_solution(solution: Solution, outputs_directory_relative_path: str = None):
    """
    Write the solution to a .txt file.

    :param solution: the solution to write (Solution)
    :param outputs_directory_relative_path: the relative path of the directory where to write the solution (str)
    :return: None
    """

    # Open file name
    if outputs_directory_relative_path is None:
        outputs_directory_relative_path = DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH
    file_path = make_absolute_path_from_relative_one(f"{outputs_directory_relative_path}/{solution.name}.txt")
    file = open(file_path, "w")

    # Write solution's data about _tasks
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

    # Close file_name
    file.close()
