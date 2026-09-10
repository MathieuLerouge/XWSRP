# Standard library
from typing import Optional

# Local libraries
from src.modeling.activity import Activity
from src.utils.time import convert_nb_minutes_to_time_string, TWELVE_HOURS_FORMAT


####################
# Global variables #
####################

BRACKET_LEFT_STRING = '{'
BRACKET_RIGHT_STRING = '}'


########
# Step #
########

class Step:
    """
    A step i.e. an activity together with its arrival, start, and end times.
    """

    def __init__(self, activity: Activity, arrival_time: Optional[int] = None, start_time: Optional[int] = None,
                 end_time: Optional[int] = None):
        """
        Args:
            activity: Activity performed during this step.
            arrival_time: Time, in minutes since midnight, the employee arrives at the activity's location.
            start_time: Time, in minutes since midnight, the activity starts.
            end_time: Time, in minutes since midnight, the activity ends.
        """
        self._activity = activity
        self._arrival_time = arrival_time
        self._start_time = start_time
        self._end_time = end_time

    def __eq__(self, step):
        """
        Returns whether this step has the same activity and start/end times as step.

        arrival_time is intentionally excluded: it only reflects travel/waiting timing,
        not what is actually scheduled to happen (which activity, and when it starts/ends),
        so two steps that differ only in arrival_time are still considered equal.

        Args:
            step: Object to compare this step to.

        Returns:
            bool: True if step is a Step with the same activity name, start_time and end_time.
        """
        return (
            isinstance(step, Step) and self.activity.name == step.activity.name and
            self.start_time == step.start_time and self.end_time == step.end_time
        )

    def __lt__(self, step):
        """
        Raises:
            ValueError: If either step has no start_time.
        """
        self_start_time = self.start_time
        step_start_time = step.start_time
        if self_start_time is None or step_start_time is None:
            raise ValueError(f"Cannot compare steps with no start_time: {self} and {step}")
        return (
            self_start_time < step_start_time or
            (self_start_time == step_start_time and self.activity.duration == 0)
        )

    def __repr__(self):
        parts = []
        if self._arrival_time is not None:
            parts.append(f"Ta={convert_nb_minutes_to_time_string(self._arrival_time)}({self._arrival_time})")
        if self._start_time is not None:
            parts.append(f"Ts={convert_nb_minutes_to_time_string(self._start_time)}({self._start_time})")
        if self._end_time is not None:
            parts.append(f"Te={convert_nb_minutes_to_time_string(self._end_time)}({self._end_time})")
        return f"{BRACKET_LEFT_STRING}{self._activity.name}: " + ", ".join(parts) + BRACKET_RIGHT_STRING

    @property
    def activity(self):
        """Activity performed during this step."""
        return self._activity

    @property
    def arrival_time(self):
        """Time, in minutes since midnight, the employee arrives at the activity's location."""
        return self._arrival_time

    @property
    def start_time(self):
        """Time, in minutes since midnight, the activity starts."""
        return self._start_time

    def get_start_time(self, as_string=False, hour_format=TWELVE_HOURS_FORMAT):
        """
        Returns the step's start time.

        Args:
            as_string: If True, return the start time as a formatted string. If False, return it as an int.
            hour_format: Format used for the string when as_string is True.

        Returns:
            The start time as an int (minutes) or as a formatted str, depending on as_string.

        Raises:
            ValueError: If this step has no start_time.
        """
        if self._start_time is None:
            raise ValueError(f"This step {self} has no start_time")
        if as_string:
            return convert_nb_minutes_to_time_string(self._start_time, hour_format)
        else:
            return self._start_time

    @property
    def end_time(self):
        """Time, in minutes since midnight, the activity ends."""
        return self._end_time

    def get_end_time(self, as_string=False, hour_format=TWELVE_HOURS_FORMAT):
        """
        Returns the step's end time.

        Args:
            as_string: If True, return the end time as a formatted string. If False, return it as an int.
            hour_format: Format used for the string when as_string is True.

        Returns:
            The end time as an int (minutes) or as a formatted str, depending on as_string.

        Raises:
            ValueError: If this step has no end_time.
        """
        if self._end_time is None:
            raise ValueError(f"This step {self} has no end_time")
        if as_string:
            return convert_nb_minutes_to_time_string(self._end_time, hour_format)
        else:
            return self._end_time

    @activity.setter
    def activity(self, activity: Activity):
        self._activity = activity

    @arrival_time.setter
    def arrival_time(self, arrival_time: int):
        self._arrival_time = arrival_time

    @start_time.setter
    def start_time(self, start_time: int):
        self._start_time = start_time
        if self._end_time is None:
            self._end_time = self._start_time + self._activity.duration

    @end_time.setter
    def end_time(self, end_time: int):
        self._end_time = end_time

    def clear(self) -> None:
        """Resets the activity and all times of this step to None."""
        self._activity = None
        self._arrival_time = None
        self._start_time = None
        self._end_time = None

    def copy(self) -> "Step":
        """Returns a new Step with the same activity and times as this one."""
        return Step(self._activity, self._arrival_time, self._start_time, self._end_time)
