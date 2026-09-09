# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.task import Task
from src.optimization.milp.subproblems.sequencemodel import SequenceModel


############################
# SequencePrescribingModel #
############################

class SequencePrescribingModel(SequenceModel):
    """
    Builds a sequence out of two kinds of candidate tasks: a prescribed subset that must be covered,
    and the remaining candidate tasks, which stay optional.
    """

    def __init__(self, instance: Instance, employee: Employee,
                 candidate_tasks: list[Task], prescribed_tasks: list[Task]):
        """
        Args:
            instance: the instance the employee belongs to.
            employee: the employee for which the sequence is optimized.
            candidate_tasks: the tasks that can be part of the employee's sequence.
            prescribed_tasks: the subset of candidate_tasks that must be covered, or None for none.

        Raises:
            ValueError: if a prescribed task is not among the candidate tasks.
            AssertionError: if the employee is not capable of performing one of the candidate tasks.
        """
        if prescribed_tasks is None:
            prescribed_tasks = []
        for task in prescribed_tasks:
            if not (task in candidate_tasks):
                raise ValueError(f"The prescribed task {task.name} is not in the candidate tasks")
        assert all([employee.is_capable_of_performing(task) for task in candidate_tasks]), \
            f"The given employee {employee.name} is not capable of performing all of the candidate tasks"
        self._prescribed_tasks = prescribed_tasks
        super().__init__(instance, employee, candidate_tasks)

    @property
    def prescribed_tasks(self):
        """The candidate tasks that must be covered."""
        return self._prescribed_tasks

    def _get_candidate_tasks_keys(self, including_prescribed_tasks: bool = True,
                                  including_non_prescribed_tasks: bool = True):
        """
        Return the keys of the candidate tasks, optionally restricted to the prescribed or
        non-prescribed subset.

        Args:
            including_prescribed_tasks: if True, include the prescribed tasks' keys.
            including_non_prescribed_tasks: if True, include the non-prescribed tasks' keys.
        """
        if including_prescribed_tasks:
            if including_non_prescribed_tasks:
                return [task.name for task in self.candidate_tasks]
            else:
                return [task.name for task in self.prescribed_tasks]
        else:
            if including_non_prescribed_tasks:
                return [task.name for task in self.candidate_tasks if not (task in self.prescribed_tasks)]
            else:
                return []

    def get_prescribed_tasks_keys(self):
        """Return the keys of the prescribed tasks."""
        return [task.name for task in self.prescribed_tasks]

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_covering_constraints(self):

        # Add constraints about non-prescribed tasks covering
        for j in self._get_candidate_tasks_keys(including_prescribed_tasks=False):
            self._model.add_component(
                f"NonPrescribedTaskCoveringConstraint[{j}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([
                        self.vars_U[(j, k)]
                        for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                        if k != j
                    ]) <= 1
                ))
            )

        # Add constraints about prescribed tasks covering
        for j in self.get_prescribed_tasks_keys():
            self._model.add_component(
                f"PrescribedTaskCoveringConstraint[{j}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([
                        self.vars_U[(j, k)]
                        for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                        if k != j
                    ]) == 1
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

        # Add time windows lower bounds constraints for non-prescribed tasks
        for j in self._get_candidate_tasks_keys(including_prescribed_tasks=False):
            self._model.add_component(
                f"TimeWindowLBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] - pyo.quicksum([
                        self.vars_U[(j, k)]
                        for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                        if k != j
                    ]) * self.get_candidate_task_by_key(j).start_time_lb >= 0
                ))
            )

        # Add time windows lower bounds constraints for prescribed tasks
        for j in self.get_prescribed_tasks_keys():
            self._model.add_component(
                f"TimeWindowLBConstraint[{j}]",
                pyo.Constraint(expr=(self.vars_T[j] - self.get_candidate_task_by_key(j).start_time_lb >= 0))
            )

        # Add time windows upper bounds constraints for non-prescribed tasks
        for j in self._get_candidate_tasks_keys(including_prescribed_tasks=False):
            self._model.add_component(
                f"TimeWindowUBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] - pyo.quicksum([
                        self.vars_U[(j, k)]
                        for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                        if k != j
                    ]) * (self.get_candidate_task_by_key(j).end_time_ub - self.get_candidate_task_by_key(j).duration)
                    <= 0
                ))
            )

        # Add time windows upper bounds constraints for prescribed tasks
        for j in self.get_prescribed_tasks_keys():
            self._model.add_component(
                f"TimeWindowUBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration
                    - self.get_candidate_task_by_key(j).end_time_ub <= 0
                ))
            )
