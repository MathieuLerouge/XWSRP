# Local libraries
from src.explaining.computing.templates.counterfactual.MILP_model.swap_with_alterations import \
    MILPModelForSwapWithInstanceAlterations


################################################
# Class MILPModelForSwap3WithInstanceAlterations #
################################################

class MILPModelForSwap3WithInstanceAlterations(MILPModelForSwapWithInstanceAlterations):
    """
    MILP model to compute explanation content for answering (Swp,3) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} instead of any of their already-performed tasks
    (even if it means changing their order)?"
    """
    pass
