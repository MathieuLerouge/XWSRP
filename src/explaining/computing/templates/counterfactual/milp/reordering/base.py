# Standard library
from typing import Optional

# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.computing.templates.counterfactual.milp.base import \
    TransformationWithAlterationsBaseModel
from src.modeling.task import Task
from src.optimization.heuristics.sequence import SequenceForHeuristics
from src.optimization.milp.subproblems.sequencemodel import create_activity_key


######################################
# ReorderingWithAlterationsBaseModel #
######################################

class ReorderingWithAlterationsBaseModel(TransformationWithAlterationsBaseModel):
    """
    Base MILP model to compute explanation content for answering counterfactual question about reordering
    """

    _pivot_task_is_new_to_employee = False

    def __init__(self, sequence: SequenceForHeuristics, moving_task: Task,
                 instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                 solving_time_limit: Optional[int] = None):
        """
        Return a MILP model for moving a task of the sequence at another position
        while allowing instance parameter alterations

        Args:
            sequence: The sequence to optimize.
            moving_task: The moving task.
            instance_parameter_alteration_bounds: The bounds of instance parameter alterations.
            solving_time_limit: The solving time limit in seconds.
        """
        super().__init__(sequence, moving_task, instance_parameter_alteration_bounds, solving_time_limit)

    def _compute_candidate_tasks(self):
        """
        Compute the candidate tasks i.e. the tasks that are part of the employee's sequence

        Returns:
            The list of candidate tasks.
        """
        return self._sequence.get_contained_tasks()

    #####################################
    # Getters and setters - Moving task #
    #####################################

    @property
    def moving_task(self):
        """The moving task."""
        return self._pivot_task

    @property
    def _moving_task_key(self):
        """The key of the moving task."""
        return self._pivot_task_key

    @property
    def moving_task_time_gap(self):
        """The time gap between backward and forward start times of the moving task."""
        return self.pivot_task_time_gap

    @property
    def moving_task_start_time(self):
        """The start time of the moving task."""
        return self.pivot_task_start_time

    @property
    def moving_task_start_time_for_backward(self):
        """The start time of the moving task which respects time constraints in backward direction."""
        return self.pivot_task_start_time_for_backward

    @property
    def moving_task_start_time_for_forward(self):
        """The start time of the moving task which respects time constraints in forward direction."""
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

    def _add_constraints(self):
        """
        Add all constraints to the model including:

        - covering constraints
        - flow constraints
        - time window constraints
        - sequence times constraints
        - split time constraints
        - instance parameter alterations bounds constraints
        - sequence order change constraint
        - (no skill constraints)
        """
        super()._add_constraints()
        self._add_sequence_order_change_constraints()

    #######################
    # Constraints - Order #
    #######################

    def _add_sequence_order_change_constraints(self):
        """
        Add the constraints ensuring that the order of activities in the sequence changes
        """
        sequence = self._sequence
        self._model.add_component(
            "SequenceOrderConstraint",
            pyo.Constraint(expr=(
                pyo.quicksum([self.vars_U[(create_activity_key(sequence[j].activity),
                                           create_activity_key(sequence[j + 1].activity))]
                              for j in range(sequence.nb_steps - 1)]) <= sequence.nb_steps - 3
            ))
        )
