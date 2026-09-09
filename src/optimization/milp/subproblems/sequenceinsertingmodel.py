# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.modeling.sequence import Sequence
from src.modeling.task import Task
from src.optimization.milp.subproblems.sequencemodel import SequenceModel


##########################
# SequenceInsertingModel #
##########################

class SequenceInsertingModel(SequenceModel):
    """
    Tests whether one new task can optionally be inserted into an existing sequence: its covering
    constraint is relaxed to at most one, so the model stays feasible whether or not the task ends up
    covered — a feasibility probe rather than a forced insertion.
    """

    def __init__(self, sequence: Sequence, new_task: Task):
        """
        Args:
            sequence: the existing sequence to try inserting the new task into.
            new_task: the task whose insertion is tested.
        """
        candidate_tasks = sequence.get_contained_tasks() + [new_task]
        self._new_task = new_task
        super().__init__(sequence.instance, sequence.employee, candidate_tasks)

    @property
    def new_task(self):
        """The task whose insertion is tested."""
        return self._new_task

    def _get_candidate_tasks_keys(self, including_new_task: bool = True):
        """
        Return the keys of the candidate tasks, optionally excluding the new task
        (which is handled separately since its covering constraint is optional, not mandatory).

        Args:
            including_new_task: if True, include the new task's key.
        """
        if including_new_task:
            return [task.name for task in self.candidate_tasks]
        else:
            return [task.name for task in self.candidate_tasks if task != self._new_task]

    def get_new_task_key(self):
        """Return the new task's key."""
        return self._new_task.name

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_covering_constraints(self):

        # Add constraints about old tasks covering
        for j in self._get_candidate_tasks_keys(including_new_task=False):
            self._model.add_component(
                f"TaskCoveringConstraint[{j}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([
                        self.vars_U[(j, k)]
                        for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                        if k != j
                    ]) == 1
                ))
            )

        # Add constraints about new task covering
        j = self.get_new_task_key()
        self._model.add_component(
            f"TaskCoveringConstraint[{j}]",
            pyo.Constraint(expr=(
                pyo.quicksum([
                    self.vars_U[(j, k)]
                    for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                    if k != j
                ]) <= 1
            ))
        )

        # Add constraints about unavailabilities covering
        for j in self.get_unavailabilities_keys():
            self._model.add_component(
                f"UnavailabilityCoveringConstraint[{j}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([
                        self.vars_U[(j, k)]
                        for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                        if k != j
                    ]) == 1
                ))
            )

    #############################
    # Constraints - Time window #
    #############################

    def _add_time_window_constraints(self):

        # Add time windows lower bounds constraints for old tasks
        for j in self._get_candidate_tasks_keys(including_new_task=False):
            self._model.add_component(
                f"TimeWindowLBConstraint[{j}]",
                pyo.Constraint(expr=(self.vars_T[j] - self.get_candidate_task_by_key(j).start_time_lb >= 0))
            )

        # Add time window lower bound constraint for new task
        j = self.get_new_task_key()
        self._model.add_component(
            f"TimeWindowLBConstraint[{j}]",
            pyo.Constraint(expr=(
                self.vars_T[j]
                - pyo.quicksum([
                    self.vars_U[(j, k)]
                    for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                    if k != j
                ]) * self.get_candidate_task_by_key(j).start_time_lb >= 0
            ))
        )

        # Add time windows upper bounds constraints for old tasks
        for j in self._get_candidate_tasks_keys(including_new_task=False):
            self._model.add_component(
                f"TimeWindowUBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration
                    - self.get_candidate_task_by_key(j).end_time_ub <= 0
                ))
            )

        # Add time window upper bound constraint for new task
        j = self.get_new_task_key()
        self._model.add_component(
            f"TimeWindowUBConstraint[{j}]",
            pyo.Constraint(expr=(
                self.vars_T[j]
                - pyo.quicksum([
                    self.vars_U[(j, k)]
                    for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                    if k != j
                ]) * (self.get_candidate_task_by_key(j).end_time_ub - self.get_candidate_task_by_key(j).duration) <= 0
            ))
        )
