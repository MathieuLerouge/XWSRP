# Local libraries
from src.modeling.solution import Solution
from src.utils.constants import *


def write_solution(solution: Solution, output_directory: str = None):

    # Open file name
    if output_directory is None:
        output_directory = OUTPUTS_DIRECTORY
    file_name = output_directory + "/" + solution.name + ".txt"
    file = open(file_name, "w")

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
