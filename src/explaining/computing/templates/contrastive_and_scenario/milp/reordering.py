# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.explaining.computing.templates.contrastive_and_scenario.milp.base import TransformationBaseModel
from src.modeling.sequence import Sequence
from src.optimization.milp.subproblems.sequencemodel import create_activity_key


###################
# ReorderingModel #
###################

class ReorderingModel(TransformationBaseModel):
    """MILP model answering the (Ord,3) question, which reorders the route without changing what is in it."""

    # Reordering only moves a task the employee already performs.
    _pivot_task_is_new_to_employee = False

    def __init__(self, sequence: Sequence):
        """
        Return a MILP model reordering the given sequence.

        The question names no task, so the activity at the middle of the route is taken as the pivot:
        the split start times have to hang off something, and any task in the route will do.

        Args:
            sequence: The sequence to reorder.
        """
        pivot_task_index = int(len(sequence)/2)
        super().__init__(sequence, sequence[pivot_task_index].activity)

    def _compute_candidate_tasks(self):
        """Return the tasks already in the route, and nothing else."""
        return self._sequence.get_contained_tasks()

    #####################
    # Constraints - All #
    #####################

    def _add_constraints(self):
        """Add every constraint the model needs, plus the one forcing the order to actually change."""
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
        """Require every task of the route to still be performed."""
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
        """
        Force the route into a genuinely different order.

        Of the consecutive pairs the given route is made of, at most all but two may survive,
        so a solution that merely reproduces the original order is infeasible.
        """
        sequence = self._sequence
        self._model.add_component(
            "SequenceOrderConstraint",
            pyo.Constraint(expr=(
                pyo.quicksum(
                    [self.vars_U[(create_activity_key(sequence[j].activity),
                                  create_activity_key(sequence[j + 1].activity))]
                     for j in range(sequence.nb_steps - 1)]
                ) <= sequence.nb_steps - 3
            ))
        )
