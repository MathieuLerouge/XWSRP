# Third-party library
import pytest

# Local library
from src.utils.intset import IntInterval, IntIntervalUnion


###############
# IntInterval #
###############

def test_init_creates_an_empty_interval_by_default():
    assert IntInterval().is_empty()


def test_init_creates_an_interval_with_the_given_bounds():
    interval = IntInterval(2, 5)
    assert interval.lower_bound == 2
    assert interval.upper_bound == 5


@pytest.mark.parametrize("lower_bound, upper_bound", [
    pytest.param(None, 5, id="lower_none"),
    pytest.param(2, None, id="upper_none"),
])
def test_init_raises_type_error_when_only_one_bound_is_none(lower_bound, upper_bound):
    with pytest.raises(TypeError):
        _ = IntInterval(lower_bound, upper_bound)


def test_init_raises_type_error_when_a_bound_is_not_an_int():
    with pytest.raises(TypeError):
        _ = IntInterval("2", 5)


def test_init_raises_value_error_when_lower_bound_exceeds_upper_bound():
    with pytest.raises(ValueError):
        _ = IntInterval(5, 2)


def test_getitem_returns_the_corresponding_bound_by_index():
    interval = IntInterval(2, 5)
    assert interval[0] == 2
    assert interval[1] == 5


def test_getitem_raises_on_empty_interval():
    with pytest.raises(ValueError):
        _ = IntInterval()[0]


def test_getitem_raises_on_invalid_index():
    with pytest.raises(ValueError):
        _ = IntInterval(2, 5)[2]


def test_lower_bound_setter_accepts_a_value_not_exceeding_upper_bound():
    interval = IntInterval(2, 5)
    interval.lower_bound = 4
    assert interval.lower_bound == 4


def test_lower_bound_setter_rejects_a_value_greater_than_upper_bound():
    interval = IntInterval(2, 5)
    with pytest.raises(ValueError):
        interval.lower_bound = 10


def test_upper_bound_setter_accepts_a_value_not_less_than_lower_bound():
    interval = IntInterval(2, 5)
    interval.upper_bound = 6
    assert interval.upper_bound == 6


def test_upper_bound_setter_rejects_a_value_less_than_lower_bound():
    interval = IntInterval(2, 5)
    with pytest.raises(ValueError):
        interval.upper_bound = 1


def test_clear_empties_the_interval():
    interval = IntInterval(2, 5)
    interval.clear()
    assert interval.is_empty()


def test_copy_returns_an_equal_but_distinct_interval():
    interval = IntInterval(2, 5)
    copied = interval.copy()
    assert copied.lower_bound == 2
    assert copied.upper_bound == 5
    copied.lower_bound = 3
    assert interval.lower_bound == 2


@pytest.mark.parametrize("value, expected", [
    pytest.param(3, True, id="inside"),
    pytest.param(2, True, id="on_lower_boundary"),
    pytest.param(5, True, id="on_upper_boundary"),
    pytest.param(10, False, id="outside"),
])
def test_contain_checks_whether_the_value_is_within_bounds(value, expected):
    assert IntInterval(2, 5).contain(value) is expected


def test_contain_returns_false_for_an_empty_interval():
    assert IntInterval().contain(3) is False


def test_contain_all_returns_true_when_every_value_is_contained():
    assert IntInterval(2, 5).contain_all([2, 3, 5]) is True


def test_contain_all_returns_false_when_one_value_is_not_contained():
    assert IntInterval(2, 5).contain_all([2, 10]) is False


@pytest.mark.parametrize("interval1, interval2, expected_bounds", [
    pytest.param(IntInterval(0, 10), IntInterval(5, 15), (5, 10), id="overlapping"),
    pytest.param(IntInterval(0, 5), IntInterval(2, 7), (2, 5), id="overlapping_other_order"),
    pytest.param(IntInterval(0, 10), IntInterval(2, 7), (2, 7), id="one_contains_other"),
])
def test_intersect_returns_the_overlapping_range(interval1, interval2, expected_bounds):
    result = interval1.intersect(interval2)
    assert (result.lower_bound, result.upper_bound) == expected_bounds


def test_intersect_returns_an_empty_interval_when_disjoint():
    result = IntInterval(0, 5).intersect(IntInterval(10, 15))
    assert result.is_empty()


def test_intersect_raises_type_error_for_a_non_int_interval_argument():
    with pytest.raises(TypeError):
        IntInterval(0, 5).intersect("not an interval")


# subtract's branches: no overlap (unchanged), overlap at one edge (single interval remains),
# full overlap (empty result), overlap in the middle (splits into two intervals).
@pytest.mark.parametrize("interval, interval_to_subtract, expected_bounds", [
    pytest.param(IntInterval(2, 5), IntInterval(10, 15), (2, 5), id="no_overlap"),
    pytest.param(IntInterval(2, 10), IntInterval(0, 5), (5, 10), id="overlap_at_left_edge"),
    pytest.param(IntInterval(2, 10), IntInterval(7, 15), (2, 7), id="overlap_at_right_edge"),
])
def test_subtract_returns_the_remaining_interval(interval, interval_to_subtract, expected_bounds):
    result = interval.subtract(interval_to_subtract)
    assert (result.lower_bound, result.upper_bound) == expected_bounds


def test_subtract_returns_an_empty_interval_when_fully_covered():
    result = IntInterval(2, 5).subtract(IntInterval(0, 10))
    assert result.is_empty()


def test_subtract_returns_a_union_of_two_intervals_when_the_overlap_is_in_the_middle():
    result = IntInterval(0, 10).subtract(IntInterval(3, 7))
    assert isinstance(result, IntIntervalUnion)
    assert (result[0].lower_bound, result[0].upper_bound) == (0, 3)
    assert (result[1].lower_bound, result[1].upper_bound) == (7, 10)


####################
# IntIntervalUnion #
####################

def test_init_creates_an_empty_union_by_default():
    assert IntIntervalUnion().is_empty()


def test_init_seeds_the_union_with_the_given_intervals():
    union = IntIntervalUnion([IntInterval(0, 3), IntInterval(7, 10)])
    assert len(union) == 2


def test_init_drops_empty_intervals():
    union = IntIntervalUnion([IntInterval(0, 3), IntInterval()])
    assert len(union) == 1


def test_getitem_returns_the_interval_at_the_given_index():
    union = IntIntervalUnion([IntInterval(0, 3), IntInterval(7, 10)])
    assert union[1].lower_bound == 7


def test_getitem_raises_on_empty_union():
    with pytest.raises(ValueError):
        _ = IntIntervalUnion()[0]


def test_getitem_raises_on_out_of_range_index():
    with pytest.raises(ValueError):
        _ = IntIntervalUnion([IntInterval(0, 3)])[5]


def test_len_returns_the_number_of_intervals():
    assert len(IntIntervalUnion([IntInterval(0, 3), IntInterval(7, 10)])) == 2


def test_clear_empties_the_union():
    union = IntIntervalUnion([IntInterval(0, 3)])
    union.clear()
    assert union.is_empty()


def test_add_appends_an_interval():
    union = IntIntervalUnion()
    union.add(IntInterval(0, 3))
    assert len(union) == 1


def test_add_merges_another_unions_intervals():
    union = IntIntervalUnion([IntInterval(0, 3)])
    union.add(IntIntervalUnion([IntInterval(7, 10)]))
    assert len(union) == 2


def test_add_raises_type_error_for_a_non_int_set_argument():
    with pytest.raises(TypeError):
        IntIntervalUnion().add("not an int set")


def test_subtract_removes_the_given_range_from_every_interval():
    union = IntIntervalUnion([IntInterval(0, 10), IntInterval(20, 30)])
    result = union.subtract(IntInterval(5, 25))
    assert (result[0].lower_bound, result[0].upper_bound) == (0, 5)
    assert (result[1].lower_bound, result[1].upper_bound) == (25, 30)


def test_intersect_returns_the_overlap_with_every_interval():
    union = IntIntervalUnion([IntInterval(0, 10), IntInterval(20, 30)])
    result = union.intersect(IntInterval(5, 25))
    assert (result[0].lower_bound, result[0].upper_bound) == (5, 10)
    assert (result[1].lower_bound, result[1].upper_bound) == (20, 25)
