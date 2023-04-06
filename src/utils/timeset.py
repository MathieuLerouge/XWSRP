#! /usr/bin/env python3
# coding: utf-8


# Local libraries
from src.utils.intset import IntInterval, IntIntervalUnion
from src.utils.time import convert_nb_minutes_to_time_string, TWELVE_HOURS_FORMAT


# Class TimeInterval
class TimeInterval(IntInterval):

    @classmethod
    def from_IntInterval(cls, interval: IntInterval):
        return cls(interval.lower_bound, interval.upper_bound)

    def as_string(self, hour_format: str = TWELVE_HOURS_FORMAT):
        if self.is_empty():
            return "Ø"
        else:
            return f"[{convert_nb_minutes_to_time_string(self._lower_bound, hour_format)};" \
                   f"{convert_nb_minutes_to_time_string(self._upper_bound, hour_format)}]"

    def __repr__(self):
        return self.as_string()

    def intersect(self, interval):
        return self.from_IntInterval(super().intersect(interval))

    # def subtract(self, interval_to_subtract):
    #     # TODO to preserve TimeSet type and not IntSet

    def copy(self):
        return self.from_IntInterval(super().copy())


# Class TimeIntervalUnion
class TimeIntervalUnion(IntIntervalUnion):

    # def __init__(self, intervals=[]):
    #     # TODO

    @classmethod
    def from_IntIntervalUnion(cls, union: IntIntervalUnion):
        return cls([TimeInterval.from_IntInterval(interval) for interval in union.intervals])

    def as_string(self, hour_format: str = TWELVE_HOURS_FORMAT):
        if self.is_empty():
            return "Ø"
        else:
            return " U ".join([interval.as_string(hour_format) for interval in self._intervals])

    def __repr__(self):
        return self.as_string()

    def subtract(self, interval_to_subtract: TimeInterval):
        return self.from_IntIntervalUnion(super().subtract(interval_to_subtract))


# Main function
def main():

    # Create empty interval
    interval1 = TimeInterval()
    print(interval1)

    # Create [0, 10] interval
    interval2 = TimeInterval(0, 10)
    print(interval2)

    # Create [8, 13] interval
    interval3 = TimeInterval(8, 13)
    print(interval3)

    # Create [0, 5] interval
    interval4 = TimeInterval(0, 5)
    print(interval4)

    # Create [5, 10] interval
    interval5 = TimeInterval(5, 10)
    print(interval5)

    # Create [2, 7] interval
    interval6 = TimeInterval(2, 7)
    print(interval6)

    # Copy intervals
    print("Copies")
    print(interval1.copy())
    print(interval2.copy())

    # Intersect intervals
    print("Intersections")
    print(interval1.intersect(interval2))
    print(interval2.intersect(interval1))
    print(interval2.intersect(interval3))
    print(interval3.intersect(interval2))
    print(interval2.intersect(interval4))
    print(interval4.intersect(interval2))
    print(interval2.intersect(interval5))
    print(interval5.intersect(interval2))
    print(interval2.intersect(interval6))
    print(interval6.intersect(interval2))

    # Subtract intervals
    print("Subtractions")
    print(interval1.subtract(interval2))
    print(interval2.subtract(interval1))
    print(interval2.subtract(interval3))
    print(interval3.subtract(interval2))
    print(interval2.subtract(interval4))
    print(interval4.subtract(interval2))
    print(interval2.subtract(interval5))
    print(interval5.subtract(interval2))
    print(interval2.subtract(interval6))
    print(interval6.subtract(interval2))
    print(interval2.subtract(interval2))


if __name__ == '__main__':
    main()
