# Third-party library
import pytest

# Local libraries
from src.importing.instance import extract_instance_from_file
from src.modeling.instance import Instance, LUNCH_BREAK_KEY, UNAVAILABILITIES_KEY
from src.utils.time import convert_time_string_to_nb_minutes
from tests.importing.helpers import INSTANCE_FILE_PATH, INSTANCE_WITH_UNAVAILABILITIES_FILE_PATH


@pytest.fixture
def instance_with_unavailabilities():
    return extract_instance_from_file(INSTANCE_WITH_UNAVAILABILITIES_FILE_PATH)


@pytest.fixture
def instance_without_unavailabilities():
    return extract_instance_from_file(INSTANCE_FILE_PATH)


def _as_time_ranges(intervals) -> list[tuple[int, int]]:
    """Returns the given time intervals as (lower bound, upper bound) pairs, in chronological order."""
    return sorted((interval.lower_bound, interval.upper_bound) for interval in intervals)


def test_from_dict_reads_the_employees_unavailabilities(instance_with_unavailabilities):
    employee = instance_with_unavailabilities.get_employee_by_name("Ellen")
    unavailabilities_time_ranges = sorted(
        (unavailability.start_time_lb, unavailability.end_time_ub)
        for unavailability in employee.unavailabilities
    )
    assert unavailabilities_time_ranges == [(600, 660), (900, 960)]
    assert not instance_with_unavailabilities.get_employee_by_name("Adam").has_unavailabilities


def test_from_dict_applies_the_tasks_unavailabilities_to_their_time_windows(instance_with_unavailabilities):
    task = instance_with_unavailabilities.get_task_by_name("T1")
    assert task.has_unavailability
    assert _as_time_ranges(task.time_windows.intervals) == [(480, 660), (780, 1080)]


def test_from_dict_applies_a_tasks_unavailability_that_truncates_its_time_window(
        instance_with_unavailabilities):
    """T2's second unavailability runs to the end of its window, so it shortens it rather than splitting it."""
    task = instance_with_unavailabilities.get_task_by_name("T2")
    assert _as_time_ranges(task.time_windows.intervals) == [(480, 540), (570, 960)]


def test_from_dict_leaves_a_task_without_unavailability_untouched(instance_with_unavailabilities):
    task = instance_with_unavailabilities.get_task_by_name("T3")
    assert not task.has_unavailability
    assert _as_time_ranges(task.time_windows.intervals) == [(480, 1080)]


def test_from_dict_reads_the_lunch_break(instance_with_unavailabilities):
    assert instance_with_unavailabilities.has_lunch_break
    assert instance_with_unavailabilities.lunch_break_time_lb == convert_time_string_to_nb_minutes("12:00pm")
    assert instance_with_unavailabilities.lunch_break_time_ub == convert_time_string_to_nb_minutes("2:00pm")
    assert instance_with_unavailabilities.lunch_break_duration == 60


def test_an_instance_dictionary_is_unchanged_by_a_round_trip_through_from_dict(instance_with_unavailabilities):
    dictionary = instance_with_unavailabilities.to_dict()
    assert Instance.from_dict(dictionary).to_dict() == dictionary


def test_to_dict_omits_the_optional_content_when_the_instance_has_none(instance_without_unavailabilities):
    dictionary = instance_without_unavailabilities.to_dict()
    assert LUNCH_BREAK_KEY not in dictionary
    assert all(UNAVAILABILITIES_KEY not in employee_data
               for employee_data in dictionary['employees'].values())
    assert all(UNAVAILABILITIES_KEY not in task_data for task_data in dictionary['tasks'].values())
