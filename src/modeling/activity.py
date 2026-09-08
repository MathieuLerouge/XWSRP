# Standard library
from typing import Optional

# Local libraries
from src.utils.location import Location
from src.utils.time import convert_nb_minutes_to_time_string, TWELVE_HOURS_FORMAT
from src.utils.timeset import TimeInterval, TimeIntervalUnion


############
# Activity #
############

class Activity:
    """
    An activity (e.g. a task) that can be part of an employee's sequence.
    """

    def __init__(self, name: str, duration: int = 0, start_time_lb: Optional[int] = None,
                 end_time_ub: Optional[int] = None, skill_level: int = 0, location: Optional[Location] = None):
        """
        Args:
            name: Unique identifier of the activity.
            duration: Duration of the activity, in minutes.
            start_time_lb: Lower bound, in minutes since midnight, of the activity's time window.
            end_time_ub: Upper bound, in minutes since midnight, of the activity's time window.
            skill_level: Skill level required to perform the activity.
            location: Location where the activity takes place.
        """
        self._name = name
        self._employee = None
        self._duration = duration
        self._start_time_lb = start_time_lb
        self._end_time_ub = end_time_ub
        self._time_windows = TimeIntervalUnion([TimeInterval(lower_bound=start_time_lb, upper_bound=end_time_ub)])
        self._skill_level = skill_level
        self._location = location

    def __repr__(self):
        location_repr = self._location if self._location is not None else "no location"
        return (f"{self._name}: {self._duration}min in {self._time_windows} "
                f"at {location_repr} requiring level {self._skill_level}")

    @property
    def name(self):
        """Unique identifier of the activity."""
        return self._name

    @property
    def employee(self):
        """Employee assigned to this activity, if any."""
        return self._employee

    @property
    def duration(self):
        """Duration of the activity, in minutes."""
        return self._duration

    def get_duration(self, as_integer: bool = True):
        """
        Returns the activity's duration.

        Args:
            as_integer: If True, return the duration as a number of minutes.
                If False, return it as a formatted string.

        Returns:
            The duration as an int (minutes) or as a formatted str, depending on as_integer.
        """
        if as_integer:
            return self._duration
        else:
            return str(self._duration) + "min"

    @property
    def start_time_lb(self):
        """Lower bound, in minutes since midnight, of the activity's time window."""
        return self._start_time_lb

    def get_start_time_lb(self, as_integer: bool = True, hour_format: str = TWELVE_HOURS_FORMAT):
        """
        Returns the activity's time window lower bound.

        Args:
            as_integer: If True, return the bound as a number of minutes since midnight.
                If False, return it as a formatted string.
            hour_format: Format used for the string when as_integer is False.

        Returns:
            The lower bound as an int (minutes) or as a formatted str, depending on as_integer.

        Raises:
            ValueError: If this activity has no start_time_lb.
        """
        if self._start_time_lb is None:
            raise ValueError(f"This activity {self} has no start_time_lb")
        if as_integer:
            return self._start_time_lb
        else:
            return convert_nb_minutes_to_time_string(self._start_time_lb, hour_format)

    @property
    def end_time_ub(self):
        """Upper bound, in minutes since midnight, of the activity's time window."""
        return self._end_time_ub

    def get_end_time_ub(self, as_integer: bool = True, hour_format: str = TWELVE_HOURS_FORMAT):
        """
        Returns the activity's time window upper bound.

        Args:
            as_integer: If True, return the bound as a number of minutes since midnight. If False, return it
                as a formatted string.
            hour_format: Format used for the string when as_integer is False.

        Returns:
            The upper bound as an int (minutes) or as a formatted str, depending on as_integer.

        Raises:
            ValueError: If this activity has no end_time_ub.
        """
        if self._end_time_ub is None:
            raise ValueError(f"This activity {self} has no end_time_ub")
        if as_integer:
            return self._end_time_ub
        else:
            return convert_nb_minutes_to_time_string(self._end_time_ub, hour_format)

    @property
    def time_windows(self):
        """The activity's time window, as a TimeIntervalUnion (possibly split by unavailabilities)."""
        return self._time_windows

    @property
    def location(self):
        """Location where the activity takes place."""
        return self._location

    @property
    def skill_level(self):
        """Skill level required to perform the activity."""
        return self._skill_level

    def distance_to(self, activity: "Activity") -> float:
        """
        Returns the distance, in km, to another activity.

        Args:
            activity: Activity to compute the distance to.

        Returns:
            The distance in km.

        Raises:
            AttributeError: If this activity has no location.
            ValueError: If the given activity has no location, or if the two activities' locations don't use
                the same coordinate system (geographic or cartesian).
        """
        self_location = self.location
        activity_location = activity.location
        if self_location is None or self_location.is_empty():
            raise AttributeError(f"This activity {self} has no location")
        if activity_location is None or activity_location.is_empty():
            raise ValueError(f"The given activity {activity} has no location")
        return self_location.distance_to(activity_location)
