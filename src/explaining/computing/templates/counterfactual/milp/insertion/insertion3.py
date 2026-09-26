# Local libraries
from src.explaining.computing.templates.counterfactual.milp.insertion.base \
    import InsertionWithAlterationsBaseModel


##################################
# Insertion3WithAlterationsModel #
##################################

class Insertion3WithAlterationsModel(InsertionWithAlterationsBaseModel):
    """
    MILP model to compute explanation content for answering (Ins,3) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task}
    in addition to their already-performed activities (even if it means changing their order)?"
    """

    pass
