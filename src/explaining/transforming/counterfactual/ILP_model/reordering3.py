# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.transforming.counterfactual.ILP_model.reordering_with_alterations import \
    IPModelForReorderingWithInstanceAlterations
from src.optimization.heuristics.sequence import SequenceForHeuristics


######################################################
# Class IPModelForReordering3WithInstanceAlterations #
######################################################

class IPModelForReordering3WithInstanceAlterations(IPModelForReorderingWithInstanceAlterations):
    """
    IP model to compute explanation content for answering (Ord,3) counterfactual question:
    "How to make possible that employee {Employee} performs the activities of their route in another order?"
    """

    def __init__(self, sequence: SequenceForHeuristics, instance_parameter_alteration_bounds: InstanceChanges = None,
                 solving_time_limit: int = None):
        """
        Return an IP model for moving a task of the sequence at another position
        while allowing instance parameter alterations

        :param sequence: the sequence to optimize (SequenceForHeuristics)
        :param instance_parameter_alteration_bounds: the bounds of instance parameter alterations (InstanceChanges)
        :param solving_time_limit: the solving time limit in seconds (int)
        """
        self._sequence = sequence
        super().__init__(sequence, self._choose_moving_task(), instance_parameter_alteration_bounds, solving_time_limit)

    def _choose_moving_task(self):
        """
        Return the task to move which is chosen as the task in the middle of the sequence

        :return: the task to move (Task)
        """
        moving_task_index = int(self._sequence.nb_realized_tasks / 2)
        return self._sequence.get_contained_tasks(True)[moving_task_index]
