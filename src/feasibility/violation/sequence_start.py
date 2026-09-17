# Local libraries
from src.modeling.employee import Employee
from src.modeling.step import Step
from src.feasibility.violation.violation import Violation
from src.utils.timeset import convert_nb_minutes_to_time_string


##########################
# SequenceStartViolation #
##########################

class SequenceStartViolation(Violation):
    """
    An employee's departure step scheduled to make them start working before their working-time lower bound.
    """

    def __init__(self, employee: Employee, departure_step: Step, first_step: Step):
        """
        Args:
            employee: Employee whose sequence starts too early.
            departure_step: Employee's departure step, from their initial location.
            first_step: First task step of the employee's sequence.
        """
        self._employee = employee
        self._departure_step = departure_step
        self._first_step = first_step

    @property
    def employee(self):
        """Employee whose sequence starts too early."""
        return self._employee

    @property
    def departure_step(self):
        """Employee's departure step, from their initial location."""
        return self._departure_step

    @property
    def first_step(self):
        """First task step of the employee's sequence."""
        return self._first_step

    @property
    def text(self):
        """Human-readable description of this violation."""
        return (f"{self._employee.name} is supposed to perform "
                f"task {self._first_step.activity.name} at "
                f"{convert_nb_minutes_to_time_string(self._first_step.start_time)}, "
                f"which means that he/she is supposed to leave their initial location at "
                f"{convert_nb_minutes_to_time_string(self._departure_step.start_time)}. "
                f"However, he/she must not start to work before "
                f"{convert_nb_minutes_to_time_string(self._employee.start_time_lb)}.")
