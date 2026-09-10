# Local libraries
from src.explaining.computing.templates.counterfactual.ILP_model.insertion_with_alterations \
    import IPModelForInsertionWithInstanceAlterations


#####################################################
# Class IPModelForInsertion3WithInstanceAlterations #
#####################################################

class IPModelForInsertion3WithInstanceAlterations(IPModelForInsertionWithInstanceAlterations):
    """
    IP model to compute explanation content for answering (Ins,3) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task}
    in addition to their already-performed activities (even if it means changing their order)?"
    """

    pass
