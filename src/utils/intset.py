# NB: it is not possible to separate IntInterval and IntIntervalUnion classes in different files
# as they need each other to be defined

# Standard library
from typing import Optional


##########
# IntSet #
##########

class IntSet:
    """
    Base interface for a set of integers.

    Not meant to be instantiated directly: its methods model the behavior of an unpopulated (empty) set and
    are overridden by subclasses (IntInterval, IntIntervalUnion) with real logic.
    """

    def __init__(self):
        pass

    def __getitem__(self, index):
        """Returns None: an IntSet has no elements to index into."""
        return None

    def clear(self):
        """Empties the set. No-op: an IntSet is already empty."""
        pass

    def is_empty(self):
        """Returns whether the set is empty."""
        return True

    def contain(self, value):
        """Returns whether the set contains the given value."""
        return False

    def subtract(self, int_set):
        """Returns this set with int_set's elements removed."""
        return None

    def intersect(self, int_set):
        """Returns the intersection of this set with int_set."""
        return None


###############
# IntInterval #
###############

class IntInterval(IntSet):
    """
    A closed interval of integers, [lower_bound, upper_bound].

    The interval is considered empty when both bounds are None.
    """

    def __init__(self, lower_bound=None, upper_bound=None):
        """
        Args:
            lower_bound: Lower bound of the interval, or None for an empty interval.
            upper_bound: Upper bound of the interval, or None for an empty interval.
        """
        super().__init__()
        self._lower_bound = None
        self._upper_bound = None
        self.set(lower_bound, upper_bound)

    def __getitem__(self, index):
        """
        Returns a bound of the interval by index.

        Args:
            index: 0 for the lower bound, 1 for the upper bound.

        Returns:
            The corresponding bound.

        Raises:
            ValueError: If the interval is empty, or if index isn't 0 or 1.
        """
        if self.is_empty():
            raise ValueError("this interval is empty")
        else:
            if index == 0:
                return self._lower_bound
            elif index == 1:
                return self._upper_bound
            else:
                raise ValueError("index must 0 or 1")

    def __repr__(self):
        if self.is_empty():
            return "Ø"
        else:
            return f"[{self._lower_bound};{self._upper_bound}]"

    @property
    def lower_bound(self):
        """Lower bound of the interval, or None if it's empty."""
        return self._lower_bound

    @property
    def upper_bound(self):
        """Upper bound of the interval, or None if it's empty."""
        return self._upper_bound

    @lower_bound.setter
    def lower_bound(self, lower_bound):
        """
        Args:
            lower_bound: New lower bound, or None to make the interval empty.

        Raises:
            TypeError: If lower_bound isn't an int or None, or if setting it to/from None while the
                other bound isn't also None (use set() to change both bounds together).
            ValueError: If lower_bound would be greater than the current upper bound.
        """
        if lower_bound is None:
            if self._upper_bound is not None:
                raise TypeError("lower bound can not be None because upper bound is int, use set_bounds")
        else:
            if not isinstance(lower_bound, int):
                raise TypeError("lower bound must be int or None")
            elif self._upper_bound is None:
                raise TypeError("lower bound can not be int because upper bound is None, use set_bounds")
            elif lower_bound > self._upper_bound:
                raise ValueError("lower bound must be smaller than upper bound")
        self._lower_bound = lower_bound

    @upper_bound.setter
    def upper_bound(self, upper_bound):
        """
        Args:
            upper_bound: New upper bound, or None to make the interval empty.

        Raises:
            TypeError: If upper_bound isn't an int or None, or if setting it to/from None while the
                other bound isn't also None (use set() to change both bounds together).
            ValueError: If upper_bound would be smaller than the current lower bound.
        """
        if upper_bound is None:
            if self._lower_bound is not None:
                raise TypeError("upper bound can not be None because lower bound is int, use set_bounds")
        else:
            if not isinstance(upper_bound, int):
                raise TypeError("upper bound must be int or None")
            elif self._lower_bound is None:
                raise TypeError("upper bound can not be int because lower bound is None, use set_bounds")
            elif self._lower_bound > upper_bound:
                raise ValueError("upper bound must be larger than lower bound")
        self._upper_bound = upper_bound

    def set(self, lower_bound=None, upper_bound=None):
        """
        Sets both bounds of the interval at once.

        Args:
            lower_bound: New lower bound, or None to make the interval empty.
            upper_bound: New upper bound, or None to make the interval empty.

        Raises:
            TypeError: If exactly one of lower_bound/upper_bound is None, or either isn't an int.
            ValueError: If lower_bound is greater than upper_bound.
        """
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
        """Empties the interval (sets both bounds to None)."""
        self.set()

    def is_empty(self):
        """Returns whether the interval is empty (both bounds None)."""
        return self._lower_bound is None

    def copy(self):
        """Returns a new IntInterval with the same bounds as this one."""
        return IntInterval(lower_bound=self._lower_bound, upper_bound=self._upper_bound)

    def contain(self, value):
        """
        Returns whether the interval contains the given value.

        Args:
            value: Value to check.

        Returns:
            True if the interval contains value, False otherwise.
        """
        if self.is_empty():
            return False
        else:
            return self._lower_bound <= value <= self._upper_bound

    def contain_all(self, values: list[int]):
        """
        Returns whether the interval contains every given value.

        Args:
            values: Values to check.

        Returns:
            True if the interval contains every value in values, False otherwise.
        """
        for value in values:
            if not self.contain(value):
                return False
        return True

    def subtract(self, interval_to_subtract: "IntInterval"):
        """
        Removes interval_to_subtract's range from this interval.

        Args:
            interval_to_subtract: Interval to subtract from this one.

        Returns:
            An IntInterval if what remains is contiguous, or an IntIntervalUnion if subtracting
            interval_to_subtract splits this interval in two.
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

    def intersect(self, interval: "IntInterval"):
        """
        Returns the intersection of this interval with another.

        Args:
            interval: Interval to intersect with.

        Returns:
            An IntInterval covering the overlap, or an empty IntInterval if they don't overlap.

        Raises:
            TypeError: If interval isn't an IntInterval.
        """
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


####################
# IntIntervalUnion #
####################

class IntIntervalUnion(IntSet):
    """
    A union of disjoint IntInterval ranges.
    """

    def __init__(self, intervals: Optional[list[IntInterval]] = None):
        """
        Args:
            intervals: Intervals to seed the union with. Empty intervals are dropped; see add_multiple.
        """
        super().__init__()
        self._intervals: list[IntInterval] = []
        if intervals is not None:
            self.add_multiple(intervals)

    def __getitem__(self, index):
        """
        Returns the interval at the given index.

        Args:
            index: Position of the interval to return, in [0, len(self)).

        Returns:
            The IntInterval at index.

        Raises:
            ValueError: If the union is empty, or if index is out of range.
        """
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
    def intervals(self) -> list[IntInterval]:
        """The disjoint intervals making up this union."""
        return self._intervals

    def clear(self):
        """Empties the union (removes all intervals)."""
        self._intervals = []

    def is_empty(self):
        """Returns whether the union contains no intervals."""
        return not self._intervals

    def _add_interval(self, interval: IntInterval, copy_interval=False):
        """
        Appends a single interval to the union, dropping it if it's empty.

        Args:
            interval: Interval to add.
            copy_interval: If True, append a copy of interval instead of the instance itself.

        Raises:
            TypeError: If interval isn't an IntInterval.
        """
        if not isinstance(interval, IntInterval):
            raise TypeError("the given interval must be IntInterval")
        else:
            if not (interval.is_empty()):
                if copy_interval:
                    self._intervals.append(interval.copy())
                else:
                    self._intervals.append(interval)

    def _add_union(self, union, copy_interval=False):
        """
        Appends every interval of another union to this one.

        Args:
            union: IntIntervalUnion whose intervals should be added.
            copy_interval: If True, append copies of the intervals instead of the instances themselves.

        Raises:
            TypeError: If union isn't an IntIntervalUnion.
        """
        if not isinstance(union, IntIntervalUnion):
            raise TypeError("The given union must be IntIntervalUnion")
        else:
            for interval in union.intervals:
                self._add_interval(interval, copy_interval)

    def add(self, int_set: IntSet, copy_interval=False):
        """
        Appends an IntInterval or every interval of an IntIntervalUnion to this union.

        Args:
            int_set: IntInterval or IntIntervalUnion to add.
            copy_interval: If True, append copies of the interval(s) instead of the instances themselves.

        Raises:
            TypeError: If int_set isn't an IntSet.
        """
        if not isinstance(int_set, IntSet):
            raise TypeError("The given int_set must be IntInterval")
        else:
            if isinstance(int_set, IntInterval):
                self._add_interval(int_set, copy_interval)
            else:
                self._add_union(int_set, copy_interval)

    def add_multiple(self, intervals: list[IntSet], copy_interval=False):
        """
        Appends multiple IntSets (IntInterval or IntIntervalUnion) to this union.

        Args:
            intervals: IntSets to add.
            copy_interval: If True, append copies of the intervals instead of the instances themselves.
        """
        for interval in intervals:
            self.add(interval, copy_interval)

    def subtract(self, interval_to_subtract: IntInterval):
        """
        Removes interval_to_subtract's range from every interval in this union.

        Args:
            interval_to_subtract: Interval to subtract from this union.

        Returns:
            A new IntIntervalUnion with interval_to_subtract's range removed.
        """
        result = IntIntervalUnion()
        for subtracted_interval in self._intervals:
            result.add(subtracted_interval.subtract(interval_to_subtract))
        return result

    def intersect(self, interval_to_intersect: IntInterval):
        """
        Returns the intersection of this union with an interval.

        Args:
            interval_to_intersect: Interval to intersect with.

        Returns:
            A new IntIntervalUnion covering the overlap.
        """
        result = IntIntervalUnion()
        if not (self.is_empty()):
            for interval in self._intervals:
                result.add(interval.intersect(interval_to_intersect))
        return result
