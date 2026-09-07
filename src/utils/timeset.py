# Standard library
from typing import cast

# Local libraries
from src.utils.intset import IntInterval, IntIntervalUnion
from src.utils.time import convert_nb_minutes_to_time_string, TWELVE_HOURS_FORMAT


################
# TimeInterval #
################

class TimeInterval(IntInterval):
    """
    An IntInterval whose bounds are minutes since midnight, printable as clock times via as_string().
    """

    @classmethod
    def from_IntInterval(cls, interval: IntInterval):
        """
        Returns a TimeInterval with the same bounds as the given IntInterval.

        Args:
            interval: Interval whose bounds to copy.

        Returns:
            A new TimeInterval.
        """
        return cls(interval.lower_bound, interval.upper_bound)

    def as_string(self, hour_format: str = TWELVE_HOURS_FORMAT):
        """
        Returns the interval as a "[start;end]" string, with bounds formatted as clock times.

        Args:
            hour_format: Hour format to render the bounds in.

        Returns:
            The formatted interval string, or "Ø" if the interval is empty.
        """
        if self.is_empty():
            return "Ø"
        else:
            return (
                f"[{convert_nb_minutes_to_time_string(self._lower_bound, hour_format)};"
                f"{convert_nb_minutes_to_time_string(self._upper_bound, hour_format)}]"
            )

    def __repr__(self):
        return self.as_string()

    def intersect(self, interval):
        """Returns the intersection with the given interval, as a TimeInterval (see IntInterval.intersect)."""
        return self.from_IntInterval(super().intersect(interval))

    def subtract(self, interval_to_subtract):
        """
        Returns the difference with the given interval, as a TimeInterval or TimeIntervalUnion.

        See IntInterval.subtract.
        """
        result = super().subtract(interval_to_subtract)
        if isinstance(result, IntIntervalUnion):
            return TimeIntervalUnion.from_IntIntervalUnion(result)
        else:
            return self.from_IntInterval(result)

    def copy(self):
        """Returns a new TimeInterval with the same bounds as this one."""
        return self.from_IntInterval(super().copy())


#####################
# TimeIntervalUnion #
#####################

class TimeIntervalUnion(IntIntervalUnion):
    """
    An IntIntervalUnion of TimeInterval ranges, printable as clock times via as_string().
    """

    # def __init__(self, intervals=[]):
    #     # TODO

    @classmethod
    def from_IntIntervalUnion(cls, union: IntIntervalUnion):
        """
        Returns a TimeIntervalUnion with the same intervals as the given IntIntervalUnion.

        Args:
            union: Union whose intervals to copy.

        Returns:
            A new TimeIntervalUnion.
        """
        return cls([TimeInterval.from_IntInterval(interval) for interval in union.intervals])

    @property
    def intervals(self) -> list[TimeInterval]:
        """The disjoint TimeInterval ranges making up this union."""
        return cast(list[TimeInterval], self._intervals)

    def as_string(self, hour_format: str = TWELVE_HOURS_FORMAT):
        """
        Returns the union as a "U"-separated string of its intervals, formatted as clock times.

        Args:
            hour_format: Hour format to render the bounds in.

        Returns:
            The formatted union string, or "Ø" if the union is empty.
        """
        if self.is_empty():
            return "Ø"
        else:
            return " U ".join([interval.as_string(hour_format) for interval in self.intervals])

    def __repr__(self):
        return self.as_string()

    def subtract(self, interval_to_subtract: TimeInterval):
        """
        Returns this union with interval_to_subtract removed, as a TimeIntervalUnion.

        See IntIntervalUnion.subtract.
        """
        return self.from_IntIntervalUnion(super().subtract(interval_to_subtract))

    def intersect(self, interval_to_intersect: TimeInterval):
        """
        Returns the intersection of this union with interval_to_intersect, as a TimeIntervalUnion.

        See IntIntervalUnion.intersect.
        """
        return self.from_IntIntervalUnion(super().intersect(interval_to_intersect))
