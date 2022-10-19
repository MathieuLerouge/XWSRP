# Standard library
from abc import abstractmethod

# Local libraries
from src.modeling.employee import Employee
from src.modeling.task import Task


#################
# Infeasibility #
#################

# Class Infeasibility
class Infeasibility:

    def __init__(self, conflicting_employee: Employee, conflicting_task: Task):
        self._conflicting_employee = conflicting_employee
        self._conflicting_task = conflicting_task

    @property
    def conflicting_employee(self):
        return self._conflicting_employee

    @property
    def conflicting_task(self):
        return self._conflicting_task

    @property
    @abstractmethod
    def is_due_to_skill_considerations(self):
        pass

    @property
    @abstractmethod
    def is_due_to_time_considerations(self):
        pass

    def __repr__(self):
        return f"Infeasibility due to {self._conflicting_employee.name} and {self._conflicting_task.name}"


######################
# SkillInfeasibility #
######################

# Class SkillInfeasibility
class SkillInfeasibility(Infeasibility):

    @property
    def is_due_to_skill_considerations(self):
        return True

    @property
    def is_due_to_time_considerations(self):
        return False


#####################
# TimeInfeasibility #
#####################

# Class TimeInfeasibility
class TimeInfeasibility(Infeasibility):

    def __init__(self, conflicting_employee: Employee, conflicting_task: Task,
                 solution_is_upstream_feasible: bool, solution_is_downstream_feasible: bool,
                 earliest_upstream_feasible_start_time_of_conflicting_task: int,
                 latest_downstream_feasible_start_time_of_conflicting_task: int,
                 upstream_critical_step_index: int, downstream_critical_step_index: int):
        super().__init__(conflicting_employee, conflicting_task)
        self._solution_is_upstream_feasible = solution_is_upstream_feasible
        self._solution_is_downstream_feasible = solution_is_downstream_feasible
        self._earliest_start_time = earliest_upstream_feasible_start_time_of_conflicting_task
        self._latest_start_time = latest_downstream_feasible_start_time_of_conflicting_task
        self._upstream_critical_step_index = upstream_critical_step_index
        self._downstream_critical_step_index = downstream_critical_step_index

    @property
    def is_due_to_skill_considerations(self):
        return False

    @property
    def is_due_to_time_considerations(self):
        return True

    @property
    def solution_is_upstream_feasible(self):
        return self._solution_is_upstream_feasible

    @property
    def solution_is_downstream_feasible(self):
        return self._solution_is_downstream_feasible

    @property
    def earliest_upstream_feasible_start_time_of_conflicting_task(self):
        return self._earliest_start_time

    @property
    def latest_downstream_feasible_start_time_of_conflicting_task(self):
        return self._latest_start_time

    @property
    def upstream_critical_step_index(self):
        return self._upstream_critical_step_index

    @property
    def downstream_critical_step_index(self):
        return self._downstream_critical_step_index
