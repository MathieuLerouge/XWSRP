# Third party libraries
import gurobipy as grb
from gurobipy import GRB

# Local libraries
from src.explaining.transforming.category3.category3 import IPModelForCategory3


# Class IPModelForInsertion3
class IPModelForInsertion3(IPModelForCategory3):

    def _compute_candidate_tasks(self):
        return self._sequence.get_contained_tasks() + [self._pivot_task]

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_tasks_covering_constraints(self):
        for j in self.get_candidate_tasks_keys():
            self._GRB_model.addLConstr(
                grb.quicksum(
                    [self.vars_U[(j, k)]
                     for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                     if k != j]
                ),
                sense=GRB.EQUAL, rhs=1,
                name=f"TaskCoveringConstraint[{j}]"
            )
