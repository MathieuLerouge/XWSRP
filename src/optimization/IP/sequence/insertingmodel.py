# Third party libraries
import gurobipy as grb
from gurobipy import GRB

# Local libraries
from src.modeling.sequence import Sequence
from src.modeling.task import Task
from src.optimization.IP.sequence.basemodel import IPModelForSequenceOptimization


# Class IPModelForSequenceInserting
class IPModelForSequenceInserting(IPModelForSequenceOptimization):

    def __init__(self, sequence: Sequence, new_task: Task):
        candidate_tasks = sequence.get_contained_tasks() + [new_task]
        self._new_task = new_task
        super().__init__(sequence.instance, sequence.employee, candidate_tasks)

    @property
    def new_task(self):
        return self._new_task

    def get_candidate_tasks_keys(self, including_new_task: bool = True):
        if including_new_task:
            return [task.name for task in self.candidate_tasks]
        else:
            return [task.name for task in self.candidate_tasks if task != self._new_task]

    def get_new_task_key(self):
        return self._new_task.name

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_covering_constraints(self):

        # Add constraints about old tasks covering
        for j in self.get_candidate_tasks_keys(including_new_task=False):
            self._GRB_model.addLConstr(
                grb.quicksum(
                    [self.vars_U[(j, k)]
                     for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                     if k != j]
                ),
                sense=GRB.EQUAL, rhs=1,
                name=f"TaskCoveringConstraint[{j}]"
            )

        # Add constraints about new task covering
        j = self.get_new_task_key()
        self._GRB_model.addLConstr(
            grb.quicksum(
                [self.vars_U[(j, k)]
                 for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                 if k != j]
            ),
            sense=GRB.LESS_EQUAL, rhs=1,
            name=f"TaskCoveringConstraint[{j}]"
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

        # Add time windows lower bounds constraints for old tasks
        for j in self.get_candidate_tasks_keys(including_new_task=False):
            self._GRB_model.addLConstr(
                self.vars_T[j] - self.get_candidate_task_by_key(j).start_time_LB,
                sense=GRB.GREATER_EQUAL, rhs=0,
                name=f"TimeWindowLBConstraint[{j}]"
            )

        # Add time window lower bound constraint for new task
        j = self.get_new_task_key()
        self._GRB_model.addLConstr(
            self.vars_T[j]
            - grb.quicksum(
                [self.vars_U[(j, k)]
                 for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                 if k != j]
            ) * self.get_candidate_task_by_key(j).start_time_LB,
            sense=GRB.GREATER_EQUAL, rhs=0,
            name=f"TimeWindowLBConstraint[{j}]"
        )

        # Add time windows upper bounds constraints for old tasks
        for j in self.get_candidate_tasks_keys(including_new_task=False):
            self._GRB_model.addLConstr(
                self.vars_T[j] + self.get_candidate_task_by_key(j).duration
                - self.get_candidate_task_by_key(j).end_time_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"TimeWindowUBConstraint[{j}]"
            )

        # Add time window upper bound constraint for new task
        j = self.get_new_task_key()
        self._GRB_model.addLConstr(
            self.vars_T[j]
            - grb.quicksum(
                [self.vars_U[(j, k)]
                 for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                 if k != j]
            ) * (self.get_candidate_task_by_key(j).end_time_UB - self.get_candidate_task_by_key(j).duration),
            sense=GRB.LESS_EQUAL, rhs=0,
            name=f"TimeWindowUBConstraint[{j}]"
        )

        self._GRB_model.update()
