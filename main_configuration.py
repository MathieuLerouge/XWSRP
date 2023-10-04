# Local libraries
from src.utils.constants import *


################
# Main process #
################

# Choose which process to run when executing __main__.py at the root of the project
# by activating one of the following lines
#
# NB: configuration parameters specific to each process can be found below
#
MAIN_PROCESS = RUN_EXPLANATION_PROCESS
# MAIN_PROCESS = RUN_EVALUATION_PROCESS
# MAIN_PROCESS = RUN_OPTIMIZATION_PROCESS
# MAIN_PROCESS = RUN_REOPTIMIZATION_PROCESS
# MAIN_PROCESS = RUN_ANALYSIS_PROCESS
# MAIN_PROCESS = RUN_TEACHING_PROCESS


#####################################
# Explainer process - Configuration #
#####################################

# Choose which explainer process to run when executing __main__.py at the root of the project
# by activating one of the following lines
MAIN_PROCESS_AMONG_EXPLAINER_ONES = RUN_EXPLAINER_ON_DEMO_SOLUTION_AS_EXPLANATION_PROCESS
# MAIN_PROCESS_AMONG_EXPLAINER_ONES = RUN_EXPLAINER_ON_GIVEN_SOLUTION_AS_EXPLANATION_PROCESS
# MAIN_PROCESS_AMONG_EXPLAINER_ONES = RUN_EXPLANATION_COMPUTATION_ANALYSIS_AS_EXPLANATION_PROCESS
# MAIN_PROCESS_AMONG_EXPLAINER_ONES = RUN_COUNTERFACTUAL_EXPLANATION_COMPUTATION_ANALYSIS_AS_EXPLANATION_PROCESS

# If explainer process is explanations analysis, set values to the following parameters
EXPLANATIONS_ANALYSIS_MAXIMUM_NUMBER_OF_EXPLANATIONS_PER_TEMPLATE = 40
EXPLANATIONS_ANALYSIS_TIME_LIMIT_FOR_COMPUTING_EACH_EXPLANATION = 15
EXPLANATION_COMPUTATION_TIME_BETWEEN_MESSAGES = 30


######################################
# Evaluation process - Configuration #
######################################

# Nothing to configure here


############################################################
# Optimization or reoptimization processes - Configuration #
############################################################

# Choose which optimization process to run when executing __main__.py at the root of the project
# by activating one of the following lines
MAIN_PROCESS_AMONG_OPTIMIZATION_ONES = RUN_GREEDY_ALGORITHM_AS_OPTIMIZATION_PROCESS
# MAIN_PROCESS_AMONG_OPTIMIZATION_ONES = RUN_STOCHASTIC_HEURISTIC_AS_OPTIMIZATION_PROCESS
# MAIN_PROCESS_AMONG_OPTIMIZATION_ONES = RUN_NEIGHBORHOOD_SEARCH_AS_OPTIMIZATION_PROCESS

# Choose which reoptimization process to run when executing __main__.py at the root of the project
# by activating one of the following lines
MAIN_PROCESS_AMONG_REOPTIMIZATION_ONES = RUN_NEIGHBORHOOD_SEARCH_AS_OPTIMIZATION_PROCESS

# General
OPTIMIZATION_PROCESS_SHOW_SOLUTIONS_FIGURES = False
OPTIMIZATION_PROCESS_SAVE_SOLUTIONS_FIGURES = True
OPTIMIZATION_PROCESS_WRITE_SOLUTIONS_ANALYSIS_INTO_FILES = True

# If main process is neighboring search process, set values to the following parameters
NEIGHBORHOOD_SEARCH_POPULATION_SIZE = 20
NEIGHBORHOOD_SEARCH_NB_NEIGHBORS_PER_SOLUTION = 8
NEIGHBORHOOD_SEARCH_PROPORTION_OF_BEST_SOLUTIONS_TO_KEEP = .35
NEIGHBORHOOD_SEARCH_TIME_LIMIT = 15*60
NEIGHBORHOOD_SEARCH_TIME_BETWEEN_MESSAGES = 30


###################################
# Reading process - Configuration #
###################################

# NB 1: solutions files to check must be in the folder inputs at the root of the project,
# all solutions files in this folder will be checked
# NB 2: instances files corresponding to solutions files to check must be placed in the same folder inputs,
CHECK_SOLUTIONS_FEASIBILITY = True
SHOW_SOLUTIONS_FIGURES = True
SAVE_SOLUTIONS_FIGURES = True
WRITE_SOLUTIONS_ANALYSIS_INTO_FILES = True


####################################
# Teaching process - Configuration #
####################################

# Choose which teaching process to run when executing __main__.py at the root of the project
# by activating one of the following lines
MAIN_PROCESS_AMONG_TEACHING_ONES = RUN_SOLUTION_FEASIBILITY_CHECK_AS_TEACHING_PROCESS
# MAIN_PROCESS_AMONG_TEACHING_ONES = RUN_INSTANCE_IP_SOLVING_AS_TEACHING_PROCESS

# If main process is feasibility check of teaching solutions, set values to the following parameters
#
# NB 1: solutions files to check must be in the folder inputs at the root of the project,
# all solutions files in this folder will be checked
# NB 2: instances files corresponding to solutions files to check can be placed in the same folder inputs,
# otherwise instances files that will be considered will be the ones from the folder data/teaching
# NB 3: solutions feasibility checks, solutions analysis and solutions figures, if saved,
# will be found in the folder outputs at the root of the project
#
TOLERANCE_IN_MINUTES_IN_TIME_CONSTRAINTS_CHECK = 0
WRITE_TEACHING_SOLUTIONS_FEASIBILITY_CHECKS_INTO_A_FILE = False
SHOW_TEACHING_SOLUTIONS_FIGURES_WHILE_CHECKING_FEASIBILITY = True
SAVE_TEACHING_SOLUTIONS_FIGURES_WHILE_CHECKING_FEASIBILITY = False
WRITE_TEACHING_SOLUTIONS_ANALYSIS_INTO_FILES = False

# If main process is IP solving of teaching instances, set values to the following parameters
# NB: instances files to solve must be in the folder inputs, all the instances files will be solved
SOLVING_TIME_LIMIT_IN_SECONDS = 30 * 60
MUTE_SOLVING_PROCESS = False


#################
# Do not change #
#################

# Fix whether Gurobi can be used in the project (wherever it is executed)
# NB: this is not a configuration parameter to set, do not change
if MAIN_PROCESS == RUN_EVALUATION_PROCESS:
    GUROBI_IS_ENABLED = False
else:
    GUROBI_IS_ENABLED = True
