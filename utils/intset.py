#! /usr/bin/env python3
# coding: utf-8

# Remark: it is not possible to separate IntInterval and IntIntervalUnion classes in different files
# as they need each other to be defined

# Class IntSet
class IntSet:

    def __init__(self):
        pass

    def __getitem__(self, index):
        return None

    def clear(self):
        pass

    def is_empty(self):
        return True

    def contain(self, value):
        return False

    def subtract(self, int_set):
        return None

    def intersect(self, int_set):
        return None


# Class IntInterval
class IntInterval(IntSet):

    def __init__(self, lower_bound=None, upper_bound=None):
        """
        Create a closed integer interval given lower and upper bounds
        (if both bounds are None, the interval is considered empty)

        :param lower_bound: lower bound (int)
        :param upper_bound: upper bound (int)
        """
        super().__init__()
        self._lower_bound = None
        self._upper_bound = None
        self.set(lower_bound, upper_bound)

    def __getitem__(self, index):
        if self.is_empty():
            raise ValueError("this interval is empty")
        else:
            if index == 0:
                return self._lower_bound
            elif index == 1:
                return self._lower_bound
            else:
                raise ValueError("index must 0 or 1")

    def __repr__(self):
        if self.is_empty():
            return "Ø"
        else:
            return f"[{self._lower_bound};{self._upper_bound}]"

    @property
    def lower_bound(self):
        return self._lower_bound

    @property
    def upper_bound(self):
        return self._upper_bound

    @lower_bound.setter
    def lower_bound(self, lower_bound):
        if lower_bound is None:
            if self._upper_bound is not None:
                raise TypeError("lower bound can not be None because upper bound is int, use set_bounds")
        else:
            if not isinstance(lower_bound, int):
                raise TypeError("lower bound must be int or None")
            elif self._upper_bound is None:
                raise TypeError("lower bound can not be int because upper bound is None, use set_bounds")
            elif self._lower_bound > self._upper_bound:
                raise ValueError("lower bound must be smaller than upper bound")
        self._lower_bound = lower_bound

    @upper_bound.setter
    def upper_bound(self, upper_bound):
        if upper_bound is None:
            if self._lower_bound is not None:
                raise TypeError("upper bound can not be None because lower bound is int, use set_bounds")
        else:
            if not isinstance(upper_bound, int):
                raise TypeError("upper bound must be int or None")
            elif self._lower_bound is None:
                raise TypeError("upper bound can not be int because lower bound is None, use set_bounds")
            elif self._lower_bound > self._upper_bound:
                raise ValueError("upper bound must be larger than lower bound")
        self._upper_bound = upper_bound

    def set(self, lower_bound=None, upper_bound=None):
        if (lower_bound is None and upper_bound is not None) or (lower_bound is not None and upper_bound is None):
            raise TypeError("either both lower and upper bounds must be None, or both must be int")
        elif lower_bound is not None:
            if not (isinstance(lower_bound, int) and isinstance(upper_bound, int)):
                raise TypeError("both lower and upper bounds must be int, if they are not both None")
            elif lower_bound > upper_bound:
                raise ValueError("lower bound must be smaller than upper bound")
        self._lower_bound = lower_bound
        self._upper_bound = upper_bound

    def clear(self):
        self.set()

    def is_empty(self):
        return self._lower_bound is None

    def copy(self):
        return IntInterval(lower_bound=self._lower_bound, upper_bound=self._upper_bound)

    def contain(self, value):
        """
        Check if the interval contains the given value

        :param value: value to check (int)
        :return: boolean
        """
        if self.is_empty():
            return False
        else:
            return self._lower_bound <= value <= self._upper_bound

    def contain_all(self, values):
        """
        Check if the interval contains all the given values

        :param values: list of integers (list)
        :return: boolean
        """
        for value in values:
            if not self.contain(value):
                return False
        return True

    def subtract(self, interval_to_subtract: IntSet):
        """
        Subtract the given interval to this interval
        (the bounds of the given interval are not remove from this interval)

        :param interval_to_subtract: interval to subtract to this interval (IntInterval)
        :return: (IntegerSet)
        """
        intersection = self.intersect(interval_to_subtract)
        if intersection.is_empty():
            return self.copy()
        else:
            if intersection.lower_bound == self._lower_bound:
                if intersection.upper_bound == self._upper_bound:
                    return IntInterval()
                else:
                    return IntInterval(lower_bound=intersection.upper_bound, upper_bound=self._upper_bound)
            else:
                if intersection.upper_bound == self._upper_bound:
                    return IntInterval(lower_bound=self._lower_bound, upper_bound=intersection._lower_bound)
                else:
                    return IntIntervalUnion([
                        IntInterval(lower_bound=self._lower_bound, upper_bound=intersection._lower_bound),
                        IntInterval(lower_bound=intersection.upper_bound, upper_bound=self._upper_bound)
                    ])

    def intersect(self, interval):
        if not isinstance(interval, IntInterval):
            raise TypeError("interval to intersect must be IntInterval")
        else:
            if self.is_empty() or interval.is_empty():
                return IntInterval()
            else:
                lower_bound = max(self._lower_bound, interval.lower_bound)
                upper_bound = min(self._upper_bound, interval.upper_bound)
                result = IntInterval()
                if upper_bound - lower_bound >= 0:
                    result.set(lower_bound, upper_bound)
                return result


# Class IntIntervalUnion
class IntIntervalUnion(IntSet):

    def __init__(self, intervals=None):
        super().__init__()
        self._intervals = []
        if intervals is not None:
            self.add_multiple(intervals)

    def __getitem__(self, index):
        if self.is_empty():
            raise ValueError("this union is empty")
        elif index < 0 or index >= len(self._intervals):
            raise ValueError("given index is out of range")
        else:
            return self._intervals[index]

    def __len__(self):
        return len(self._intervals)

    def __repr__(self):
        if self.is_empty():
            return "Ø"
        else:
            representation = self._intervals[0].__repr__()
            for interval in self._intervals[1:]:
                representation += " U " + interval.__repr__()
            return representation

    @property
    def intervals(self):
        return self._intervals

    def clear(self):
        self._intervals = []

    def is_empty(self):
        return not self._intervals

    def _add_interval(self, interval: IntInterval, copy_interval=False):
        if not isinstance(interval, IntInterval):
            raise TypeError("the given interval must be IntInterval")
        else:
            if not (interval.is_empty()):
                if copy_interval:
                    self._intervals.append(interval.copy())
                else:
                    self._intervals.append(interval)

    def _add_union(self, union, copy_interval=False):
        if not isinstance(union, IntIntervalUnion):
            raise TypeError("The given union must be IntIntervalUnion")
        else:
            for interval in union.intervals:
                self._add_interval(interval, copy_interval)

    def add(self, int_set: IntSet, copy_interval=False):
        if not isinstance(int_set, IntSet):
            raise TypeError("The given int_set must be IntInterval")
        else:
            if isinstance(int_set, IntInterval):
                self._add_interval(int_set, copy_interval)
            else:
                self._add_union(int_set, copy_interval)

    def add_multiple(self, intervals, copy_interval=False):
        for interval in intervals:
            self.add(interval, copy_interval)

    def subtract(self, interval_to_subtract: IntInterval):
        result = IntIntervalUnion()
        for subtracted_interval in self._intervals:
            result.add(subtracted_interval.subtract(interval_to_subtract))
        return result

    def intersect(self, interval_to_intersect: IntInterval):
        result = IntIntervalUnion()
        if not (self.is_empty()):
            for interval in self._intervals:
                result.add(interval.intersect(interval_to_intersect))
        return result

    # TODO: to remove if not necessary
    # def toTimeString(self):
    #     if self.isEmpty():
    #         return "Ø"
    #     else:
    #         representation = self.intervals[0].toTimeString()
    #         for interval in self.intervals[1:]:
    #             representation += " U " + interval.toTimeString()
    #         return representation


# Main function
def main():

    # Create empty interval
    interval1 = IntInterval()
    print(interval1)

    # Create [0, 10] interval
    interval2 = IntInterval(0, 10)
    print(interval2)

    # Create [8, 13] interval
    interval3 = IntInterval(8, 13)
    print(interval3)

    # Create [0, 5] interval
    interval4 = IntInterval(0, 5)
    print(interval4)

    # Create [5, 10] interval
    interval5 = IntInterval(5, 10)
    print(interval5)

    # Create [2, 7] interval
    interval6 = IntInterval(2, 7)
    print(interval6)

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
