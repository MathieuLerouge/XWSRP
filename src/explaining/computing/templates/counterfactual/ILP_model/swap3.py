# Local libraries
from src.explaining.computing.templates.counterfactual.ILP_model.swap_with_alterations import \
    IPModelForSwapWithInstanceAlterations


################################################
# Class IPModelForSwap3WithInstanceAlterations #
################################################

class IPModelForSwap3WithInstanceAlterations(IPModelForSwapWithInstanceAlterations):
    """
    IP model to compute explanation content for answering (Swp,3) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} instead of any of their already-performed tasks
    (even if it means changing their order)?"
    """
    pass
