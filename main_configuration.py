# Local libraries
from src.utils.constants import *


####################
# Variables to set #
####################

# Choose which routine to run (when executing main)
# ROUTINE_KEY = CHECKING_ROUTINE_KEY
# ROUTINE_KEY = OPTIMIZING_ROUTINE_KEY
# ROUTINE_KEY = EXPLAINING_ROUTINE_KEY
ROUTINE_KEY = EVALUATING_ROUTINE_KEY

# Choose whether or not Gurobi can be used in the project (wherever it is executed)
if ROUTINE_KEY == EVALUATING_ROUTINE_KEY:
    GUROBI_IS_ENABLED = False
else:
    GUROBI_IS_ENABLED = True
