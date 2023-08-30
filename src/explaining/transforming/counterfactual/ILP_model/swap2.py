# Third party libraries
import gurobipy as grb
from gurobipy import GRB

# Local libraries
from src.explaining.transforming.counterfactual.ILP_model.swap_with_alterations import \
    IPModelForSwapWithInstanceAlterations
from src.optimization.IP.sequence.basemodel import create_activity_key


#################################################
# Class IPModelForSwap2aWithInstanceAlterations #
#################################################

class IPModelForSwap2aWithInstanceAlterations(IPModelForSwapWithInstanceAlterations):
    """
    IP model to compute explanation content for answering (Swp,2a) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} in place of one of their tasks?"
    """

    ######################
    # Decision variables #
    ######################

    # Decision variables are unchanged

    ######################
    # Objective function #
    ######################

    # Objective function is unchanged

    #####################
    # Constraints - All #
    #####################

    # Constraints are mostly unchanged
    # Only the flow constraints are changed

    ######################
    # Constraints - Flow #
    ######################

    def _add_flow_constraints(self):
        """
        Add flow constraints to the model:

        - the flow starts with a departure activity
        - the flow ends with a comeback activity
        - the flow is conserved at each activity
        - the sequence of activities remains unchanged except that one task is replaced by the replacing task

        :return: None
        """
        # Add original flow constraints:
        # - ensuring that the flow starts with a departure activity
        # - ensuring that the flow ends with a comeback activity
        # - ensuring that the flow is conserved at each activity
        super()._add_flow_constraints()
        # Add a new flow constraint which ensures that the sequence of activities remains the same
        # except that one task is replaced by the replacing task
        activities = self._sequence.get_contained_activities()
        self._GRB_model.addLConstr(
            grb.quicksum([self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))]
                          for j in range(len(activities) - 1)]),
            sense=GRB.EQUAL, rhs=len(activities) - 3, name=f"ReplacementBetweenConsecutiveActivities"
        )
        self._GRB_model.update()
