# Local libraries
from main_configuration import *
from src.checking.feasibility import check_feasibility
from src.drawing.figuresmanager import FiguresManager
from src.reading.solution import extract_solution_from_file
from src.utils.display import print_title_frame
from src.utils.files import get_paths_of_solutions_files_in_given_directory
from src.writing.analysis import write_solution_analysis


########
# Main #
########

def analysis_main():
    """
    Main function of the analysis-relative part of the project.
    :return: None
    """

    # Extract the paths of all the solutions located in the default inputs directory
    solutions_files_paths = get_paths_of_solutions_files_in_given_directory()
    if len(solutions_files_paths) == 0:
        print("No solution file found in the default inputs directory")

    for solution_file_path in solutions_files_paths:

        # Extract the solution
        solution = extract_solution_from_file(solution_file_path)
        print_title_frame(f"Extraction of {solution.name}")
        print("")
        print(f"File path: {solution_file_path}")
        print(f"Name: {solution.name}")
        print("Extraction: done")
        print("")

        # Check the feasibility of the solution
        print_title_frame(f"Checking feasibility of {solution.name}")
        print("")
        feasible = check_feasibility(solution, covering=False)[0]
        solution.compute_KPIs()
        print("Checking: done")
        print("")

        # Show and save figures related to the solution
        if SHOW_SOLUTIONS_FIGURES or SAVE_SOLUTIONS_FIGURES:
            figures_manager = FiguresManager(solution)
            if SHOW_SOLUTIONS_FIGURES:
                print_title_frame(f"Representing {solution.name}")
                print("")
                figures_manager.show_figures()
                print("Representing: done")
                print("")
            if SAVE_SOLUTIONS_FIGURES:
                figures_manager.save_figures()

        # Write the analysis of the solution
        if feasible and WRITE_SOLUTIONS_ANALYSIS_INTO_FILES:
            print_title_frame(f"Writing analysis of {solution.name}")
            print("")
            write_solution_analysis(solution)
            print("Writing: done")

        print("")
        print("")
