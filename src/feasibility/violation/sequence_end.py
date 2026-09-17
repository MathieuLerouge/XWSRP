# Local libraries
from src.modeling.employee import Employee
from src.modeling.step import Step
from src.feasibility.violation.violation import Violation
from src.utils.timeset import convert_nb_minutes_to_time_string


########################
# SequenceEndViolation #
########################

class SequenceEndViolation(Violation):
    """
    An employee's comeback step scheduled to make them end working after their working-time upper bound.
    """

    def __init__(self, employee: Employee, last_step: Step, comeback_step: Step):
        """
        Args:
            employee: Employee whose sequence ends too late.
            last_step: Last task step of the employee's sequence.
            comeback_step: Employee's comeback step, to their final location.
        """
        self._employee = employee
        self._last_step = last_step
        self._comeback_step = comeback_step

    @property
    def employee(self):
        """Employee whose sequence ends too late."""
        return self._employee

    @property
    def last_step(self):
        """Last task step of the employee's sequence."""
        return self._last_step

    @property
    def comeback_step(self):
        """Employee's comeback step, to their final location."""
        return self._comeback_step

    @property
    def text(self):
        """Human-readable description of this violation."""
        return (f"{self._employee.name} is supposed perform "
                f"{self._last_step.activity.name} at "
                f"{convert_nb_minutes_to_time_string(self._last_step.start_time)} "
                f"and then go to his/her final location, "
                f"which means that he/she is supposed to be at his/her final location at "
                f"{convert_nb_minutes_to_time_string(self._comeback_step.arrival_time)}. "
                f"However, {self._employee.name} must end to work no later than "
                f"{convert_nb_minutes_to_time_string(self._employee.end_time_ub)}.")
