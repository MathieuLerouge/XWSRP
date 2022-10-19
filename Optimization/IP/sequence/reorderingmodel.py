# Third-party libraries
import gurobipy as grb
from gurobipy import GRB

# Local libraries
from model.sequence import Sequence
from optimization.IP.sequence.basemodel import IPModelForSequenceOptimization, create_activity_key


# Class IPModelForSequenceReordering
class IPModelForSequenceReordering(IPModelForSequenceOptimization):

    def __init__(self, sequence: Sequence):
        self._initial_sequence = sequence
        super().__init__(sequence.instance, sequence.employee, sequence.get_contained_tasks())

    @property
    def initial_sequence(self):
        return self._initial_sequence

    ###############
    # Constraints #
    ###############

    def _add_constraints(self):
        self._add_covering_constraints()
        self._add_flow_constraints()
        self._add_time_window_constraints()
        self._add_sequence_times_constraints()
        self._add_sequence_order_constraint()
        # No skill constraints

    ################################
    # Constraints - Sequence order #
    ################################

    def _add_sequence_order_constraint(self):
        sequence = self.initial_sequence
        self._GRB_model.addLConstr(
            grb.quicksum(
                [self.vars_U[(create_activity_key(sequence[j].activity),
                              create_activity_key(sequence[j + 1].activity))]
                 for j in range(sequence.nb_steps - 1)]
            ),
            sense=GRB.LESS_EQUAL, rhs=self.initial_sequence.nb_steps - 3,
            name=f"SequenceOrderConstraint"
        )
        self._GRB_model.update()
