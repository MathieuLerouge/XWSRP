# Local libraries
from src.utils.timeset import TimeInterval


###################
# LunchBreakRules #
###################

class LunchBreakRules:
    """
    The rules governing when and for how long employees can take their lunch break in an instance.
    """

    def __init__(self, lower_bound: int, upper_bound: int, duration: int):
        """
        Args:
            lower_bound: Lower bound, in minutes since midnight, of the time window during which
                the lunch break must take place.
            upper_bound: Upper bound, in minutes since midnight, of the time window during which
                the lunch break must take place.
            duration: Duration of the lunch break, in minutes.
        """
        self._time_window = TimeInterval(lower_bound, upper_bound)
        self._duration = duration

    @property
    def time_window(self) -> TimeInterval:
        """Time window during which the lunch break must take place."""
        return self._time_window

    @property
    def lower_bound(self) -> int:
        """Lower bound, in minutes since midnight, of the lunch break's time window."""
        return self._time_window.lower_bound

    @property
    def upper_bound(self) -> int:
        """Upper bound, in minutes since midnight, of the lunch break's time window."""
        return self._time_window.upper_bound

    @property
    def duration(self) -> int:
        """Duration of the lunch break, in minutes."""
        return self._duration
