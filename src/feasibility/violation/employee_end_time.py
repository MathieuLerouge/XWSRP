# Local libraries
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.feasibility.violation.violation import Violation
from src.utils.timeset import TimeInterval, convert_nb_minutes_to_time_string


############################
# EmployeeEndTimeViolation #
############################

class EmployeeEndTimeViolation(Violation):
    """
    A task performed after the assigned employee's working-time upper bound.
    """

    def __init__(self, task: Task, employee: Employee, start_time: int, end_time: int):
        """
        Args:
            task: Task performed after the employee's working-time upper bound.
            employee: Employee assigned to the task.
            start_time: Start time at which the task is performed, in minutes since midnight.
            end_time: End time at which the task is performed, in minutes since midnight.
        """
        self._task = task
        self._employee = employee
        self._start_time = start_time
        self._end_time = end_time

    @property
    def task(self):
        """Task performed after the employee's working-time upper bound."""
        return self._task

    @property
    def employee(self):
        """Employee assigned to the task."""
        return self._employee

    @property
    def start_time(self):
        """Start time at which the task is performed, in minutes since midnight."""
        return self._start_time

    @property
    def end_time(self):
        """End time at which the task is performed, in minutes since midnight."""
        return self._end_time

    @property
    def text(self):
        """Human-readable description of this violation."""
        return (f"Task {self._task.name} is supposed to be performed over "
                f"{TimeInterval(self._start_time, self._end_time)} by employee {self._employee.name} "
                f"while he/she must end working at "
                f"{convert_nb_minutes_to_time_string(self._employee.end_time_ub)}.")
