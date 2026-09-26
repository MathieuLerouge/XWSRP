# Local libraries
from src.explaining.computing.templates.counterfactual.milp.swap.base import \
    SwapWithAlterationsBaseModel


#############################
# Swap3WithAlterationsModel #
#############################

class Swap3WithAlterationsModel(SwapWithAlterationsBaseModel):
    """
    MILP model to compute explanation content for answering (Swp,3) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} instead of any of their already-performed tasks
    (even if it means changing their order)?"
    """
    pass
