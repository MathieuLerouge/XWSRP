# Local libraries
from src.evaluation.constants import *
from src.evaluation.data_preparation import get_instance_for_evaluation_in_default_inputs_directory, \
    compute_solution_for_evaluation_by_ILP_optimization, get_solution_for_evaluation_in_default_inputs_directory, \
    check_explanations_negativity, compute_and_export_contrastive_explanations
from src.evaluation.user_interface_with_prepared_data import \
    prepare_explainer_GUI_for_evaluation_given_experiment_version
from src.optimization.localsearch.solution import SolutionLS
from src.optimization.localsearch.solving import run_simulated_annealing
from src.utils.files import get_default_inputs_directory_path, get_default_outputs_directory_path
from src.writing.solution import write_solution


# Global variables
ILP_OPTIMIZATION = 'ILP_optimization'
HEURISTIC_OPTIMIZATION = 'heuristic_optimization'
EXPLANATIONS_NEGATIVITY_CHECK = 'explanations_negativity_check'
EXPLANATIONS_COMPUTATION = 'explanations_computation'
EVALUATION_GUI = 'evaluation_GUI'


####################
# Variables to set #
####################

# Choose instance index
instance_index = 0
evaluation_experiment_version = EVALUATION_SOLUTION_3_CATEGORY_3

# Choose what to do
process_to_run = EVALUATION_GUI


if __name__ == '__main__':

    #########################################
    # Solving instance via ILP optimization #
    #########################################

    if process_to_run == ILP_OPTIMIZATION:
        instance = get_instance_for_evaluation_in_default_inputs_directory(instance_index)
        solution = compute_solution_for_evaluation_by_ILP_optimization(instance, 45*60)
        print(f"Objective values: {solution.total_working_duration, solution.total_traveling_duration}")
        write_solution(solution, get_default_inputs_directory_path())

    ##################################################
    # Re-optimization of solution via metaheuristics #
    ##################################################

    if process_to_run == HEURISTIC_OPTIMIZATION:
        solution = get_solution_for_evaluation_in_default_inputs_directory(instance_index)
        solution.compute_KPIs()
        print(f"Objective values: {solution.total_working_duration, solution.total_traveling_duration}")
        solution = SolutionLS.from_Solution(solution)
        solution = run_simulated_annealing(solution)
        print(f"Objective values: {solution.total_working_duration, solution.total_traveling_duration}")
        solution.name = solution.name + "_reoptimized"
        write_solution(solution, get_default_outputs_directory_path())

    ##########################################################
    # Checking negativity of all explanations about solution #
    ##########################################################

    if process_to_run == EXPLANATIONS_NEGATIVITY_CHECK:
        solution = get_solution_for_evaluation_in_default_inputs_directory(instance_index)
        check_explanations_negativity(solution, False, True)

    ###############################
    # Computation of explanations #
    ###############################

    if process_to_run == EXPLANATIONS_COMPUTATION:
        solution = get_solution_for_evaluation_in_default_inputs_directory(instance_index)
        compute_and_export_contrastive_explanations(solution, False, True)

    ########################
    # Launch explainer GUI #
    ########################

    if process_to_run == EVALUATION_GUI:
        explainer = prepare_explainer_GUI_for_evaluation_given_experiment_version(evaluation_experiment_version)
        explainer.launch()
