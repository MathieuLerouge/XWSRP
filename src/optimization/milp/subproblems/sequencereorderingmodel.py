# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.modeling.sequence import Sequence
from src.optimization.milp.subproblems.sequencemodel import SequenceModel, create_activity_key


###########################
# SequenceReorderingModel #
###########################

class SequenceReorderingModel(SequenceModel):
    """
    Keeps the exact same set of tasks as a given initial sequence, and only looks for a better order
    for them, forced to differ from that initial order via _add_sequence_order_constraint.
    """

    def __init__(self, sequence: Sequence):
        """
        Args:
            sequence: the sequence whose tasks are kept, and whose order is to be improved.
        """
        self._initial_sequence = sequence
        super().__init__(sequence.instance, sequence.employee, sequence.get_contained_tasks())

    @property
    def initial_sequence(self):
        """The sequence whose tasks are kept, and whose order is to be improved."""
        return self._initial_sequence

    ###############
    # Constraints #
    ###############

    def _add_constraints(self):
        """Add all constraints to the model: same as SequenceModel, plus the sequence-order constraint."""
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
        """Force at least two of the initial sequence's consecutive-activity arcs to change."""
        sequence = self.initial_sequence
        self._model.add_component(
            "SequenceOrderConstraint",
            pyo.Constraint(expr=(
                pyo.quicksum([
                    self.vars_U[(create_activity_key(sequence[j].activity),
                                create_activity_key(sequence[j + 1].activity))]
                    for j in range(sequence.nb_steps - 1)
                ]) <= self.initial_sequence.nb_steps - 3
            ))
        )
