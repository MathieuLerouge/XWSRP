# Local libraries
from src.modeling.task import Task
from src.modeling.unavailability import Unavailability
from src.utils.location import Location
from src.utils.time import convert_nb_minutes_to_time_string, TWELVE_HOURS_FORMAT
from src.utils.timeset import TimeInterval


############
# Employee #
############

class Employee:
    """
    An employee available to be assigned to tasks within a working-time window.
    """

    def __init__(self, name: str, start_time_lb: int, end_time_ub: int, location: Location, skill_level: int):
        """
        Args:
            name: Unique identifier of the employee.
            start_time_lb: Lower bound, in minutes since midnight, of the employee's working-time window.
            end_time_ub: Upper bound, in minutes since midnight, of the employee's working-time window.
            location: Location the employee starts/ends their working day from.
            skill_level: Skill level of the employee, compared against a task's skill level to check eligibility.
        """
        self._name = name
        self._start_time_lb = start_time_lb
        self._end_time_ub = end_time_ub
        self._location = location
        self._skill_level = skill_level
        self._nb_unavailabilities = 0
        self._unavailabilities: dict[str, Unavailability] = dict()

    def __eq__(self, employee):
        if isinstance(employee, Employee):
            return self.name == employee._name
        else:
            return False

    def __hash__(self):
        return hash(self._name)

    def __repr__(self):
        return (
            f"{self.name}: working during {TimeInterval(self._start_time_lb, self._end_time_ub)} "
            f"located at {self.location} having skill {self._skill_level} "
            f"and having {self._nb_unavailabilities} unavailability(ies)"
        )

    @property
    def name(self):
        """Unique identifier of the employee."""
        return self._name

    @property
    def start_time_lb(self):
        """Lower bound, in minutes since midnight, of the employee's working-time window."""
        return self._start_time_lb

    def get_start_time_lb(self, as_integer: bool = True, hour_format: str = TWELVE_HOURS_FORMAT):
        """
        Returns the employee's working-time lower bound.

        Args:
            as_integer: If True, return the bound as a number of minutes since midnight.
                If False, return it as a formatted string.
            hour_format: Format used for the string when as_integer is False.

        Returns:
            The lower bound as an int (minutes) or as a formatted str, depending on as_integer.
        """
        if as_integer:
            return self._start_time_lb
        else:
            return convert_nb_minutes_to_time_string(self._start_time_lb, hour_format)

    @property
    def end_time_ub(self):
        """Upper bound, in minutes since midnight, of the employee's working-time window."""
        return self._end_time_ub

    def get_end_time_ub(self, as_integer: bool = True, hour_format: str = TWELVE_HOURS_FORMAT):
        """
        Returns the employee's working-time upper bound.

        Args:
            as_integer: If True, return the bound as a number of minutes since midnight.
                If False, return it as a formatted string.
            hour_format: Format used for the string when as_integer is False.

        Returns:
            The upper bound as an int (minutes) or as a formatted str, depending on as_integer.
        """
        if as_integer:
            return self._end_time_ub
        else:
            return convert_nb_minutes_to_time_string(self._end_time_ub, hour_format)

    @property
    def time_window(self):
        """Returns the employee's working-time window (between start_time_lb and end_time_ub) as a TimeInterval."""
        return TimeInterval(self._start_time_lb, self._end_time_ub)

    @property
    def location(self):
        """Location the employee starts/ends their working day from."""
        return self._location

    @property
    def skill_level(self):
        """Skill level of the employee, compared against a task's required skill level to check eligibility."""
        return self._skill_level

    @property
    def nb_unavailabilities(self):
        """Number of unavailability periods declared for this employee."""
        return self._nb_unavailabilities

    @property
    def has_unavailabilities(self):
        """Whether this employee has at least one declared unavailability period."""
        return self._nb_unavailabilities > 0

    @property
    def unavailabilities(self) -> list[Unavailability]:
        """Unavailability periods declared for this employee."""
        return list(self._unavailabilities.values())

    def add_unavailability(self, location: Location, start_time: int, end_time: int) -> None:
        """
        Registers a new unavailability period for this employee.

        Args:
            location: Location where the employee is unavailable.
            start_time: Start of the unavailability, in minutes since midnight.
            end_time: End of the unavailability, in minutes since midnight.

        Raises:
            ValueError: If an identical unavailability (same location, start time, and end time)
                is already registered for this employee.
        """
        for unavailability in self._unavailabilities.values():
            if (
                unavailability.location == location
                and unavailability.start_time_lb == start_time
                and unavailability.end_time_ub == end_time
            ):
                raise ValueError(f"The given unavailability is already among {self.name}'s unavailabilities")
        self._nb_unavailabilities += 1
        unavailability_name = f"U{self._nb_unavailabilities}"
        self._unavailabilities[unavailability_name] = Unavailability(
            employee=self,
            name=unavailability_name,
            location=location,
            start_time=start_time,
            end_time=end_time,
        )

    def get_unavailability_by_name(self, unavailability_name: str) -> Unavailability:
        """
        Returns the unavailability registered under the given name.

        Args:
            unavailability_name: Name the unavailability was registered under (see add_unavailability).

        Returns:
            The matching Unavailability instance.
        """
        return self._unavailabilities[unavailability_name]

    def is_capable_of_performing(self, task: Task) -> bool:
        """
        Returns whether this employee's skill level is sufficient for a task.

        Args:
            task: Task to check eligibility for.

        Returns:
            True if the employee's skill_level is at least the task's required skill_level, False otherwise.
        """
        return self._skill_level >= task.skill_level
