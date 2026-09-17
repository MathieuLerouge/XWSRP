# Local libraries
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.modeling.unavailability import Unavailability
from src.feasibility.violation.violation import Violation
from src.utils.timeset import TimeInterval


###################################
# EmployeeUnavailabilityViolation #
###################################

class EmployeeUnavailabilityViolation(Violation):
    """
    A task performed while the assigned employee is unavailable.
    """

    def __init__(self, task: Task, employee: Employee, start_time: int, end_time: int,
                 unavailability: Unavailability):
        """
        Args:
            task: Task performed while the employee is unavailable.
            employee: Employee assigned to the task.
            start_time: Start time at which the task is performed, in minutes since midnight.
            end_time: End time at which the task is performed, in minutes since midnight.
            unavailability: Unavailability period conflicting with the task.
        """
        self._task = task
        self._employee = employee
        self._start_time = start_time
        self._end_time = end_time
        self._unavailability = unavailability

    @property
    def task(self):
        """Task performed while the employee is unavailable."""
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
    def unavailability(self):
        """Unavailability period conflicting with the task."""
        return self._unavailability

    @property
    def text(self):
        """Human-readable description of this violation."""
        return (f"Task {self._task.name} is supposed to be performed "
                f"over {TimeInterval(self._start_time, self._end_time)} by employee {self._employee.name} "
                f"while he/she is unavailable over {self._unavailability.time_windows[0]} "
                f"due to his/her unavailability {self._unavailability.name}.")
