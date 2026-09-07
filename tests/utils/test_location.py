# Third-party library
import pytest

# Local library
from src.utils.location import Location


# NB: `is True`/`is False` are used instead of plain truthy asserts throughout this file:
# Location.__eq__'s contract requires it to return an actual bool, not merely a truthy value.


# Locations whose coordinates differ by less than COORDINATES_TOLERANCE are treated as equal,
# for both geographic (degrees, converted to radians internally) and cartesian coordinates.
@pytest.mark.parametrize(
    "loc1, loc2",
    [
        pytest.param(
            Location(44.5, -0.3),
            Location(44.5 + 1e-10, -0.3),
            id="geographic"
        ),
        pytest.param(
            Location(1.0, 2.0, is_geographic=False),
            Location(1.0 + 1e-10, 2.0, is_geographic=False),
            id="cartesian",
        ),
    ],
)
def test_close_coordinates_are_equal(loc1, loc2):
    assert (loc1 == loc2) is True


# Locations whose coordinates differ by more than COORDINATES_TOLERANCE are not equal.
@pytest.mark.parametrize(
    "loc1, loc2",
    [
        pytest.param(
            Location(44.5, -0.3),
            Location(44.5 + 1e-3, -0.3),
            id="geographic"
        ),
        pytest.param(
            Location(1.0, 2.0, is_geographic=False),
            Location(1.0 + 1e-3, 2.0, is_geographic=False),
            id="cartesian",
        ),
    ],
)
def test_far_apart_coordinates_are_not_equal(loc1, loc2):
    assert (loc1 == loc2) is False


def test_two_empty_locations_are_equal():
    assert (Location() == Location()) is True


# An empty location is never equal to a non-empty one, regardless of operand order.
@pytest.mark.parametrize(
    "loc1, loc2",
    [
        pytest.param(Location(), Location(44.5, -0.3), id="empty_vs_non_empty"),
        pytest.param(Location(44.5, -0.3), Location(), id="non_empty_vs_empty"),
    ],
)
def test_empty_and_non_empty_locations_are_not_equal(loc1, loc2):
    assert (loc1 == loc2) is False


def test_comparing_to_a_non_location_object_returns_false():
    assert (Location(44.5, -0.3) == "not a location") is False
