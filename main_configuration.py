# Local libraries
from src.utils.constants import *


####################
# Variables to set #
####################


# Choose which process to run when executing __main__.py at the root of the project
# NB: for setting parameters of the process, go to the corresponding 'configuration' file in the src/ directory
MAIN_PROCESS = EXPLAINER_ON_DEMO_SOLUTION_PROCESS
# MAIN_PROCESS = EXPLAINER_ON_SOLUTION_IN_DEFAULT_INPUTS_PROCESS
# MAIN_PROCESS = TEACHING_FEASIBILITY_CHECK_PROCESS
# MAIN_PROCESS = TEACHING_INSTANCE_OPTIMIZATION_PROCESS
# MAIN_PROCESS = EVALUATION_PROCESS


#################
# Do not change #
#################


# Choose whether Gurobi can be used in the project (wherever it is executed)
if MAIN_PROCESS == EVALUATION_PROCESS:
    GUROBI_IS_ENABLED = False
else:
    GUROBI_IS_ENABLED = True
