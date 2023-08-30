# Third party libraries
import gurobipy as grb
from gurobipy import GRB

# Local libraries
from src.explaining.transforming.contrastive_and_scenario.ILP_model.category3 import IPModelForCategory3
from src.modeling.sequence import Sequence
from src.optimization.IP.sequence.basemodel import create_activity_key


# Class IPModelForReordering3
class IPModelForReordering3(IPModelForCategory3):

    def __init__(self, sequence: Sequence):
        pivot_task_index = int(len(sequence)/2)
        super().__init__(sequence, sequence[pivot_task_index].activity)

    def _compute_candidate_tasks(self):
        return self._sequence.get_contained_tasks()

    #####################
    # Constraints - All #
    #####################

    def _add_constraints(self):
        self._add_covering_constraints()
        self._add_flow_constraints()
        self._add_time_window_constraints()
        self._add_sequence_times_constraints()
        self._add_split_time_constraint()
        self._add_sequence_order_constraint()
        # No skill constraints
        self._GRB_model.update()

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_tasks_covering_constraints(self):
        for j in self._get_candidate_tasks_keys():
            self._GRB_model.addLConstr(
                grb.quicksum(
                    [self.vars_U[(j, k)]
                     for k in self.get_activities_keys(including_departure=False, including_comeback=True) if k != j]
                ),
                sense=GRB.EQUAL, rhs=1,
                name=f"TaskCoveringConstraint[{j}]"
            )

    #######################
    # Constraints - Order #
    #######################

    def _add_sequence_order_constraint(self):
        sequence = self._sequence
        self._GRB_model.addLConstr(
            grb.quicksum(
                [self.vars_U[(create_activity_key(sequence[j].activity), create_activity_key(sequence[j + 1].activity))]
                 for j in range(sequence.nb_steps - 1)]
            ),
            sense=GRB.LESS_EQUAL, rhs=sequence.nb_steps - 3,
            name=f"SequenceOrderConstraint"
        )
