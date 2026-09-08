# Local libraries
from main_configuration import MAIN_PROCESS, EXPLANATIONS_ANALYSIS_MAXIMUM_NUMBER_OF_EXPLANATIONS_PER_TEMPLATE, \
    MAIN_PROCESS_AMONG_EXPLAINER_ONES
from src.checking.feasibility import check_feasibility
from src.explaining.configuration import *
from src.explaining.processes import launch_explainer_UI_on_demo_solution, launch_explainer_UI_on_default_solution, \
    compute_computation_time_analysis_of_explanations
from src.explaining.questioning.question import ContrastiveQuestion, CounterfactualQuestion
from src.explaining.writing.explanation import export_explanations_analysis_to_json_file
from src.reading.solution import extract_solution_from_file
from src.utils.constants import RUN_EXPLAINER_ON_DEMO_SOLUTION_AS_EXPLANATION_PROCESS, \
    RUN_EXPLAINER_ON_GIVEN_SOLUTION_AS_EXPLANATION_PROCESS, \
    RUN_EXPLANATION_COMPUTATION_ANALYSIS_AS_EXPLANATION_PROCESS, RUN_EXPLANATION_PROCESS, \
    RUN_COUNTERFACTUAL_EXPLANATION_COMPUTATION_ANALYSIS_AS_EXPLANATION_PROCESS
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
    if MAIN_PROCESS == RUN_EXPLANATION_PROCESS:

        # Launch the explainer UI on the demo solution
        if MAIN_PROCESS_AMONG_EXPLAINER_ONES == RUN_EXPLAINER_ON_DEMO_SOLUTION_AS_EXPLANATION_PROCESS:
            launch_explainer_UI_on_demo_solution(
                EXPLAINER_DEMO_SOLUTION_LANGUAGE, EXPLAINER_DEMO_SOLUTION_ENABLE_HISTORY,
                EXPLAINER_DEMO_SOLUTION_ENABLE_SCENARIO, EXPLAINER_DEMO_SOLUTION_ENABLE_COUNTERFACTUAL,
                EXPLAINER_DEMO_SOLUTION_ENABLE_USING_ALREADY_COMPUTED_CONTRASTIVE_EXPLANATIONS
            )

        # Launch the explainer UI on the solution in the default inputs directory
        elif MAIN_PROCESS_AMONG_EXPLAINER_ONES == RUN_EXPLAINER_ON_GIVEN_SOLUTION_AS_EXPLANATION_PROCESS:
            launch_explainer_UI_on_default_solution(
                EXPLAINER_DEFAULT_SOLUTION_LANGUAGE, EXPLAINER_DEFAULT_SOLUTION_ENABLE_HISTORY,
                EXPLAINER_DEFAULT_SOLUTION_ENABLE_SCENARIO, EXPLAINER_DEFAULT_SOLUTION_ENABLE_COUNTERFACTUAL
            )

        # Compute the explanations analysis on the solutions in the default inputs directory
        elif MAIN_PROCESS_AMONG_EXPLAINER_ONES in \
                [RUN_EXPLANATION_COMPUTATION_ANALYSIS_AS_EXPLANATION_PROCESS,
                 RUN_COUNTERFACTUAL_EXPLANATION_COMPUTATION_ANALYSIS_AS_EXPLANATION_PROCESS]:

            # Extract the solutions from the input directory
            solutions_files_paths = get_paths_of_solutions_files_in_given_directory()
            if len(solutions_files_paths) == 0:
                print("No solution file found in the default inputs directory")

            # Run and save explanation analysis for each solution file
            for solution_file_path in solutions_files_paths:

                # Extract solution from file
                solution = extract_solution_from_file(solution_file_path)
                feasible = check_feasibility(solution, covering=False)[0]
                if feasible:
                    solution.compute_kpis()
                print_title_frame(f"Extraction of {solution.name}")
                print("")
                print(f"File path: {solution_file_path}")
                print(f"Name: {solution.name}")
                print(f"Feasible: {feasible}")
                print(f"Number of employees: {solution.instance.nb_employees}")
                print(f"Number of tasks: {solution.instance.nb_tasks}")
                print(f"Number of non-performed tasks: {solution.nb_non_performed_tasks}")
                print("Extraction: done")
                print("")

                # Run explanation analysis only if the solution is feasible
                if feasible: # and solution.nb_non_performed_tasks < 550: # 280 <

                    # Define the type of explanations to analyze
                    if MAIN_PROCESS_AMONG_EXPLAINER_ONES == \
                            RUN_EXPLANATION_COMPUTATION_ANALYSIS_AS_EXPLANATION_PROCESS:
                        question_type = ContrastiveQuestion
                    else:
                        question_type = CounterfactualQuestion

                    # Run explanation analysis
                    print_title_frame(f"{'Contrastive' if question_type == ContrastiveQuestion else 'Counterfactual'} "
                                      f"explanations computation time analysis of {solution.name}")
                    print("")
                    explanations_analysis = compute_computation_time_analysis_of_explanations(
                        solution, maximum_number_of_explanations_per_template=
                        EXPLANATIONS_ANALYSIS_MAXIMUM_NUMBER_OF_EXPLANATIONS_PER_TEMPLATE,
                        question_type=question_type)

                    # Save explanation analysis
                    export_explanations_analysis_to_json_file(solution, explanations_analysis, question_type)
                    print(f"")
                    print("")

        else:
            raise Exception(f"Unknown main process among explainer ones: {MAIN_PROCESS_AMONG_EXPLAINER_ONES}")
    else:
        raise ValueError(f"The process {MAIN_PROCESS} is not an explainer process")


if __name__ == '__main__':
    explaining_main()
