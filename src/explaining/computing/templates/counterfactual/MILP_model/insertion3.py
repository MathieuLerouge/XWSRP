# Local libraries
from src.explaining.computing.templates.counterfactual.MILP_model.insertion_with_alterations \
    import MILPModelForInsertionWithInstanceAlterations


#####################################################
# Class MILPModelForInsertion3WithInstanceAlterations #
#####################################################

class MILPModelForInsertion3WithInstanceAlterations(MILPModelForInsertionWithInstanceAlterations):
    """
    MILP model to compute explanation content for answering (Ins,3) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task}
    in addition to their already-performed activities (even if it means changing their order)?"
    """

    pass
