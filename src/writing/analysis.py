# Local libraries
from src.modeling.solution import Solution
from src.optimization.solution import SolutionOpti
from src.utils.constants import OUTPUTS_DIRECTORY_RELATIVE_PATH, SOLUTION_ANALYSIS_FILE_NAME_SUFFIX, LINE_BREAK_STRING
from src.utils.files import make_absolute_path_from_relative_one


#############################
# Writing solution analysis #
#############################

def write_solution_analysis(solution: Solution, outputs_directory_relative_path: str = None):
    """
    Write the solution analysis to a .txt file.

    :param solution: the solution to write about (Solution)
    :param outputs_directory_relative_path: the relative path of the directory where to write the solution analysis
    (str)
    :return: None
    """

    # Open file_name
    if outputs_directory_relative_path is None:
        outputs_directory_relative_path = OUTPUTS_DIRECTORY_RELATIVE_PATH
    file_name = f"{solution.name}{SOLUTION_ANALYSIS_FILE_NAME_SUFFIX}.txt"
    file_path = make_absolute_path_from_relative_one(f"{outputs_directory_relative_path}/{file_name}")
    file = open(file_path, "w")

    # Write solution performances indicators
    if not solution.has_KPIs:
        solution.compute_KPIs()
    file.write("Number of performed tasks: " + str(solution.nb_performed_tasks) + LINE_BREAK_STRING)
    file.write("Total working duration (in min): " + str(solution.total_working_duration) + LINE_BREAK_STRING)
    file.write("Total traveling duration (in min): " + str(solution.total_traveling_duration) + LINE_BREAK_STRING)
    file.write("Total traveling distance (in km): " + str(solution.total_traveling_distance) + LINE_BREAK_STRING)
    file.write("Total idle time (in min): " + str(solution.total_idle_time) + LINE_BREAK_STRING)
    file.write(LINE_BREAK_STRING)

    # Write about solving method
    if isinstance(solution, SolutionOpti):
        file.write("Optimization method id: " + str(solution.solving_method_id) + LINE_BREAK_STRING)
        file.write("Optimization run time (in s): " + str(solution.solving_time) + LINE_BREAK_STRING)
        if solution.solving_method_parameters is not None:
            file.write("Objective function parameters: " + str(solution.solving_method_parameters) + LINE_BREAK_STRING)
        if solution.optimality_gap is not None:
            file.write("Optimality gap (in %): " + str(solution.optimality_gap*100) + LINE_BREAK_STRING)
        if solution.objective_value is not None:
            file.write("Objective value: " + str(solution.objective_value) + LINE_BREAK_STRING)
        file.write(LINE_BREAK_STRING)

    # Write about employees sequences
    file.write(str(solution))

    # Close file_name
    file.close()
