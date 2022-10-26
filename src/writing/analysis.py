# Local libraries
from src.modeling.solution import Solution
from src.optimization.solution import SolutionOpti
from src.utils.constants import OUTPUTS_DIRECTORY_RELATIVE_PATH, SOLUTION_ANALYSIS_FILE_NAME_SUFFIX, LINE_BREAK_STRING


def write_solution_analysis(solution: Solution, output_directory: str = None):

    # Open file_name
    if output_directory is None:
        output_directory = OUTPUTS_DIRECTORY_RELATIVE_PATH
    file_name = output_directory + "/" + solution.name + SOLUTION_ANALYSIS_FILE_NAME_SUFFIX + ".txt"
    file = open(file_name, "w")

    # Write solution performances indicators
    if not solution.has_KPIs:
        solution.compute_KPIs()
    file.write("Number of realized tasks: " + str(solution.nb_performed_tasks) + LINE_BREAK_STRING)
    file.write("Total working duration (in min): " + str(solution.total_working_duration) + LINE_BREAK_STRING)
    file.write("Total traveling duration (in min): " + str(solution.total_traveling_duration) + LINE_BREAK_STRING)
    file.write("Total traveling distance (in km): " + str(solution.total_traveling_distance) + LINE_BREAK_STRING)
    file.write("Total idle time (in min): " + str(solution.total_idle_time) + LINE_BREAK_STRING)
    file.write(LINE_BREAK_STRING)

    # Write about solving method
    if isinstance(solution, SolutionOpti):
        file.write("Optimization method id: " + str(solution.solving_method_id) + LINE_BREAK_STRING)
        file.write("Optimization run time (in s): " + str(solution.solving_time) + LINE_BREAK_STRING)
        if solution.solving_method_id in ["V1", "V2"]:
            file.write("Objective function parameters: " + str(solution.solving_method_parameters) + LINE_BREAK_STRING)
            file.write("Optimality gap (in %): " + str(solution.optimality_gap*100) + LINE_BREAK_STRING)
            file.write("Objective value: " + str(solution.objective_value) + LINE_BREAK_STRING)
        file.write(LINE_BREAK_STRING)

    # Write about _employees' sequences
    file.write(str(solution))

    # Close file_name
    file.close()
