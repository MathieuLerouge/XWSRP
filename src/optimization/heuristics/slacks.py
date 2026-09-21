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

    # TODO adapt to tasks unavailabilities and lunch breaks
    @staticmethod
    def update_bts_forward_from(sequence: "SequenceForHeuristics", step_index: int):
        """
        Assumption: there are no tasks unavailabilities and no lunch breaks
        Assumption: when step_index > 0, it is assumed that BTS[step_index-1] is computed and valid

        Args:
            sequence: The sequence whose BTS slacks are updated.
            step_index: The step index to start updating BTS from.
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

    # TODO adapt to tasks unavailabilities and lunch breaks
    @staticmethod
    def update_fts_backward_from(sequence: "SequenceForHeuristics", step_index: int):
        """
        Assumption: there are no tasks unavailabilities and no lunch breaks
        Assumption: when step_index < nb_steps - 1, it is assumed that FTS[step_index+1] is computed and valid

        Args:
            sequence: The sequence whose FTS slacks are updated.
            step_index: The step index to start updating FTS from.
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

    @staticmethod
    def update_time_slacks(sequence: "SequenceForHeuristics"):
        """
        Recompute the BTS and FTS slacks of every step of the given sequence, from scratch.

        Args:
            sequence: The sequence whose BTS and FTS slacks are updated.
        """
        SlackTimeComputer.update_bts_forward_from(sequence, 0)
        SlackTimeComputer.update_fts_backward_from(sequence, sequence.nb_steps - 1)

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
        Whether the given step's activity is a permanently fixed employee unavailability,
        whose start and end times must never be shifted.

        Args:
            step: The step to check.

        Returns:
            Whether the step is rigid.
        """
        return isinstance(step.activity, Unavailability)

    @staticmethod
    def _unavailability_step_indices(sequence: "SequenceForHeuristics") -> list[int]:
        """
        Find the indices, in sequence order, of the given sequence's steps
        whose activity is an  employee unavailability.

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

    # TODO adapt to lunch breaks
    @staticmethod
    def shift_steps_times_backward_from(sequence: "SequenceForHeuristics", step_index: int, start_time: int) -> int:
        """
        Assumption: instance without lunch breaks.

        Stops without shifting anything further as soon as the step being visited is rigid (an employee unavailability):
        its own start and end times, being permanently fixed, are never changed.

        Args:
            sequence: The sequence whose steps' times are shifted.
            step_index: Index of the step whose start time is changed,
              and from which times of previous steps are changed in consequence.
            start_time: Start time of the step.

        Returns:
            Index of the first step which start time is changed.
        """
        time_variation = sequence[step_index].start_time - start_time
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

    # TODO adapt to lunch breaks
    @staticmethod
    def shift_steps_times_forward_from(sequence: "SequenceForHeuristics", step_index: int, start_time: int) -> int:
        """
        Assumption: instance without lunch breaks.

        Stops propagating the shift as soon as the next step to be reached is rigid (an employee
        unavailability): its own start and end times, being permanently fixed, are never changed, and
        neither is its arrival time.

        Args:
            sequence: The sequence whose steps' times are shifted.
            step_index: Index of the step which start time is changed,
              and from which times of next steps are changed in consequence.
            start_time: Start time of the step.

        Returns:
            Index of the last step which start time is changed.
        """
        time_variation = start_time - sequence[step_index].start_time
        if step_index == 0 and time_variation > 0:
            sequence[0].arrival_time = start_time
        while time_variation > 0 and step_index <= sequence.nb_steps - 2:
            step = sequence[step_index]
            next_step = sequence[step_index + 1]
            step.start_time += time_variation
            step.end_time += time_variation
            step.bts += time_variation
            step.fts -= time_variation
            if SlackTimeComputer._is_rigid(next_step):
                step_index += 1
                break
            next_step.arrival_time += time_variation
            time_variation = max(next_step.arrival_time - next_step.start_time, 0)
            step_index += 1
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
        (departure -> first unavailability -> ... -> comeback): each segment is tightened on its  own,
        forward from its first step and backward from its last,
        since BTS/FTS already only ever reflect slack up to the nearest such rigid step in either direction
        (see update_bts_forward_from/ update_fts_backward_from) and
        shift_steps_times_forward_from/backward_from never shift a rigid step's own times.
        With no unavailability, this is exactly one segment spanning the whole sequence.

        Args:
            sequence: The sequence whose steps' times are tightened.
            update_kpis: Whether to keep the sequence's idle-time KPI up to date after the change.
        """
        idle_time_loss = 0
        segment_boundaries = (
            [0] + SlackTimeComputer._unavailability_step_indices(sequence) + [sequence.nb_steps - 1]
        )
        for segment_start, segment_end in zip(segment_boundaries, segment_boundaries[1:]):
            time_variation_forward = sequence[segment_start].fts
            if time_variation_forward > 0:
                former_segment_end_time = sequence[segment_end].start_time
                SlackTimeComputer.shift_steps_times_forward_from(
                    sequence, segment_start, sequence[segment_start].start_time + time_variation_forward)
                idle_time_loss += time_variation_forward - (sequence[segment_end].start_time - former_segment_end_time)
        for segment_start, segment_end in zip(segment_boundaries, segment_boundaries[1:]):
            time_variation_backward = sequence[segment_end].bts
            if time_variation_backward > 0:
                former_segment_start_time = sequence[segment_start].start_time
                SlackTimeComputer.shift_steps_times_backward_from(
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
