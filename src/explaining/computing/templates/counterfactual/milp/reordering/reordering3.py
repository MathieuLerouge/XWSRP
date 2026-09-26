# Standard library
from typing import Optional

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.computing.templates.counterfactual.milp.reordering.base import \
    ReorderingWithAlterationsBaseModel
from src.optimization.heuristics.sequence import SequenceForHeuristics


###################################
# Reordering3WithAlterationsModel #
###################################

class Reordering3WithAlterationsModel(ReorderingWithAlterationsBaseModel):
    """
    MILP model to compute explanation content for answering (Ord,3) counterfactual question:
    "How to make possible that employee {Employee} performs the activities of their route in another order?"
    """

    def __init__(self, sequence: SequenceForHeuristics,
                 instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                 solving_time_limit: Optional[int] = None):
        """
        Return a MILP model for moving a task of the sequence at another position
        while allowing instance parameter alterations

        Args:
            sequence: The sequence to optimize.
            instance_parameter_alteration_bounds: The bounds of instance parameter alterations.
            solving_time_limit: The solving time limit in seconds.
        """
        self._sequence = sequence
        super().__init__(sequence, self._choose_moving_task(), instance_parameter_alteration_bounds, solving_time_limit)

    def _choose_moving_task(self):
        """
        Return the task to move which is chosen as the task in the middle of the sequence

        Returns:
            The task to move.
        """
        moving_task_index = int(self._sequence.nb_performed_tasks / 2)
        return self._sequence.get_contained_tasks(True)[moving_task_index]
