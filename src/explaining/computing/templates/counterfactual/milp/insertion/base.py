# Standard library
from typing import Optional

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.modeling.task import Task
from src.explaining.computing.templates.counterfactual.milp.base import \
    TransformationWithAlterationsBaseModel
from src.optimization.heuristics.sequence import SequenceForHeuristics


#####################################
# InsertionWithAlterationsBaseModel #
#####################################

class InsertionWithAlterationsBaseModel(TransformationWithAlterationsBaseModel):
    """
    Base MILP model to compute explanation content for answering counterfactual question about insertion
    """

    _pivot_task_is_new_to_employee = True

    def __init__(self, sequence: SequenceForHeuristics, task_to_insert: Task,
                 instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                 solving_time_limit: Optional[int] = None):
        """
        Return a MILP model for inserting a task in the sequence while allowing instance parameter alterations

        Args:
            sequence: The sequence to optimize.
            task_to_insert: The task to insert.
            instance_parameter_alteration_bounds: The bounds of instance parameter alterations.
            solving_time_limit: The solving time limit in seconds.
        """
        super().__init__(sequence, task_to_insert, instance_parameter_alteration_bounds, solving_time_limit)

    #######################################
    # Getters and setters - Entering task #
    #######################################

    @property
    def task_to_insert(self):
        """The task to insert."""
        return self._pivot_task

    @property
    def task_to_insert_time_gap(self):
        """The time gap between backward and forward start times of the task to insert."""
        return self.pivot_task_time_gap

    @property
    def task_to_insert_start_time(self):
        """The start time of the task to insert."""
        return self.pivot_task_start_time

    @property
    def task_to_insert_start_time_for_backward(self):
        """The start time of the task to insert which respects time constraints in backward direction."""
        return self.pivot_task_start_time_for_backward

    @property
    def task_to_insert_start_time_for_forward(self):
        """The start time of the task to insert which respects time constraints in forward direction."""
        return self.pivot_task_start_time_for_forward

    ######################
    # Decision variables #
    ######################

    # Decision variables are unchanged

    ######################
    # Objective function #
    ######################

    # Objective function is unchanged (lexicographic, see the base class)

    #####################
    # Constraints - All #
    #####################

    # Constraints are unchanged
