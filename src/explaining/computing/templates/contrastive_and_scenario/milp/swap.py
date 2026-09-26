# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.explaining.computing.templates.contrastive_and_scenario.milp.base import TransformationBaseModel


#############
# SwapModel #
#############

class SwapModel(TransformationBaseModel):
    """
    MILP model answering the (Swp,3) question, which trades one of the route's tasks for another and
    may reorder the rest.
    """

    # The replacing task is one the employee does not perform yet.
    _pivot_task_is_new_to_employee = True

    def _compute_candidate_tasks(self):
        """Return the tasks already in the route, plus the one that would come in."""
        return self._sequence.get_contained_tasks() + [self._pivot_task]

    @property
    def leaving_task(self):
        """
        The task the solved route gave up to make room for the pivot task.

        Raises:
            Exception: if the route performs every candidate task, so nothing was given up.
        """
        for task_key in self._get_candidate_tasks_keys(including_pivot_task=False):
            if not self._check_task_is_performed_by_key(task_key):
                return self.get_candidate_task_by_key(task_key)
        raise Exception("There is a problem here!")

    ###############
    # Constraints #
    ###############

    def _add_tasks_covering_constraints(self):
        # Constraint for covering the pivot task
        """
        Require the incoming task to be performed, leave every other one optional, and keep the route the
        same length as before - so that exactly one task drops out.
        """
        j = self.pivot_task_key
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
        # Constraint for potentially covering all other tasks
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._model.add_component(
                f"TaskCoveringConstraint[{j}]",
                pyo.Constraint(expr=(
                    pyo.quicksum(
                        [self.vars_U[(j, k)]
                         for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                         if k != j]
                    ) <= 1
                ))
            )
        # Constraint for covering as many tasks as before
        self._model.add_component(
            "CoveringConstraint",
            pyo.Constraint(expr=(
                pyo.quicksum(
                    [self.vars_U[(j, k)]
                     for j in self.get_activities_keys(including_departure=True, including_comeback=False)
                     for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                     if k != j]
                ) == self._sequence.nb_steps - 1
            ))
        )
