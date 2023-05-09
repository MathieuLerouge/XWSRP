# Local libraries
from main_configuration import MAIN_PROCESS, EXPLANATIONS_ANALYSIS_MAXIMUM_NUMBER_OF_EXPLANATIONS_PER_TEMPLATE, \
    MAIN_PROCESS_AMONG_EXPLAINER_ONES
from src.checking.feasibility import check_feasibility
from src.explaining.configuration import *
from src.explaining.processes import launch_explainer_UI_on_demo_solution, launch_explainer_UI_on_default_solution, \
    compute_computation_time_analysis_of_contrastive_explanations
from src.explaining.writing.explanation import export_contrastive_explanations_analysis_to_json_file
from src.reading.solution import extract_solution_from_file
from src.utils.constants import EXPLAINER_PROCESS_ON_DEMO_SOLUTION, EXPLAINER_PROCESS_ON_SOLUTION_IN_DEFAULT_INPUTS, \
    EXPLANATIONS_COMPUTATION_ANALYSIS_ON_SOLUTIONS_IN_DEFAULT_INPUTS, EXPLANATION_PROCESS
from src.utils.display import print_title_frame
from src.utils.files import get_paths_of_solutions_files_in_given_directory


########
# Main #
########


def explaining_main():
    """
    Main function of the explaining module
    There are two main processes:
    - launching the explainer UI on the demo solution
    - launching the explainer UI on the solution in the default inputs directory
    - computing the explanations analysis on the solutions in the default inputs directory

    :return: None
    """
    if MAIN_PROCESS == EXPLANATION_PROCESS:
        if MAIN_PROCESS_AMONG_EXPLAINER_ONES == EXPLAINER_PROCESS_ON_DEMO_SOLUTION:
            launch_explainer_UI_on_demo_solution(
                EXPLAINER_DEMO_SOLUTION_LANGUAGE, EXPLAINER_DEMO_SOLUTION_ENABLE_HISTORY,
                EXPLAINER_DEMO_SOLUTION_ENABLE_SCENARIO, EXPLAINER_DEMO_SOLUTION_ENABLE_COUNTERFACTUAL,
                EXPLAINER_DEMO_SOLUTION_ENABLE_USING_ALREADY_COMPUTED_CONTRASTIVE_EXPLANATIONS
            )
        elif MAIN_PROCESS_AMONG_EXPLAINER_ONES == EXPLAINER_PROCESS_ON_SOLUTION_IN_DEFAULT_INPUTS:
            launch_explainer_UI_on_default_solution(
                EXPLAINER_DEFAULT_SOLUTION_LANGUAGE, EXPLAINER_DEFAULT_SOLUTION_ENABLE_HISTORY,
                EXPLAINER_DEFAULT_SOLUTION_ENABLE_SCENARIO, EXPLAINER_DEFAULT_SOLUTION_ENABLE_COUNTERFACTUAL
            )
        elif MAIN_PROCESS_AMONG_EXPLAINER_ONES == EXPLANATIONS_COMPUTATION_ANALYSIS_ON_SOLUTIONS_IN_DEFAULT_INPUTS:
            solutions_files_paths = get_paths_of_solutions_files_in_given_directory()
            if len(solutions_files_paths) == 0:
                print("No solution file found in the default inputs directory")
            for solution_file_path in solutions_files_paths:
                solution = extract_solution_from_file(solution_file_path)
                feasible = check_feasibility(solution, covering=False)[0]
                print_title_frame(f"Extraction of {solution.name}")
                print("")
                print(f"File path: {solution_file_path}")
                print(f"Name: {solution.name}")
                print(f"Feasible: {feasible}")
                print("Extraction: done")
                print("")
                if feasible:
                    print_title_frame(f"Contrastive explanations computation time analysis of {solution.name}")
                    print("")
                    solution.compute_KPIs()
                    explanations_analysis = compute_computation_time_analysis_of_contrastive_explanations(
                        solution, maximum_number_of_explanations_per_template=
                        EXPLANATIONS_ANALYSIS_MAXIMUM_NUMBER_OF_EXPLANATIONS_PER_TEMPLATE)
                    export_contrastive_explanations_analysis_to_json_file(solution, explanations_analysis)
                    print(f"")
                    print("")
        else:
            raise Exception(f"Unknown main process among explainer ones: {MAIN_PROCESS_AMONG_EXPLAINER_ONES}")
    else:
        raise ValueError(f"The process {MAIN_PROCESS} is not an explainer process")


if __name__ == '__main__':
    explaining_main()
