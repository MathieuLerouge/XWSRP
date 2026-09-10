# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.explaining.computing.templates.contrastive_and_scenario.ILP_model.category3 import IPModelForCategory3


#########################
# IPModelForSwap3 #
#########################

class IPModelForSwap3(IPModelForCategory3):

    def _compute_candidate_tasks(self):
        return self._sequence.get_contained_tasks() + [self._pivot_task]

    @property
    def leaving_task(self):
        for task_key in self._get_candidate_tasks_keys(including_pivot_task=False):
            if not self._check_task_is_performed_by_key(task_key):
                return self.get_candidate_task_by_key(task_key)
        raise Exception("There is a problem here!")

    ###############
    # Constraints #
    ###############

    def _add_tasks_covering_constraints(self):
        # Constraint for covering the pivot task
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
