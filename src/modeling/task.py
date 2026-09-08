# Local libraries
from src.modeling.activity import Activity
from src.utils.timeset import TimeInterval
from src.utils.location import Location


########
# Task #
########

class Task(Activity):
    """
    A task that can be assigned to an eligible employee within its time window.
    """

    def __init__(self, name: str, duration: int, start_time_lb: int, end_time_ub: int,
                 skill_level: int, location: Location):
        """
        Args:
            name: Unique identifier of the task.
            duration: Duration of the task, in minutes.
            start_time_lb: Lower bound, in minutes since midnight, of the task's time window.
            end_time_ub: Upper bound, in minutes since midnight, of the task's time window.
            skill_level: Skill level required to perform the task.
            location: Location where the task takes place.
        """
        super().__init__(name, duration, start_time_lb, end_time_ub, skill_level, location)
        self._has_unavailability = False

    def __eq__(self, task):
        if isinstance(task, Task) and task.name == self.name:
            return True
        else:
            return False

    def __lt__(self, task):
        return self.name < task.name

    def __hash__(self):
        return hash(self._name)

    def apply_unavailability(self, unavailability_start_time: int, unavailability_end_time: int) -> None:
        """
        Removes the given unavailability period from the task's time window.

        Args:
            unavailability_start_time: Start of the unavailability, in minutes since midnight.
            unavailability_end_time: End of the unavailability, in minutes since midnight.
        """
        self._time_windows = self._time_windows.subtract(
            TimeInterval(lower_bound=unavailability_start_time, upper_bound=unavailability_end_time)
        )
        self._has_unavailability = True

    @property
    def has_unavailability(self):
        """Whether an unavailability period has been applied to this task's time window."""
        return self._has_unavailability
