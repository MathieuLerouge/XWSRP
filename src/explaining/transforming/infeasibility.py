# Standard library
from abc import abstractmethod

# Local libraries
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.task import Task

# Global variables
INFEASIBILITY_TYPE_KEY = 'type'
CONFLICTING_EMPLOYEE_NAME_KEY = 'employee'
CONFLICTING_TASK_NAME_KEY = 'task'
SOLUTION_IS_UPSTREAM_FEASIBLE_KEY = 'upstream feasible'
SOLUTION_IS_DOWNSTREAM_FEASIBLE_KEY = 'downstream feasible'
EARLIEST_UPSTREAM_FEASIBLE_START_TIME_OF_CONFLICTING_TASK_KEY = 'early start time'
LATEST_DOWNSTREAM_FEASIBLE_START_TIME_OF_CONFLICTING_TASK_KEY = 'late start time'
UPSTREAM_CRITICAL_STEP_INDEX_KEY = 'upstream critical index'
DOWNSTREAM_CRITICAL_STEP_INDEX_KEY = 'downstream critical index'


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

    def to_dict(self):
        return {CONFLICTING_EMPLOYEE_NAME_KEY: self.conflicting_employee.name,
                CONFLICTING_TASK_NAME_KEY: self.conflicting_task.name}

    @classmethod
    def from_dict(cls, dictionary, instance: Instance):
        if dictionary[INFEASIBILITY_TYPE_KEY] == 'skill':
            return SkillInfeasibility.from_dict(dictionary, instance)
        elif dictionary[INFEASIBILITY_TYPE_KEY] == 'time':
            return TimeInfeasibility.from_dict(dictionary, instance)
        else:
            raise ValueError("The infeasibility should be regarding skill or time")


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

    def to_dict(self):
        dictionary = super().to_dict()
        dictionary[INFEASIBILITY_TYPE_KEY] = "skill"
        return dictionary

    @classmethod
    def from_dict(cls, dictionary, instance: Instance):
        return cls(instance.get_employee_by_name(dictionary[CONFLICTING_EMPLOYEE_NAME_KEY]),
                   instance.get_task_by_name(dictionary[CONFLICTING_TASK_NAME_KEY]))


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

    def to_dict(self):
        dictionary = super().to_dict()
        dictionary[INFEASIBILITY_TYPE_KEY] = "time"
        dictionary[SOLUTION_IS_UPSTREAM_FEASIBLE_KEY] = int(self.solution_is_upstream_feasible)
        dictionary[SOLUTION_IS_DOWNSTREAM_FEASIBLE_KEY] = int(self.solution_is_downstream_feasible)
        dictionary[EARLIEST_UPSTREAM_FEASIBLE_START_TIME_OF_CONFLICTING_TASK_KEY] = \
            self.earliest_upstream_feasible_start_time_of_conflicting_task
        dictionary[LATEST_DOWNSTREAM_FEASIBLE_START_TIME_OF_CONFLICTING_TASK_KEY] = \
            self.latest_downstream_feasible_start_time_of_conflicting_task
        dictionary[UPSTREAM_CRITICAL_STEP_INDEX_KEY] = self.upstream_critical_step_index
        dictionary[DOWNSTREAM_CRITICAL_STEP_INDEX_KEY] = self.downstream_critical_step_index
        return dictionary

    @classmethod
    def from_dict(cls, dictionary, instance: Instance):
        return cls(instance.get_employee_by_name(dictionary[CONFLICTING_EMPLOYEE_NAME_KEY]),
                   instance.get_task_by_name(dictionary[CONFLICTING_TASK_NAME_KEY]),
                   bool(dictionary[SOLUTION_IS_UPSTREAM_FEASIBLE_KEY]),
                   bool(dictionary[SOLUTION_IS_DOWNSTREAM_FEASIBLE_KEY]),
                   int(dictionary[EARLIEST_UPSTREAM_FEASIBLE_START_TIME_OF_CONFLICTING_TASK_KEY]),
                   int(dictionary[LATEST_DOWNSTREAM_FEASIBLE_START_TIME_OF_CONFLICTING_TASK_KEY]),
                   int(dictionary[UPSTREAM_CRITICAL_STEP_INDEX_KEY]),
                   int(dictionary[DOWNSTREAM_CRITICAL_STEP_INDEX_KEY]))
