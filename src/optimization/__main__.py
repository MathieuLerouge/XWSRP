# Standard libraries
import time
import numpy as np

# Local libraries
from main_configuration import *
from src.checking.feasibility import check_feasibility
from src.drawing.figuresmanager import FiguresManager
from src.optimization.heuristics.greedy import run_greedy_algorithm
from src.optimization.heuristics.neighborhood_search import run_neighborhood_search
from src.optimization.heuristics.solution import SolutionForHeuristics
from src.optimization.heuristics.stochastic import run_stochastic_heuristic
from src.reading.instance import extract_instance_from_file
from src.reading.solution import extract_solution_from_file
from src.utils.display import print_title_frame
from src.utils.files import get_paths_of_instances_files_in_given_directory, \
    get_paths_of_solutions_files_in_given_directory
from src.writing.analysis import write_solution_analysis
from src.writing.solution import write_solution


########
# Main #
########

def optimization_main():
    """
    Main function of the optimization-relative part of the project.
    There are various solving processes:
    - greedy algorithm;
    - stochastic heuristic algorithm;
    - simulated annealing algorithm;
    - variable neighborhood search algorithm.
    There are various
    :return: None
    """
    if MAIN_PROCESS == RUN_OPTIMIZATION_PROCESS:

        # Extract the paths of all the instances located in the default inputs directory
        instances_files_paths = get_paths_of_instances_files_in_given_directory()
        if len(instances_files_paths) == 0:
            print("No instance file found in the default inputs directory")

        for instance_file_path in instances_files_paths:

            # Extract each instance data
            instance = extract_instance_from_file(instance_file_path)
            print_title_frame(f"Extraction of {instance.name}")
            print("")
            print(f"File path: {instance_file_path}")
            print(f"Name: {instance.name}")
            print(f"Nb employees: {instance.nb_employees}")
            print(f"Nb tasks: {instance.nb_tasks}")
            print("Extraction: done")
            print("")

            # Solve each instance
            start = time.time()
            # - Using the greedy algorithm
            if MAIN_PROCESS_AMONG_OPTIMIZATION_ONES == RUN_GREEDY_ALGORITHM_AS_OPTIMIZATION_PROCESS:
                print_title_frame(f"Solving of {instance.name} using greedy algorithm")
                print("")
                solution = run_greedy_algorithm(instance)
            # - Using the stochastic heuristic algorithm
            elif MAIN_PROCESS_AMONG_OPTIMIZATION_ONES == RUN_STOCHASTIC_HEURISTIC_AS_OPTIMIZATION_PROCESS:
                # Solution computation
                print_title_frame(f"Solving of {instance.name} using stochastic heuristic algorithm")
                print("")
                start = time.time()
                solution = run_stochastic_heuristic(instance)
                end = time.time()
                solving_time_in_seconds = np.ceil(end - start)
                feasible = check_feasibility(solution, covering=False)[0]
                print(f"Feasible solution: {feasible}")
                print(f"Solving time: {solving_time_in_seconds}s = "
                      f"{solving_time_in_seconds // 60}min {solving_time_in_seconds % 60}s")
                print("Solving: done")
                print("")
            # -Using the variable neighborhood search algorithm
            elif MAIN_PROCESS_AMONG_OPTIMIZATION_ONES == RUN_NEIGHBORHOOD_SEARCH_AS_OPTIMIZATION_PROCESS:
                # Solution computation
                print_title_frame(f"Solving of {instance.name} using variable neighborhood search algorithm")
                print("")
                solution = run_neighborhood_search(instance)
            else:
                raise ValueError(f"The process {MAIN_PROCESS_AMONG_OPTIMIZATION_ONES} is not an optimizing process")
            end = time.time()
            solving_time_in_seconds = int(np.ceil(end - start))
            feasible = check_feasibility(solution, covering=False)[0]
            print(f"Feasible solution: {feasible}")
            print(f"Solving time: {solving_time_in_seconds}s = "
                  f"{solving_time_in_seconds // 60}min {solving_time_in_seconds % 60}s")
            print("Solving: done")
            print("")

            # Solution writing
            print_title_frame(f"Writing down {solution.name}")
            print("")
            write_solution(solution)
            if OPTIMIZATION_PROCESS_WRITE_SOLUTIONS_ANALYSIS_INTO_FILES:
                write_solution_analysis(solution)
            print(f"Nb performed tasks: {solution.nb_performed_tasks}/{instance.nb_tasks}")
            print(f"Total working duration: {solution.total_working_duration}")
            print(f"Total traveling duration: {solution.total_traveling_duration}")
            print("Writing: done")
            print("")

            # Solution representation
            print_title_frame(f"Representation of {solution.name}")
            print("")
            figures_manager = FiguresManager(solution)
            if OPTIMIZATION_PROCESS_SHOW_SOLUTIONS_FIGURES:
                figures_manager.show_figures()
            if OPTIMIZATION_PROCESS_SAVE_SOLUTIONS_FIGURES:
                figures_manager.save_figures()
            print("Representation: done")
            print("")

    elif MAIN_PROCESS == RUN_REOPTIMIZATION_PROCESS:

        # Extract the paths of all the solutions located in the default inputs directory
        solutions_files_paths = get_paths_of_solutions_files_in_given_directory()
        if len(solutions_files_paths) == 0:
            print("No solution file found in the default inputs directory")

        for solution_file_path in solutions_files_paths:

            # Extract each solution data
            initial_solution = extract_solution_from_file(solution_file_path)
            initial_solution.compute_KPIs()
            print_title_frame(f"Extraction of {initial_solution.name}")
            print("")
            print(f"File path: {solution_file_path}")
            print(f"Name: {initial_solution.name}")
            print(f"Instance name: {initial_solution.name}")
            print(f"Nb employees: {initial_solution.instance.nb_employees}")
            print(f"Nb tasks: {initial_solution.instance.nb_tasks}")
            print(f"Nb performed tasks: {initial_solution.nb_performed_tasks}")
            print(f"Total working duration: {initial_solution.total_working_duration}")
            print(f"Total traveling duration: {initial_solution.total_traveling_duration}")
            print("Extraction: done")
            print("")

            # Reoptimize each solution
            start = time.time()
            # - Using the variable neighborhood search algorithm
            if MAIN_PROCESS_AMONG_REOPTIMIZATION_ONES == RUN_NEIGHBORHOOD_SEARCH_AS_OPTIMIZATION_PROCESS:
                print_title_frame(f"Reoptimizing of {initial_solution.name} "
                                  f"using variable neighborhood search algorithm")
                print("")
                solution = SolutionForHeuristics.from_Solution(initial_solution)
                print("New solution:", solution.name)
                solution = run_neighborhood_search(solution.instance, solution)
            else:
                raise ValueError(f"The process {MAIN_PROCESS_AMONG_REOPTIMIZATION_ONES} is not a reoptimizing process")
            end = time.time()
            solving_time_in_seconds = int(np.ceil(end - start))
            feasible = check_feasibility(solution, covering=False)[0]
            print(f"Feasible solution: {feasible}")
            print(f"Solving time: {solving_time_in_seconds}s = "
                  f"{solving_time_in_seconds // 60}min {solving_time_in_seconds % 60}s")
            print("Solving: done")
            print("")

            # Solution writing
            print_title_frame(f"Comparison of {solution.name} with initial_solution {initial_solution.name}")
            print("")
            instance = solution.instance
            relative_change_in_nb_performed_tasks = np.round(
                (solution.nb_performed_tasks - initial_solution.nb_performed_tasks) /
                initial_solution.nb_performed_tasks, 4)
            print(f"Nb performed tasks: in new solution, {solution.nb_performed_tasks}/{instance.nb_tasks} | "
                  f"in initial solution {initial_solution.nb_performed_tasks}/{instance.nb_tasks} | "
                  f"relative change of {relative_change_in_nb_performed_tasks * 100}%")
            relative_change_in_total_working_duration = np.round(
                (solution.total_working_duration - initial_solution.total_working_duration) /
                initial_solution.total_working_duration, 4)
            print(f"Total working time: in new solution, {solution.total_working_duration} | "
                  f"in initial solution, {initial_solution.total_working_duration} | "
                  f"relative change of {relative_change_in_total_working_duration * 100}%")
            relative_change_in_total_traveling_duration = np.round(
                (solution.total_traveling_duration - initial_solution.total_traveling_duration) /
                initial_solution.total_traveling_duration, 4)
            print(f"Total travel time: in new solution, {solution.total_traveling_duration} | "
                  f"in initial solution, {initial_solution.total_traveling_duration} | "
                  f"relative change of {relative_change_in_total_traveling_duration * 100}%")
            print("Comparison: done")
            print("")

            # Solution writing
            print_title_frame(f"Writing down {solution.name}")
            print("")
            write_solution(solution)
            if OPTIMIZATION_PROCESS_WRITE_SOLUTIONS_ANALYSIS_INTO_FILES:
                write_solution_analysis(solution)
            print(f"Nb performed tasks: {solution.nb_performed_tasks}/{solution.instance.nb_tasks}")
            print(f"Total working duration: {solution.total_working_duration}")
            print(f"Total traveling duration: {solution.total_traveling_duration}")
            print("Writing: done")
            print("")

            # Solution representation
            print_title_frame(f"Representation of {solution.name}")
            print("")
            figures_manager = FiguresManager(solution)
            if OPTIMIZATION_PROCESS_SHOW_SOLUTIONS_FIGURES:
                figures_manager.show_figures()
            if OPTIMIZATION_PROCESS_SAVE_SOLUTIONS_FIGURES:
                figures_manager.save_figures()
            print("Representation: done")
            print("")

    else:
        raise ValueError(f"The process {MAIN_PROCESS} is not an optimizing process")


if __name__ == '__main__':
    optimization_main()
