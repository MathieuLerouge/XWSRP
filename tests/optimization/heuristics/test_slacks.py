# Third-party library
import pytest

# Local libraries
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.optimization.heuristics.sequence import SequenceForHeuristics
from src.optimization.heuristics.slacks import SlackTimeComputer
from src.optimization.heuristics.step import StepForHeuristics
from tests.optimization.heuristics.helpers import build_employee, build_instance, build_task, build_unavailability


def build_sequence_with_unavailability() -> SequenceForHeuristics:
    """
    Departure(0) -> TaskA(100-150) -> Unavailability(300-330) -> TaskB(400-440) -> ComeBack(440),
    with 100 minutes of idle time before TaskA, 150 minutes between TaskA and the unavailability,
    and 70 minutes between the unavailability and TaskB.
    """
    instance = build_instance()
    employee = build_employee()
    task_a = build_task("TA", duration=50)
    task_b = build_task("TB", duration=40)
    unavailability = build_unavailability(employee, "U1", start_time=300, end_time=330)
    steps = [
        StepForHeuristics(Departure(employee), 0, 0, 0),
        StepForHeuristics(task_a, 0, 100, 150),
        StepForHeuristics(unavailability, 150, 300, 330),
        StepForHeuristics(task_b, 330, 400, 440),
        StepForHeuristics(ComeBack(employee), 440, 440, 440),
    ]
    return SequenceForHeuristics(instance, employee, steps)


###########################################
# recompute_bts_from / recompute_fts_from #
###########################################

def test_unavailability_step_has_zero_bts_and_fts():
    sequence = build_sequence_with_unavailability()
    assert sequence[2].bts == 0
    assert sequence[2].fts == 0


def test_fts_before_unavailability_is_bounded_by_it_not_by_the_rest_of_the_route():
    sequence = build_sequence_with_unavailability()
    # TaskA's fts must reflect only the room up to the unavailability's start (300), not up to
    # the employee's end_time_ub (1000) or the comeback: end(150) + fts must land exactly at 300.
    assert sequence[1].end_time + sequence[1].fts == 300


def test_bts_after_unavailability_is_bounded_by_it_not_by_the_rest_of_the_route():
    sequence = build_sequence_with_unavailability()
    # TaskB's bts must reflect only the room back to the unavailability's end (330),
    # not back to the employee's start_time_lb (0) or the departure:
    # start(400) - bts must land exactly at 330.
    assert sequence[3].start_time - sequence[3].bts == 330


##################################
# find_first_critical_step_index #
##################################

def test_find_first_critical_step_index_forward_from_stops_at_unavailability():
    sequence = build_sequence_with_unavailability()
    assert SlackTimeComputer.find_first_critical_step_index_forward_from(sequence, 1) == 2


def test_find_first_critical_step_index_backward_from_stops_at_unavailability():
    sequence = build_sequence_with_unavailability()
    assert SlackTimeComputer.find_first_critical_step_index_backward_from(sequence, 3) == 2


#######################################################################
# propagate_earlier_start_time_from / propagate_later_start_time_from #
#######################################################################

def test_propagate_later_start_time_from_stops_exactly_at_unavailability_boundary():
    sequence = build_sequence_with_unavailability()
    returned_index = SlackTimeComputer.propagate_later_start_time_from(
        sequence, 1, sequence[1].start_time + sequence[1].fts)
    assert returned_index == 2
    assert (sequence[1].start_time, sequence[1].end_time) == (250, 300)
    assert (sequence[2].start_time, sequence[2].end_time) == (300, 330)


def test_propagate_later_start_time_from_does_not_move_unavailability_on_overshoot():
    sequence = build_sequence_with_unavailability()
    # Ask for more than TaskA's fts allows: without the fix, this used to shift the unavailability too.
    SlackTimeComputer.propagate_later_start_time_from(
        sequence, 1, sequence[1].start_time + sequence[1].fts + 10)
    assert (sequence[2].start_time, sequence[2].end_time) == (300, 330)


def test_propagate_earlier_start_time_from_stops_exactly_at_unavailability_boundary():
    sequence = build_sequence_with_unavailability()
    returned_index = SlackTimeComputer.propagate_earlier_start_time_from(
        sequence, 3, sequence[3].start_time - sequence[3].bts)
    assert returned_index == 3
    assert (sequence[3].start_time, sequence[3].end_time) == (330, 370)
    assert (sequence[2].start_time, sequence[2].end_time) == (300, 330)


def test_propagate_earlier_start_time_from_does_not_move_unavailability_on_overshoot():
    sequence = build_sequence_with_unavailability()
    # Ask for more than TaskB's bts allows: without the fix, this used to shift the unavailability too.
    SlackTimeComputer.propagate_earlier_start_time_from(
        sequence, 3, sequence[3].start_time - sequence[3].bts - 10)
    assert (sequence[2].start_time, sequence[2].end_time) == (300, 330)


def test_propagate_later_start_time_from_does_not_move_the_unavailability_it_starts_on():
    """
    Both directions refuse to shift a rigid step they are asked to start from, not only the one they reach
    by propagation: forward used to test the next step's rigidity only, after having moved the current one.
    """
    sequence = build_sequence_with_unavailability()

    returned_index = SlackTimeComputer.propagate_later_start_time_from(sequence, 2, sequence[2].start_time + 10)

    assert returned_index == 2
    assert (sequence[2].start_time, sequence[2].end_time) == (300, 330)


def test_propagate_earlier_start_time_from_does_not_move_the_unavailability_it_starts_on():
    """The backward counterpart of the check above, pinning the two directions to the same contract."""
    sequence = build_sequence_with_unavailability()

    returned_index = SlackTimeComputer.propagate_earlier_start_time_from(sequence, 2, sequence[2].start_time - 10)

    assert returned_index == 3
    assert (sequence[2].start_time, sequence[2].end_time) == (300, 330)


def test_propagate_earlier_start_time_from_rejects_a_start_time_that_is_not_earlier():
    """Shifting by nothing used to leave the sequence untouched while reporting an empty range of changes."""
    sequence = build_sequence_with_unavailability()

    with pytest.raises(ValueError):
        SlackTimeComputer.propagate_earlier_start_time_from(sequence, 3, sequence[3].start_time)


def test_propagate_later_start_time_from_rejects_a_start_time_that_is_not_later():
    """Shifting by nothing used to leave every step but the last untouched while still reporting a range."""
    sequence = build_sequence_with_unavailability()

    with pytest.raises(ValueError):
        SlackTimeComputer.propagate_later_start_time_from(sequence, 1, sequence[1].start_time)


#################
# tighten_times #
#################

def test_tighten_times_tightens_each_segment_independently_around_unavailability():
    sequence = build_sequence_with_unavailability()
    SlackTimeComputer.tighten_times(sequence, update_kpis=False)
    # Departure/TaskA segment tightens forward to touch the unavailability's start exactly.
    assert (sequence[0].start_time, sequence[1].start_time, sequence[1].end_time) == (250, 250, 300)
    # TaskB/ComeBack segment tightens backward to touch the unavailability's end exactly.
    assert (sequence[3].start_time, sequence[3].end_time, sequence[4].start_time) == (330, 370, 370)
    # The unavailability itself never moves.
    assert (sequence[2].start_time, sequence[2].end_time) == (300, 330)


def test_tighten_times_updates_idle_time_kpi_around_unavailability():
    sequence = build_sequence_with_unavailability()
    sequence.compute_kpis()
    idle_time_before = sequence.total_idle_time
    SlackTimeComputer.tighten_times(sequence, update_kpis=True)
    # With a single task on each side of the unavailability, each of the two segments
    # (departure -> unavailability, unavailability -> comeback) fully closes its own idle time:
    # TaskA is pushed all the way forward to touch the unavailability's start,
    # and TaskB is pulled all the way backward to touch its end,
    # so no idle time is left anywhere in this particular sequence.
    assert idle_time_before == 320
    assert sequence.total_idle_time == 0


def test_tighten_times_without_unavailability_matches_prior_whole_route_behavior():
    instance = build_instance()
    employee = build_employee()
    task = build_task("TA", duration=50)
    steps = [
        StepForHeuristics(Departure(employee), 0, 0, 0),
        StepForHeuristics(task, 0, 100, 150),
        StepForHeuristics(ComeBack(employee), 150, 440, 440),
    ]
    sequence = SequenceForHeuristics(instance, employee, steps)
    SlackTimeComputer.tighten_times(sequence, update_kpis=False)
    # With no unavailability, the whole route is a single segment:
    # tightening pulls everything as close together as possible, from departure through to the comeback.
    assert sequence[0].start_time == sequence[1].start_time
    assert sequence[1].end_time == sequence[2].start_time
