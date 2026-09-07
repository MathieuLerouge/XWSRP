# Third party libraries
import gurobipy as grb
from gurobipy import GRB

# Local libraries
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.task import Task
from src.optimization.IP.sequence.basemodel import IPModelForSequenceOptimization


# Class IPModelForSequenceOptimization
class IPModelForSequencePrescribing(IPModelForSequenceOptimization):

    def __init__(self, instance: Instance, employee: Employee,
                 candidate_tasks: list[Task], prescribed_tasks: list[Task]):
        if prescribed_tasks is None:
            prescribed_tasks = []
        for task in prescribed_tasks:
            if not (task in candidate_tasks):
                raise ValueError(f"The prescribed task {task.name} is not in the candidate tasks")
        assert (all([employee.is_capable_of_performing(task) for task in candidate_tasks]),
                f"The given employee {employee.name} is not capable of realizing of the candidate tasks")
        self._prescribed_tasks = prescribed_tasks
        super().__init__(instance, employee, candidate_tasks)

    @property
    def prescribed_tasks(self):
        return self._prescribed_tasks

    def _get_candidate_tasks_keys(self, including_prescribed_tasks: bool = True,
                                  including_non_prescribed_tasks: bool = True):
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
        return [task.name for task in self.prescribed_tasks]

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_covering_constraints(self):

        # Add constraints about non-prescribed tasks covering
        for j in self._get_candidate_tasks_keys(including_prescribed_tasks=False):
            self._GRB_model.addLConstr(
                grb.quicksum(
                    [self.vars_U[(j, k)]
                     for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                     if k != j]
                ),
                sense=GRB.LESS_EQUAL, rhs=1,
                name=f"NonPrescribedTaskCoveringConstraint[{j}]"
            )

        # Add constraints about prescribed tasks covering
        for j in self.get_prescribed_tasks_keys():
            self._GRB_model.addLConstr(
                grb.quicksum(
                    [self.vars_U[(j, k)]
                     for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                     if k != j]
                ),
                sense=GRB.EQUAL, rhs=1,
                name=f"PrescribedTaskCoveringConstraint[{j}]"
            )

        # Add constraints about unavailabilities covering
        for j in self.get_unavailabilities_keys():
            self._GRB_model.addLConstr(
                grb.quicksum(
                    [self.vars_U[(j, k)]
                     for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                     if k != j]
                ),
                sense=GRB.EQUAL, rhs=1,
                name=f"UnavailabilityCoveringConstraint[{j}]"
            )

        self._GRB_model.update()

    #############################
    # Constraints - Time window #
    #############################

    def _add_time_window_constraints(self):

        # Add time windows lower bounds constraints for non-prescribed tasks
        for j in self._get_candidate_tasks_keys(including_prescribed_tasks=False):
            self._GRB_model.addLConstr(
                self.vars_T[j] - grb.quicksum(
                    [self.vars_U[(j, k)]
                     for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                     if k != j]
                ) * self.get_candidate_task_by_key(j).start_time_lb,
                sense=GRB.GREATER_EQUAL, rhs=0,
                name=f"TimeWindowLBConstraint[{j}]"
            )

        # Add time windows lower bounds constraints for prescribed tasks
        for j in self.get_prescribed_tasks_keys():
            self._GRB_model.addLConstr(
                self.vars_T[j] - self.get_candidate_task_by_key(j).start_time_lb,
                sense=GRB.GREATER_EQUAL, rhs=0,
                name=f"TimeWindowLBConstraint[{j}]"
            )

        # Add time windows upper bounds constraints for non-prescribed tasks
        for j in self._get_candidate_tasks_keys(including_prescribed_tasks=False):
            self._GRB_model.addLConstr(
                self.vars_T[j] - grb.quicksum(
                    [self.vars_U[(j, k)]
                     for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                     if k != j]
                ) * (self.get_candidate_task_by_key(j).end_time_ub - self.get_candidate_task_by_key(j).duration),
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"TimeWindowUBConstraint[{j}]"
            )

        # Add time windows upper bounds constraints for prescribed tasks
        for j in self.get_prescribed_tasks_keys():
            self._GRB_model.addLConstr(
                self.vars_T[j] + self.get_candidate_task_by_key(j).duration
                - self.get_candidate_task_by_key(j).end_time_ub,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"TimeWindowUBConstraint[{j}]"
            )

        self._GRB_model.update()
