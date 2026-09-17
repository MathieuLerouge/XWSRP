# Local libraries
from src.modeling.employee import Employee
from src.feasibility.violation.violation import Violation
from src.utils.timeset import TimeInterval


#############################
# LunchBreakWindowViolation #
#############################

class LunchBreakWindowViolation(Violation):
    """
    A lunch break taken outside of its dedicated time window.
    """

    def __init__(self, employee: Employee, lunch_break_start_time: int, lunch_break_end_time: int,
                 lunch_break_time_lb: int, lunch_break_time_ub: int):
        """
        Args:
            employee: Employee whose lunch break is taken outside of its dedicated time window.
            lunch_break_start_time: Start time of the employee's lunch break, in minutes since midnight.
            lunch_break_end_time: End time of the employee's lunch break, in minutes since midnight.
            lunch_break_time_lb: Lower bound, in minutes since midnight, of the dedicated lunch break time window.
            lunch_break_time_ub: Upper bound, in minutes since midnight, of the dedicated lunch break time window.
        """
        self._employee = employee
        self._lunch_break_start_time = lunch_break_start_time
        self._lunch_break_end_time = lunch_break_end_time
        self._lunch_break_time_lb = lunch_break_time_lb
        self._lunch_break_time_ub = lunch_break_time_ub

    @property
    def employee(self):
        """Employee whose lunch break is taken outside of its dedicated time window."""
        return self._employee

    @property
    def lunch_break_start_time(self):
        """Start time of the employee's lunch break, in minutes since midnight."""
        return self._lunch_break_start_time

    @property
    def lunch_break_end_time(self):
        """End time of the employee's lunch break, in minutes since midnight."""
        return self._lunch_break_end_time

    @property
    def lunch_break_time_lb(self):
        """Lower bound, in minutes since midnight, of the dedicated lunch break time window."""
        return self._lunch_break_time_lb

    @property
    def lunch_break_time_ub(self):
        """Upper bound, in minutes since midnight, of the dedicated lunch break time window."""
        return self._lunch_break_time_ub

    @property
    def text(self):
        """Human-readable description of this violation."""
        return (f"{self._employee.name} is supposed to have a lunch break over "
                f"{TimeInterval(self._lunch_break_start_time, self._lunch_break_end_time)} "
                f"while lunch break must be within "
                f"{TimeInterval(self._lunch_break_time_lb, self._lunch_break_time_ub)}.")
