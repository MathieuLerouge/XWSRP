# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.explaining.computing.templates.contrastive_and_scenario.ILP_model.category3 import IPModelForCategory3
from src.modeling.sequence import Sequence
from src.optimization.milp.subproblems.sequencemodel import create_activity_key


#########################
# IPModelForReordering3 #
#########################

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

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_tasks_covering_constraints(self):
        for j in self._get_candidate_tasks_keys():
            self._model.add_component(
                f"TaskCoveringConstraint[{j}]",
                pyo.Constraint(expr=(
                    pyo.quicksum(
                        [self.vars_U[(j, k)]
                         for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                         if k != j]
                    ) == 1
                ))
            )

    #######################
    # Constraints - Order #
    #######################

    def _add_sequence_order_constraint(self):
        sequence = self._sequence
        self._model.add_component(
            "SequenceOrderConstraint",
            pyo.Constraint(expr=(
                pyo.quicksum(
                    [self.vars_U[(create_activity_key(sequence[j].activity), create_activity_key(sequence[j + 1].activity))]
                     for j in range(sequence.nb_steps - 1)]
                ) <= sequence.nb_steps - 3
            ))
        )
