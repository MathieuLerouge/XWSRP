# Local libraries
from src.evaluation.routine import get_instance_for_evaluation_in_default_inputs_directory, \
    compute_solution_for_evaluation_by_ILP_optimization, prepare_explainer_UI, \
    get_solution_for_evaluation_in_default_inputs_directory, launch_explainer_UI_on_evaluation_solution
from src.optimization.localsearch.solution import SolutionLS
from src.optimization.localsearch.solving import run_simulated_annealing
from src.utils.files import get_default_inputs_directory_path, get_default_outputs_directory_path
from src.writing.solution import write_solution


INSTANCE_INDEX = 2


####################################
# Optimization of instance via ILP #
####################################

# instance = get_instance_for_evaluation_in_default_inputs_directory(INSTANCE_INDEX)
# solution = compute_solution_for_evaluation_by_ILP_optimization(instance, 6*60)
# print(solution.total_working_duration, solution.total_traveling_duration)
# write_solution(solution, get_default_inputs_directory_path())


##################################################
# Re-optimization of solution via metaheuristics #
##################################################

# solution = get_solution_for_evaluation_in_default_inputs_directory(INSTANCE_INDEX)
# solution.compute_KPIs()
# print(f"Objective values: {solution.total_working_duration, solution.total_traveling_duration}")
# solution = SolutionLS.from_Solution(solution)
# solution = run_simulated_annealing(solution)
# print(f"Objective values: {solution.total_working_duration, solution.total_traveling_duration}")
# solution.name = solution.name + "_reoptimized"
# write_solution(solution, get_default_outputs_directory_path())


#############################
# Visualisation of solution #
#############################

solution = get_solution_for_evaluation_in_default_inputs_directory(INSTANCE_INDEX)
print(solution)
explainer = prepare_explainer_UI(solution)
explainer.launch()


###############################
# Computation of explanations #
###############################

# run_explanations_computation()


###############################
# Computation of explanations #
###############################

# launch_explainer_UI_on_evaluation_solution()
