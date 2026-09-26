# Standard library
from typing import cast

# Third-party libraries
import pyomo.environ as pyo
from pyomo.core.base import VarData

# Local libraries
from src.explaining.computing.templates.contrastive_and_scenario.milp.base import TransformationBaseModel
from src.optimization.milp.subproblems.sequencemodel import create_activity_key


##################
# InsertionModel #
##################

class InsertionModel(TransformationBaseModel):
    """MILP model answering the (Ins,3) question, which adds a task to the route and may reorder the rest."""

    # The inserted task is one the employee does not perform yet.
    _pivot_task_is_new_to_employee = True

    def _compute_candidate_tasks(self):
        """Return the tasks already in the route, plus the one to insert."""
        return self._sequence.get_contained_tasks() + [self._pivot_task]

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_tasks_covering_constraints(self):
        """Require every candidate task to be performed, the inserted one included."""
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

    ################
    # Optimization #
    ################

    def warm_start(self):
        """
        Seed the solver with the given route, the task to insert placed at its middle.

        The start times come from the route as it stands,
        and the pivot task's two are set as far apart as its neighbors and its own time window allow.
        """
        nb_activities = len(self._sequence)
        # Set values for time variables
        for j in self._get_candidate_tasks_keys(False):
            task = self.get_candidate_task_by_key(j)
            step = self._sequence.get_step_of(task)
            cast(VarData, self.vars_T[j]).value = step.start_time
        # Set values for backward and forward time variables
        middle_step_index = int(nb_activities/2)
        insertion_step_index = middle_step_index + 1
        step_before_insertion = self._sequence[insertion_step_index - 1]
        activity_before_insertion = step_before_insertion.activity
        step_after_insertion = self._sequence[insertion_step_index]
        activity_after_insertion = step_after_insertion.activity
        inserted_task = self._pivot_task
        self.var_T_backward.value = \
            max(step_before_insertion.end_time +
                self._sequence.instance.compute_traveling_duration(activity_before_insertion, inserted_task),
                inserted_task.start_time_lb)
        self.var_T_forward.value = min(
            step_after_insertion.start_time -
            self._sequence.instance.compute_traveling_duration(inserted_task, activity_after_insertion),
            inserted_task.end_time_ub
        ) - inserted_task.duration
        # Set values for spatial variables
        for indices in self.vars_U.keys():
            cast(VarData, self.vars_U[indices]).value = 0
        for step_index, step in enumerate(self._sequence.get_steps(0, insertion_step_index - 1)):
            next_step = self._sequence[step_index + 1]
            activity_key = create_activity_key(step.activity)
            next_activity_key = create_activity_key(next_step.activity)
            cast(VarData, self.vars_U[(activity_key, next_activity_key)]).value = 1
        activity_before_insertion_key = create_activity_key(activity_before_insertion)
        inserted_task_key = create_activity_key(inserted_task)
        activity_after_insertion_key = create_activity_key(activity_after_insertion)
        cast(VarData, self.vars_U[(activity_before_insertion_key, inserted_task_key)]).value = 1
        cast(VarData, self.vars_U[(inserted_task_key, activity_after_insertion_key)]).value = 1
        for step_index_delta, step in enumerate(self._sequence.get_steps(insertion_step_index, nb_activities - 1)):
            step = self._sequence[insertion_step_index + step_index_delta]
            activity_key = create_activity_key(step.activity)
            next_step = self._sequence[insertion_step_index + step_index_delta + 1]
            next_activity_key = create_activity_key(next_step.activity)
            cast(VarData, self.vars_U[(activity_key, next_activity_key)]).value = 1
