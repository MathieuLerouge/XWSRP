# Local library
from src.utils.intset import IntInterval, IntIntervalUnion
from src.utils.time import TWENTY_FOUR_HOURS_FORMAT_WITH_H
from src.utils.timeset import TimeInterval, TimeIntervalUnion


################
# TimeInterval #
################

def test_from_int_interval_returns_a_time_interval_with_the_same_bounds():
    result = TimeInterval.from_IntInterval(IntInterval(0, 10))
    assert isinstance(result, TimeInterval)
    assert (result.lower_bound, result.upper_bound) == (0, 10)


def test_as_string_formats_the_bounds_as_clock_times():
    assert TimeInterval(0, 10).as_string() == "[12:00AM;12:10AM]"


def test_as_string_returns_o_for_an_empty_interval():
    assert TimeInterval().as_string() == "Ø"


def test_as_string_uses_the_given_hour_format():
    assert TimeInterval(0, 10).as_string(TWENTY_FOUR_HOURS_FORMAT_WITH_H) == "[00h00;00h10]"


def test_intersect_returns_a_time_interval():
    result = TimeInterval(0, 10).intersect(TimeInterval(5, 15))
    assert isinstance(result, TimeInterval)
    assert (result.lower_bound, result.upper_bound) == (5, 10)


def test_copy_returns_a_time_interval():
    interval = TimeInterval(0, 10)
    copied = interval.copy()
    assert isinstance(copied, TimeInterval)
    assert (copied.lower_bound, copied.upper_bound) == (0, 10)
    copied.lower_bound = 2
    assert interval.lower_bound == 0


# subtract's branches: no overlap, full overlap (empty result), overlap at one edge, and overlap in
# the middle (splits into two intervals) — each must preserve the TimeInterval/TimeIntervalUnion type.
def test_subtract_returns_a_time_interval_when_there_is_no_overlap():
    result = TimeInterval(2, 5).subtract(TimeInterval(10, 15))
    assert isinstance(result, TimeInterval)
    assert (result.lower_bound, result.upper_bound) == (2, 5)


def test_subtract_returns_a_time_interval_when_fully_covered():
    result = TimeInterval(2, 5).subtract(TimeInterval(0, 10))
    assert isinstance(result, TimeInterval)
    assert result.is_empty()


def test_subtract_returns_a_time_interval_when_the_overlap_is_at_an_edge():
    result = TimeInterval(2, 10).subtract(TimeInterval(0, 5))
    assert isinstance(result, TimeInterval)
    assert (result.lower_bound, result.upper_bound) == (5, 10)


def test_subtract_returns_a_time_interval_union_when_the_overlap_is_in_the_middle():
    result = TimeInterval(0, 10).subtract(TimeInterval(3, 7))
    assert isinstance(result, TimeIntervalUnion)
    assert all(isinstance(interval, TimeInterval) for interval in result.intervals)
    assert (result[0].lower_bound, result[0].upper_bound) == (0, 3)
    assert (result[1].lower_bound, result[1].upper_bound) == (7, 10)


#####################
# TimeIntervalUnion #
#####################

def test_from_int_interval_union_returns_a_time_interval_union_with_the_same_intervals():
    result = TimeIntervalUnion.from_IntIntervalUnion(IntIntervalUnion([IntInterval(0, 10)]))
    assert isinstance(result, TimeIntervalUnion)
    assert isinstance(result[0], TimeInterval)
    assert (result[0].lower_bound, result[0].upper_bound) == (0, 10)


def test_as_string_formats_each_interval_and_joins_with_u():
    union = TimeIntervalUnion([TimeInterval(0, 10), TimeInterval(20, 30)])
    assert union.as_string() == "[12:00AM;12:10AM] U [12:20AM;12:30AM]"


def test_as_string_returns_o_for_an_empty_union():
    assert TimeIntervalUnion().as_string() == "Ø"


def test_subtract_returns_a_time_interval_union():
    union = TimeIntervalUnion([TimeInterval(0, 10), TimeInterval(20, 30)])
    result = union.subtract(TimeInterval(5, 25))
    assert isinstance(result, TimeIntervalUnion)
    assert all(isinstance(interval, TimeInterval) for interval in result.intervals)
    assert (result[0].lower_bound, result[0].upper_bound) == (0, 5)
    assert (result[1].lower_bound, result[1].upper_bound) == (25, 30)


def test_intersect_returns_a_time_interval_union():
    union = TimeIntervalUnion([TimeInterval(0, 10), TimeInterval(20, 30)])
    result = union.intersect(TimeInterval(5, 25))
    assert isinstance(result, TimeIntervalUnion)
    # Only TimeIntervalUnion has as_string(); calling it here also confirms intersect() preserves
    # the subclass type, not just the isinstance check above.
    assert result.as_string() == "[12:05AM;12:10AM] U [12:20AM;12:25AM]"
