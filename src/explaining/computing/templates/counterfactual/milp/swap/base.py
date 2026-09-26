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


################################
# SwapWithAlterationsBaseModel #
################################

class SwapWithAlterationsBaseModel(TransformationWithAlterationsBaseModel):
    """
    Base MILP model to compute explanation content for answering counterfactual question about swap
    """

    _pivot_task_is_new_to_employee = True

    def __init__(self, sequence: SequenceForHeuristics, replacing_task: Task,
                 instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                 solving_time_limit: Optional[int] = None):
        """
        Return a MILP model for replacing a task of the sequence by the replacing task
        while allowing instance parameter alterations

        Args:
            sequence: The sequence to optimize.
            replacing_task: The replacing task.
            instance_parameter_alteration_bounds: The bounds of instance parameter alterations.
            solving_time_limit: The solving time limit in seconds.
        """
        super().__init__(sequence, replacing_task, instance_parameter_alteration_bounds, solving_time_limit)

    ########################################
    # Getters and setters - Replacing task #
    ########################################

    @property
    def replacing_task(self):
        """The replacing task."""
        return self._pivot_task

    @property
    def replacing_task_time_gap(self):
        """The time gap between backward and forward start times of the replacing task."""
        return self.pivot_task_time_gap

    @property
    def replacing_task_start_time(self):
        """The start time of the replacing task."""
        return self.pivot_task_start_time

    @property
    def replacing_task_start_time_for_backward(self):
        """The start time of the replacing task which respects time constraints in backward direction."""
        return self.pivot_task_start_time_for_backward

    @property
    def replacing_task_start_time_for_forward(self):
        """The start time of the replacing task which respects time constraints in forward direction."""
        return self.pivot_task_start_time_for_forward

    #######################################
    # Getters and setters - Replaced task #
    #######################################

    @property
    def replaced_task(self):
        """The task replaced by the replacing task, which is deduced from the results of the sequence optimization."""
        for task_key in self._get_candidate_tasks_keys(including_pivot_task=False):
            if not self._is_task_performed_given_key(task_key):
                return self.get_candidate_task_by_key(task_key)
        raise AttributeError("There is no solution sequence stored")

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

    # Constraints are mostly unchanged
    # Only the covering constraints are changed

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_covering_constraints(self):
        """
        Add the covering constraints to the model:

        - the replacing task must be performed
        - all other tasks must be performed at most once
        - there must be as many task performed as there are tasks in the sequence before the transformation
        """
        # Constraint ensuring that the replacing task is performed
        j = self._pivot_task_key
        self._model.add_component(
            f"TaskCoveringConstraint[{j}]",
            pyo.Constraint(expr=(
                pyo.quicksum([self.vars_U[(j, k)]
                              for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                              if k != j]) == 1
            ))
        )
        # Constraints ensuring that all other tasks are performed at most once
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._model.add_component(
                f"TaskCoveringConstraint[{j}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([self.vars_U[(j, k)]
                                  for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                                  if k != j]) <= 1
                ))
            )
        # Constraint ensuring that there must be as many task performed as there are tasks in the sequence
        # before the transformation
        self._model.add_component(
            "GeneralCoveringConstraint",
            pyo.Constraint(expr=(
                pyo.quicksum([self.vars_U[(j, k)]
                              for j in self.get_activities_keys(including_departure=True, including_comeback=False)
                              for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                              if k != j]) == self._sequence.nb_steps - 1
            ))
        )
