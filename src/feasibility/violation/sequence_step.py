# Local libraries
from src.modeling.employee import Employee
from src.modeling.step import Step
from src.feasibility.violation.violation import Violation
from src.utils.timeset import convert_nb_minutes_to_time_string


#########################
# SequenceStepViolation #
#########################

class SequenceStepViolation(Violation):
    """
    Two consecutive steps of an employee's sequence separated by less than their actual traveling duration.
    """

    def __init__(self, employee: Employee, previous_step: Step, step: Step, crosses_lunch_break: bool,
                 allowed_traveling_duration: int, actual_traveling_duration: int):
        """
        Args:
            employee: Employee whose sequence has the two consecutive steps.
            previous_step: Earlier of the two consecutive steps.
            step: Later of the two consecutive steps.
            crosses_lunch_break: Whether the employee's lunch break is taken between previous_step and step.
            allowed_traveling_duration: Duration, in minutes, available to travel between previous_step and
                step (accounting for the lunch break, if crosses_lunch_break is True).
            actual_traveling_duration: Actual duration, in minutes, of the travel between previous_step's and
                step's activities.
        """
        self._employee = employee
        self._previous_step = previous_step
        self._step = step
        self._crosses_lunch_break = crosses_lunch_break
        self._allowed_traveling_duration = allowed_traveling_duration
        self._actual_traveling_duration = actual_traveling_duration

    @property
    def employee(self):
        """Employee whose sequence has the two consecutive steps."""
        return self._employee

    @property
    def previous_step(self):
        """Earlier of the two consecutive steps."""
        return self._previous_step

    @property
    def step(self):
        """Later of the two consecutive steps."""
        return self._step

    @property
    def crosses_lunch_break(self):
        """Whether the employee's lunch break is taken between previous_step and step."""
        return self._crosses_lunch_break

    @property
    def allowed_traveling_duration(self):
        """Duration, in minutes, available to travel between previous_step and step."""
        return self._allowed_traveling_duration

    @property
    def actual_traveling_duration(self):
        """Actual duration, in minutes, of the travel between previous_step's and step's activities."""
        return self._actual_traveling_duration

    @property
    def text(self):
        """Human-readable description of this violation."""
        previous_activity_name = self._previous_step.activity.name
        activity_name = self._step.activity.name
        if self._crosses_lunch_break:
            middle_part = (f"then have a lunch break and perform {activity_name} at "
                           f"{convert_nb_minutes_to_time_string(self._step.start_time)}.")
        else:
            middle_part = (f"then perform {activity_name} at "
                           f"{convert_nb_minutes_to_time_string(self._step.start_time)}.")
        return (f"{self._employee.name} is supposed to perform "
                f"{previous_activity_name} at "
                f"{convert_nb_minutes_to_time_string(self._previous_step.start_time)}, "
                f"{middle_part} "
                f"It means that {self._employee.name} is supposed to travel from "
                f"{previous_activity_name} to {activity_name} "
                f"in less than {self._allowed_traveling_duration}min. "
                f"However, such a travel takes {self._actual_traveling_duration}min.")
