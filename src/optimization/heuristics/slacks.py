# Standard libraries
from contextlib import contextmanager
from typing import TYPE_CHECKING

# Local library
from src.modeling.unavailability import Unavailability

if TYPE_CHECKING:
    from src.optimization.heuristics.sequence import SequenceForHeuristics
    from src.optimization.heuristics.step import StepForHeuristics


#####################
# SlackTimeComputer #
#####################

class SlackTimeComputer:
    """
    Stateless collection of static methods computing and maintaining the times and time slacks (BTS/FTS)
    of a SequenceForHeuristics's steps, mutating the given sequence in place.
    """

    ###############
    # Computation #
    ###############

    # TODO: Adapt to task with unavailabilities (split time windows) and lunch breaks
    @staticmethod
    def recompute_bts_from(sequence: "SequenceForHeuristics", step_index: int):
        """
        Recompute the backward time slacks, in sequence order, starting from the step at the given index.
        A step's BTS (backward time slack) is how much earlier it could start,
        so that `start_time - bts` is its earliest feasible start,
        and that earliest start is what the recomputation carries forward.
        The first step of the sequence is held back by the employee's working-time window alone.
        Every other step is held back by whichever comes later of two things:
        the lower bound of its own activity's time window, and the moment the employee could reach it
        having left the previous step as early as that step could itself start,
        i.e. the previous step's earliest start plus its duration plus the traveling duration.

        An employee unavailability needs no special case here: the lower bound of its own time window is its start time,
        which gives it a BTS of zero, and that zero then propagates as a wall to the steps after it.

        NB: The steps' times are read, never written. Only their BTS are recomputed,
        and only from the given index onwards, which is why the BTS of the step before it has to be valid already.

        WIP: Instance without split task time windows (see Task.apply_unavailability) and without lunch breaks.

        Args:
            sequence: The sequence whose BTS slacks are recomputed.
            step_index: The step index to start recomputing BTS from.
              When it is not the first one, the BTS of the step before it is assumed computed and valid.
        """
        if step_index == 0:
            sequence[0].bts = sequence[0].start_time - sequence.employee.start_time_lb
            step_index += 1
        for previous_step_index in range(step_index - 1, sequence.nb_steps - 1):
            step = sequence[previous_step_index + 1]
            previous_step = sequence[previous_step_index]
            step.bts = min(
                step.start_time - step.activity.start_time_lb,
                step.start_time - (previous_step.start_time - previous_step.bts + previous_step.activity.duration +
                                   sequence.instance.compute_traveling_duration(previous_step.activity, step.activity))
            )

    # TODO: Adapt to task with unavailabilities (split time windows) and lunch breaks
    @staticmethod
    def recompute_fts_from(sequence: "SequenceForHeuristics", step_index: int):
        """
        Recompute the forward time slacks, in reverse order, starting from the step at the given index.
        A step's FTS (forward time slack) is how much later it could start,
        so that `start_time + fts` is its latest feasible start,
        and that latest start is what the recomputation carries backward.
        The last step of the sequence is held up by the employee's working-time window alone.
        Every other step is held up by whichever comes earlier of two things:
        the upper bound of its own activity's time window, and the moment the employee would have to leave it
        to reach the next step as late as that step could itself start,
        i.e. the next step's latest start minus the traveling duration and its own duration.

        An employee unavailability needs no special case here: the upper bound of its own time window is its end time,
        which gives it an FTS of zero, and that zero then propagates as a wall to the steps before it.

        NB: The steps' times are read, never written. Only their FTS are recomputed,
        and only from the given index backwards, which is why the FTS of the step after it has to be valid already.

        WIP: Instance without split task time windows (see Task.apply_unavailability) and without lunch breaks.

        Args:
            sequence: The sequence whose FTS slacks are recomputed.
            step_index: The step index to start recomputing FTS from.
              When it is not the last one, the FTS of the step after it is assumed computed and valid.
        """
        if step_index == sequence.nb_steps - 1:
            sequence[-1].fts = sequence.employee.end_time_ub - sequence[-1].start_time
            step_index -= 1
        for next_step_index in range(step_index + 1, 0, -1):
            step = sequence[next_step_index - 1]
            next_step = sequence[next_step_index]
            step.fts = min(
                step.activity.end_time_ub - (step.start_time + step.activity.duration),
                next_step.start_time + next_step.fts -
                (step.start_time + step.activity.duration +
                 sequence.instance.compute_traveling_duration(step.activity, next_step.activity))
            )

    # TODO: Adapt to task with unavailabilities (split time windows) and lunch breaks
    @staticmethod
    def recompute_time_slacks(sequence: "SequenceForHeuristics"):
        """
        Recompute the BTS and FTS slacks of every step of the given sequence, from scratch.

        Args:
            sequence: The sequence whose BTS and FTS slacks are recomputed.
        """
        SlackTimeComputer.recompute_bts_from(sequence, 0)
        SlackTimeComputer.recompute_fts_from(sequence, sequence.nb_steps - 1)

    ##################
    # Critical steps #
    ##################

    @staticmethod
    def find_first_critical_step_index_backward_from(sequence: "SequenceForHeuristics", step_index: int) -> int:
        """
        Find the index of the first backward critical step that can be found,
        starting from the given step index and going backward.

        Remark: A backward critical step is a step which BTS is limited by its start time lower bound,
        not by the times of steps before it.

        Args:
            sequence: The sequence to search.
            step_index: The step index to start searching backward from.

        Returns:
            The index of the first critical step found.
        """
        step = sequence[step_index]
        while step.bts < step.start_time - step.activity.start_time_lb:
            step_index -= 1
            step = sequence[step_index]
        return step_index

    @staticmethod
    def find_first_critical_step_index_forward_from(sequence: "SequenceForHeuristics", step_index: int) -> int:
        """
        Find the index of the first forward critical step that can be found,
        starting from the given step index and going forward.

        Remark: A forward critical step is a step which FTS is limited by its end time upper bound,
        not by the times of the steps after it.

        Args:
            sequence: The sequence to search.
            step_index: The step index to start searching forward from.

        Returns:
            The index of the first critical step found.
        """
        step = sequence[step_index]
        while step.fts < step.activity.end_time_ub - (step.start_time + step.activity.duration):
            step_index += 1
            step = sequence[step_index]
        return step_index

    ###############
    # Rigid steps #
    ###############

    @staticmethod
    def _is_rigid(step: "StepForHeuristics") -> bool:
        """
        Whether the given step's activity is an employee unavailability, whose start and end times can not be shifted.

        Args:
            step: The step to check.

        Returns:
            Whether the step is rigid.
        """
        return isinstance(step.activity, Unavailability)

    @staticmethod
    def _rigid_step_indices(sequence: "SequenceForHeuristics") -> list[int]:
        """
        Find the indices, in sequence order, of the given sequence's rigid steps.

        Args:
            sequence: The sequence to search.

        Returns:
            The ordered list of unavailability step indices, empty if the sequence has none.
        """
        return [step_index for step_index in range(sequence.nb_steps)
                if SlackTimeComputer._is_rigid(sequence[step_index])]

    ###############
    # Time shifts #
    ###############

    # TODO: Adapt to lunch breaks
    @staticmethod
    def propagate_earlier_start_time_from(sequence: "SequenceForHeuristics", step_index: int, start_time: int) -> int:
        """
        Shift the step start times to earlier times, in reverse order, starting from the step at the given index.
        The start time of the step at the given index is set to the given start time.
        The difference between the former and the new start times defines a time variation,
        which is then propagated to the steps before it.
        For each of these steps: if its idle time can absorb the propagated time variation,
        i.e. its new start time falls no earlier than its former arrival time, its arrival time remains unchanged,
        and propagation stops; if its idle time can not absorb the propagated time variation,
        i.e. the new start time falls earlier than the previous arrival time,
        its arrival time equals the new start time,
        and the remaining time variation is propagated to the previous step.
        This propagation also stops as soon as the step being visited is rigid (employee unavailability).
        At both ends of the sequence, the arrival times are pinned to start times.

        The BTS and FTS of each shifted step are updated, so the sequence's slacks stay valid without a recomputation.

        NB: The shift is checked against neither the employee's working-time window
        nor the activities' own time windows. BTS is what tells a caller how far back it may ask to go.

        WIP: Instance without lunch breaks.

        Args:
            sequence: The sequence whose steps' times are shifted.
            step_index: Index of the step whose start time is changed,
              and from which times of previous steps are changed in consequence.
            start_time: Start time of the step.

        Returns:
            Index of the first step which start time is changed. When the step at the given index is itself rigid,
            nothing is shifted at all and the index just after it is returned,
            so that pairing it with the caller's own last-changed index describes an empty range.

        Raises:
            ValueError: if the given start time is not strictly earlier than the step's current start time.
        """
        time_variation = sequence[step_index].start_time - start_time
        if time_variation <= 0:
            raise ValueError(
                f"The given start time {start_time} is not earlier than the current start time "
                f"{sequence[step_index].start_time} of step {step_index}, so there is nothing to shift backward"
            )
        while time_variation > 0 and step_index >= 0:
            step = sequence[step_index]
            if SlackTimeComputer._is_rigid(step):
                break
            step.start_time -= time_variation
            step.end_time -= time_variation
            step.bts -= time_variation
            step.fts += time_variation
            time_variation = max(step.arrival_time - step.start_time, 0)
            step.arrival_time -= time_variation
            step_index -= 1
        return step_index + 1

    # TODO: Adapt to lunch breaks
    @staticmethod
    def propagate_later_start_time_from(sequence: "SequenceForHeuristics", step_index: int, start_time: int) -> int:
        """
        Shift the step start times to later times, in sequence order, starting from the step at the given index.
        The start time of the step at the given index is set to the given start time.
        The difference between the former and the new start times defines a time variation,
        which is then propagated to the steps after it.
        For each of these steps: if its idle time can absorb the propagated time variation,
        i.e. its new arrival time falls no later than its former start time, its start time remains unchanged,
        and propagation stops; if its idle time can not absorb the propagated time variation,
        i.e. the new arrival time falls later than the former start time,
        its start time equals the new arrival time,
        and the remaining time variation is propagated to the next step.
        This propagation also stops as soon as the step being visited is rigid (employee unavailability),
        which is left untouched, its arrival time included.
        At both ends of the sequence, the arrival times are pinned to start times.

        The BTS and FTS of each shifted step are updated, so the sequence's slacks stay valid without a recomputation.

        NB: The shift is checked against neither the employee's working-time window
        nor the activities' own time windows. FTS is what tells a caller how far on it may ask to go.

        WIP: Instance without lunch breaks.

        Args:
            sequence: The sequence whose steps' times are shifted.
            step_index: Index of the step which start time is changed,
              and from which times of next steps are changed in consequence.
            start_time: Start time of the step.

        Returns:
            Index of the last step the propagation reached, which is an upper bound rather than an exact answer:
            the propagation stops on the step that absorbed the time variation into its own idle time,
            or on the rigid step it left untouched, and neither of those has its start time changed.
            The given index itself is returned when the step it points at is rigid, nothing being shifted at all.
            Callers use this index to bound the range of steps whose task performances to refresh,
            where too wide a range is wasteful but never wrong.

        Raises:
            ValueError: if the given start time is not strictly later than the step's current start time.
        """
        time_variation = start_time - sequence[step_index].start_time
        if time_variation <= 0:
            raise ValueError(
                f"The given start time {start_time} is not later than the current start time "
                f"{sequence[step_index].start_time} of step {step_index}, so there is nothing to shift forward"
            )
        if SlackTimeComputer._is_rigid(sequence[step_index]):
            return step_index
        if step_index == 0:
            sequence[0].arrival_time = start_time
        while time_variation > 0 and step_index <= sequence.nb_steps - 2:
            step = sequence[step_index]
            step.start_time += time_variation
            step.end_time += time_variation
            step.bts += time_variation
            step.fts -= time_variation
            step_index += 1
            next_step = sequence[step_index]
            if SlackTimeComputer._is_rigid(next_step):
                break
            next_step.arrival_time += time_variation
            time_variation = max(next_step.arrival_time - next_step.start_time, 0)
        if step_index == sequence.nb_steps - 1:
            step = sequence[step_index]
            step.start_time = step.arrival_time
            step.end_time = step.arrival_time
            step.bts += time_variation
            step.fts -= time_variation
        return step_index

    @staticmethod
    def tighten_times(sequence: "SequenceForHeuristics", update_kpis: bool = True):
        """
        Shift the given sequence's steps as close together as their time slacks allow, to minimize idle time:
        first forward from the departure and then backward from the comeback.

        If the sequence contains one or more employee unavailabilities, they split it into independent segments
        (departure -> first unavailability -> ... -> comeback): each segment is tightened on its own,
        forward from its first step and backward from its last,
        since BTS/FTS already only ever reflect slack up to the nearest such rigid step in either direction
        (see recompute_bts_from/recompute_fts_from) and
        propagate_later_start_time_from/propagate_earlier_start_time_from never shift a rigid step's own times.
        With no unavailability, this is exactly one segment spanning the whole sequence.

        Args:
            sequence: The sequence whose steps' times are tightened.
            update_kpis: Whether to keep the sequence's idle-time KPI up to date after the change.
        """
        idle_time_loss = 0
        segment_boundaries = (
                [0] + SlackTimeComputer._rigid_step_indices(sequence) + [sequence.nb_steps - 1]
        )
        for segment_start, segment_end in zip(segment_boundaries, segment_boundaries[1:]):
            time_variation_forward = sequence[segment_start].fts
            if time_variation_forward > 0:
                former_segment_end_time = sequence[segment_end].start_time
                SlackTimeComputer.propagate_later_start_time_from(
                    sequence, segment_start, sequence[segment_start].start_time + time_variation_forward)
                idle_time_loss += time_variation_forward - (sequence[segment_end].start_time - former_segment_end_time)
        for segment_start, segment_end in zip(segment_boundaries, segment_boundaries[1:]):
            time_variation_backward = sequence[segment_end].bts
            if time_variation_backward > 0:
                former_segment_start_time = sequence[segment_start].start_time
                SlackTimeComputer.propagate_earlier_start_time_from(
                    sequence, segment_end, sequence[segment_end].start_time - time_variation_backward)
                idle_time_loss += (time_variation_backward
                                   - (former_segment_start_time - sequence[segment_start].start_time))
        if update_kpis:
            sequence._total_idle_time -= idle_time_loss

    @staticmethod
    @contextmanager
    def deferred_tightening(sequence: "SequenceForHeuristics"):
        """
        Context manager that suspends eager time-tightening for every mutation performed within it, then
        tightens once when the block exits. Reentrant: nested blocks only tighten when the outermost one exits.

        Use this for a well-defined batch of mutations that should be tightened once, right after the batch.
        For a mutation whose tightening is deferred to some later, unrelated call (e.g. a caller that will
        eventually call tighten_times() itself, possibly much later and after other unrelated mutations),
        use _suspend_tightening() instead, which does not tighten on exit.

        Args:
            sequence: The sequence whose eager tightening is suspended for the block's duration.

        Yields:
            The given sequence, unchanged.
        """
        with SlackTimeComputer.suspend_tightening(sequence):
            yield sequence
        if not sequence.is_tightening_suspended:
            SlackTimeComputer.tighten_times(sequence)

    @staticmethod
    @contextmanager
    def suspend_tightening(sequence: "SequenceForHeuristics"):
        """
        Context manager that suspends eager time-tightening for every mutation performed within it, without
        tightening when the block exits (unlike deferred_tightening()) -- the caller remains responsible for
        eventually calling tighten_times() itself. Reentrant, via the same suspension depth as
        deferred_tightening().

        Args:
            sequence: The sequence whose eager tightening is suspended for the block's duration.

        Yields:
            The given sequence, unchanged.
        """
        sequence.suspend_tightening()
        try:
            yield sequence
        finally:
            sequence.resume_tightening()
