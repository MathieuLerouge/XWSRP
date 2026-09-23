# Standard library
from typing import Optional, cast

# Local libraries
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.kpis import KPIs
from src.modeling.sequence import Sequence
from src.modeling.task import Task
from src.optimization.heuristics.evaluator import Evaluator
from src.optimization.heuristics.slacks import SlackTimeComputer
from src.optimization.heuristics.step import StepForHeuristics


#########################
# SequenceForHeuristics #
#########################

class SequenceForHeuristics(Sequence):
    """
    A sequence of steps performed by an employee, extended with the state (KPIs, time slacks, tightening
    suspension) and in-place mutation operations (removal, insertion, replacement) needed by the heuristics.
    Time-slack computation lives in SlackTimeComputer, and move evaluation in Evaluator, both operating
    on instances of this class rather than being methods of it.
    """

    def __init__(self, instance: Instance, employee: Employee, steps: Optional[list[StepForHeuristics]] = None):
        """
        Args:
            instance: the instance (Instance) this sequence belongs to.
            employee: the employee (Employee) whose sequence this is.
            steps: the steps (list of StepForHeuristics) making up this sequence;
              if None, a sequence with only a departure and a comeback step,
              both at the employee's start time lower bound, is created.
        """
        super().__init__(instance, employee, None)
        if steps is None:
            steps = \
                [StepForHeuristics(Departure(employee), employee.start_time_lb,
                                   employee.start_time_lb, employee.start_time_lb),
                 StepForHeuristics(ComeBack(employee), employee.start_time_lb,
                                   employee.start_time_lb, employee.start_time_lb)]
        self._steps = steps
        self._tightening_suspension_depth: int = 0
        SlackTimeComputer.recompute_time_slacks(self)

    @classmethod
    def from_sequence(cls, sequence: Sequence):
        steps = [StepForHeuristics.from_step(step) for step in sequence]
        return cls(sequence.instance, sequence.employee, steps)

    def __getitem__(self, index: int) -> StepForHeuristics:
        return cast(StepForHeuristics, self._steps[index])

    @property
    def _nb_performed_tasks(self) -> int:
        """Number of tasks performed in this sequence."""
        return cast(KPIs, self._kpis).nb_performed_tasks

    @_nb_performed_tasks.setter
    def _nb_performed_tasks(self, nb_performed_tasks: int):
        cast(KPIs, self._kpis).nb_performed_tasks = nb_performed_tasks

    @property
    def _total_traveling_duration(self) -> int:
        """Total time, in minutes, spent traveling between steps in this sequence."""
        return cast(KPIs, self._kpis).total_traveling_duration

    @_total_traveling_duration.setter
    def _total_traveling_duration(self, total_traveling_duration: int):
        cast(KPIs, self._kpis).total_traveling_duration = total_traveling_duration

    @property
    def _total_working_duration(self) -> int:
        """Total time, in minutes, spent performing tasks in this sequence."""
        return cast(KPIs, self._kpis).total_working_duration

    @_total_working_duration.setter
    def _total_working_duration(self, total_working_duration: int):
        cast(KPIs, self._kpis).total_working_duration = total_working_duration

    @property
    def _total_traveling_distance(self) -> float:
        """Total distance, in km, traveled between steps in this sequence."""
        return cast(KPIs, self._kpis).total_traveling_distance

    @_total_traveling_distance.setter
    def _total_traveling_distance(self, total_traveling_distance: float):
        cast(KPIs, self._kpis).total_traveling_distance = total_traveling_distance

    @property
    def _total_idle_time(self) -> int:
        """Total idle time, in minutes, spent waiting between steps in this sequence."""
        return cast(KPIs, self._kpis).total_idle_time

    @_total_idle_time.setter
    def _total_idle_time(self, total_idle_time: int):
        cast(KPIs, self._kpis).total_idle_time = total_idle_time

    ########
    # Copy #
    ########

    def _copy_steps(self) -> list[StepForHeuristics]:
        return cast(list[StepForHeuristics], super()._copy_steps())

    def copy(self):
        sequence = self.__class__(self._instance, self._employee, self._copy_steps())
        sequence._kpis = self._copy_kpis()
        return sequence

    ########
    # Step #
    ########

    def get_step(self, index: int) -> StepForHeuristics:
        return cast(StepForHeuristics, self._steps[index])

    ##############
    # Tightening #
    ##############

    @property
    def is_tightening_suspended(self) -> bool:
        """Whether an enclosing SlackTimeComputer.deferred_tightening() block is suppressing eager tightening."""
        return self._tightening_suspension_depth > 0

    def suspend_tightening(self):
        """Increments the tightening-suspension nesting depth; pairs with resume_tightening()."""
        self._tightening_suspension_depth += 1

    def resume_tightening(self):
        """Decrements the tightening-suspension nesting depth; pairs with suspend_tightening()."""
        self._tightening_suspension_depth -= 1

    ##################################
    # Mutations - Private - Feasible #
    ##################################

    def _feasibly_remove_step(self, step_index: int, tighten_times: bool = True, update_kpis: bool = True):
        """
        Remove the step from this sequence at the given index.

        Assumptions (only checked in debug):

        - 1. the given step index is between 1 (included) and len(sequence) - 1 (included);
        - 2. the activity at the given step index is a Task;
        - 3. the times of the sequence are consistent.

        Args:
            step_index: The index of the step that is removed from this sequence.
            tighten_times: If True, tightens the times of the sequence after the step has been removed,
              in order to minimize idle time.
            update_kpis: Whether to keep the KPIs up to date after the change.
        """

        # Check assumptions
        assert 0 < step_index < self.__len__(), \
            f"The given step index {step_index} is not between 1 and {self.__len__() - 1} included"
        assert isinstance(self.get_step(step_index).activity, Task), \
            (f"It is not possible to removed step {step_index} as its corresponding activity "
             f"{self.get_step(step_index).activity.name} is not a task")
        assert self.is_time_consistent, "The times are not consistent"

        # Remove the step
        removed_step = self._steps.pop(step_index)
        # Remark: now that the step has been popped out, step_index corresponds to the step after the removal

        # Get steps around the removed step
        step_before_removal = self[step_index - 1]
        step_before_removal_former_end_time = step_before_removal.end_time
        step_after_removal = self[step_index]
        step_after_removal_former_start_time = step_after_removal.start_time
        step_after_removal_former_arrival_time = step_after_removal.arrival_time

        # Compute traveling duration
        traveling_duration_before_after = \
            self.instance.compute_traveling_duration(step_before_removal.activity, step_after_removal.activity)

        # If the step before removal is a departure, then update it
        if step_index == 1:
            step_after_removal.arrival_time = step_after_removal.start_time
            step_before_removal.end_time = step_after_removal.arrival_time - traveling_duration_before_after
            step_before_removal.start_time = step_before_removal.end_time
            step_before_removal.arrival_time = step_before_removal.start_time
            step_before_removal.bts += step_before_removal.start_time - step_before_removal_former_end_time
            assert step_before_removal.start_time >= step_before_removal_former_end_time, \
                "After removal, departure time is found to be earlier than before"

        # Else, update arrival time of step after removal
        else:
            step_after_removal.arrival_time = step_before_removal.end_time + traveling_duration_before_after
            assert step_after_removal.arrival_time <= step_after_removal_former_arrival_time, \
                "After removal, arrival time of step-after-removal is found to be later than before"

            # If the step after removal is a comeback, then update return times to be all equal
            if step_index == self.nb_steps - 1:
                step_after_removal.fts += step_after_removal.start_time - step_after_removal.arrival_time
                step_after_removal.start_time = step_after_removal.arrival_time
                step_after_removal.end_time = step_after_removal.start_time
                assert step_after_removal.arrival_time <= step_after_removal_former_arrival_time, \
                    "After removal, return time is found to be later than before"

        # Update KPIs if needed
        if update_kpis:
            # Update tasks performance
            self._nb_performed_tasks -= 1
            self._total_working_duration -= removed_step.activity.duration

            # Update traveling duration
            # Remark: rather than computing the traveling durations between the step before / after the removal and
            # the removed step, these durations can be computed thanks to former times values of steps,
            # however it supposes that arrival, start and end times of these steps are valid
            traveling_duration_variation = (
                    traveling_duration_before_after -
                    (removed_step.arrival_time - step_before_removal_former_end_time) -
                    (step_after_removal_former_arrival_time - removed_step.end_time)
            )
            assert (removed_step.arrival_time - step_before_removal_former_end_time ==
                    self.instance.compute_traveling_duration(step_before_removal.activity, removed_step.activity)), \
                "Times before removal were incorrect, traveling duration was not respected"
            assert (step_after_removal_former_arrival_time - removed_step.end_time ==
                    self.instance.compute_traveling_duration(removed_step.activity, step_after_removal.activity)), \
                "Times after removal were incorrect, traveling duration was not respected"
            assert traveling_duration_variation <= 0, \
                "After removal, variation of traveling duration is found to be positive"
            self._total_traveling_duration += traveling_duration_variation

            # Update idle time
            idle_time_variation = (
                    (step_after_removal.start_time - step_after_removal.arrival_time) -
                    (step_after_removal_former_start_time - step_after_removal_former_arrival_time) -
                    (removed_step.start_time - removed_step.arrival_time)
            )
            self._total_idle_time += idle_time_variation

            # Update traveling distance
            self._total_traveling_distance += (
                    step_before_removal.activity.distance_to(step_after_removal.activity) -
                    (step_before_removal.activity.distance_to(removed_step.activity) +
                     removed_step.activity.distance_to(step_after_removal.activity))
            )

        # Update times slacks
        # BTS of steps from steps[0] (included) to steps[step_index - 1] (included) are correct
        # BTS of steps following steps[step_index] (included) must be updated
        SlackTimeComputer.recompute_bts_from(self, step_index)
        # FTS of steps from steps[-1] (included) to steps[step_index] (included) are correct
        # FTS of steps preceding steps[step_index - 1] (included) must be updated
        SlackTimeComputer.recompute_fts_from(self, step_index - 1)

        # Tighten times if needed
        if tighten_times:
            SlackTimeComputer.tighten_times(self, update_kpis)

        # Clear removed step
        removed_step.clear()

    def _feasibly_remove_all_tasks(self, tighten_times: bool = True, update_kpis: bool = True):
        """
        Remove all the steps which correspond to tasks from this sequence.

        Args:
            tighten_times: If True, tightens the times of the sequence after the step has been removed,
              in order to minimize idle time.
            update_kpis: Whether to keep the KPIs up to date after the change.
        """
        step_indices = self.get_step_indices_of_contained_tasks()
        for step_index in reversed(step_indices):
            self._feasibly_remove_step(step_index, False, False)
        if update_kpis:
            self.compute_kpis()
        if tighten_times:
            SlackTimeComputer.tighten_times(self, update_kpis)

    def _feasibly_insert_task_at(self, task: Task, step_index: int, start_time: int,
                                 tighten_times: bool = True, update_kpis: bool = True):
        """
        Insert the given task at the given step index with the given start time;
        this method shall only be used when the insertion is known to be feasible.

        Assumptions (only checked in debug):

        - 1. the given task is not in this sequence;
        - 2. the given step index is between 1 (included) and len(sequence) - 1 (included);
        - 3. the times of the sequence are consistent.

        Args:
            task: The task to insert.
            step_index: The index of the step where the given task is inserted.
            start_time: The start time at which the task is performed.
            tighten_times: If True, tightens the times of the sequence after the step has been inserted,
              in order to minimize idle time.
            update_kpis: Whether to keep the KPIs up to date after the change.

        Returns:
            A pair of indices of the first and last step which start time has been changed.
        """

        # Check assumptions
        assert task not in self.get_contained_tasks(), \
            f"The given task {task.name} is already in this sequence"
        assert 0 < step_index < self.__len__(), \
            f"The given step index {step_index} is not between 1 and {self.__len__() - 1} included"
        assert self.is_time_consistent, "The times are not consistent"

        # Initialize indices of the range of steps which start_time has been changed
        first_step_with_time_change_index = step_index
        last_step_with_time_change_index = step_index

        # Insert step
        inserted_step = StepForHeuristics(task, start_time, start_time, start_time + task.duration)
        self._steps.insert(step_index, inserted_step)
        # Remark: currently the sequence of times around the inserted step is not valid,
        # the current arrival time of the inserted step is likely to be different from the arrival time obtained by
        # considering that the employee leaves the step before the insertion at its current end time, and
        # the current arrival time of the step after the insertion is likely to be different from the arrival time
        # obtained by considering that the employee leaves the inserted step at its current end time

        # Get steps around the insertion
        step_before_insertion = self[step_index - 1]
        step_after_insertion = self[step_index + 1]

        # Compute traveling durations
        traveling_duration_before_after = step_after_insertion.arrival_time - step_before_insertion.end_time
        assert (traveling_duration_before_after ==
                self.instance.compute_traveling_duration(
                    step_before_insertion.activity, step_after_insertion.activity)), \
            "Times before and after insertion were incorrect, traveling duration was not respected"
        traveling_duration_before = self.instance.compute_traveling_duration(step_before_insertion.activity, task)
        traveling_duration_after = self.instance.compute_traveling_duration(task, step_after_insertion.activity)

        # Update times before insertion
        arrival_times_difference_at_inserted_step = (
                inserted_step.arrival_time - (step_before_insertion.end_time + traveling_duration_before)
        )
        idle_time_variation_strictly_up_to_insertion = 0
        idle_time_at_inserted_step = 0
        # If the current arrival time of the inserted step is earlier than the arrival time obtained by considering
        # that the employee leaves the step before the insertion at its current end time,
        # then times before insertion must be shifted backward, this time shift quantity may be partially absorbed,
        # by the idle time contained in the portion of the sequence before the insertion,
        # which can be detected by the time shift of the departure time
        if arrival_times_difference_at_inserted_step < 0:
            backward_time_shift = -arrival_times_difference_at_inserted_step
            departure_former_time = self[0].start_time
            first_step_with_time_change_index = SlackTimeComputer.propagate_earlier_start_time_from(
                self, step_index - 1, step_before_insertion.start_time - backward_time_shift
            )
            departure_backward_time_shift = departure_former_time - self[0].start_time
            idle_time_variation_strictly_up_to_insertion = departure_backward_time_shift - backward_time_shift
        # Otherwise
        else:
            idle_time_at_inserted_step = arrival_times_difference_at_inserted_step
            inserted_step.arrival_time = step_before_insertion.end_time + traveling_duration_before

        # Update times after insertion
        former_idle_time_at_step_after = step_after_insertion.start_time - step_after_insertion.arrival_time
        step_after_insertion.arrival_time = inserted_step.end_time + traveling_duration_after
        difference_start_and_arrival_times_after = step_after_insertion.start_time - step_after_insertion.arrival_time
        if difference_start_and_arrival_times_after < 0:
            forward_time_shift = -difference_start_and_arrival_times_after
            comeback_former_time = self[-1].start_time
            last_step_with_time_change_index = SlackTimeComputer.propagate_later_start_time_from(
                self, step_index + 1, step_after_insertion.arrival_time
            )
            comeback_forward_time_shift = self[-1].start_time - comeback_former_time
            idle_time_variation_strictly_down_from_insertion = \
                -former_idle_time_at_step_after + (comeback_forward_time_shift - forward_time_shift)
        else:
            idle_time_variation_strictly_down_from_insertion = \
                difference_start_and_arrival_times_after - former_idle_time_at_step_after

        # Update KPIs if needed
        if update_kpis:

            # Update tasks performance
            self._nb_performed_tasks += 1
            self._total_working_duration += inserted_step.activity.duration

            # Update traveling duration
            traveling_duration_variation = (
                    traveling_duration_before + traveling_duration_after - traveling_duration_before_after
            )
            self._total_traveling_duration += traveling_duration_variation
            assert traveling_duration_variation >= 0, \
                "After insertion, variation of traveling duration is found to be negative"

            # Update idle time
            idle_time_variation = (
                    idle_time_variation_strictly_up_to_insertion + idle_time_at_inserted_step +
                    idle_time_variation_strictly_down_from_insertion
            )
            self._total_idle_time += idle_time_variation

            # Update traveling distance
            self._total_traveling_distance += (
                    step_before_insertion.activity.distance_to(task) + step_after_insertion.activity.distance_to(task) -
                    step_before_insertion.activity.distance_to(step_after_insertion.activity)
            )

        # Update times slacks
        # BTS of steps from steps[0] (included) to steps[step_index - 1] (included) are correct
        # BTS of steps following steps[step_index] (included) must be updated
        SlackTimeComputer.recompute_bts_from(self, step_index)
        # FTS of steps from steps[-1] (included) to steps[step_index + 1] (included) are correct
        # FTS of steps preceding steps[step_index] (included) must be updated
        SlackTimeComputer.recompute_fts_from(self, step_index)

        # Tighten times
        if tighten_times:
            SlackTimeComputer.tighten_times(self, update_kpis)

        # Return indices of the range of steps which start times has been changed
        return first_step_with_time_change_index, last_step_with_time_change_index

    ####################################
    # Mutations - Private - Infeasible #
    ####################################

    def _infeasibly_insert_task_at(self, task: Task, step_index: int, start_time: int,
                                   start_time_for_backward: int, start_time_for_forward: int):
        """
        Insert the given task at the given step index with the given start time;
        two artificial start times are provided for the computation of the times of the steps before and
        after the insertion; this method shall only be used when the insertion is known to be infeasible.

        Assumptions (only checked in debug):

        - 1. the given task is not in this sequence;
        - 2. the given step index is between 1 (included) and the number of steps - 1 (included);
        - 3. the times of the sequence are consistent.

        Args:
            task: The task to insert.
            step_index: The index of the step where the given task is inserted.
            start_time: The start time of the task to insert.
            start_time_for_backward: The artificial start time of the task to insert used for the
              computation of the times of the steps before the task to insert.
            start_time_for_forward: The artificial start time of the task to insert used for the
              computation of the times of the steps after the task to insert.

        Returns:
            A pair of indices of the first and last step which start time has been changed.
        """

        # Initialize indices of the range of steps which start_time has been changed
        first_step_with_time_change_index = step_index
        last_step_with_time_change_index = step_index

        # Insert step
        inserted_step = StepForHeuristics(task, start_time, start_time, start_time + task.duration)
        self._steps.insert(step_index, inserted_step)

        # Update times before insertion
        step_before_insertion = self[step_index - 1]
        traveling_duration_before = self.instance.compute_traveling_duration(step_before_insertion.activity, task)
        step_before_insertion_start_time = \
            start_time_for_backward - (traveling_duration_before + step_before_insertion.activity.duration)
        if step_before_insertion_start_time < step_before_insertion.start_time:
            first_step_with_time_change_index = SlackTimeComputer.propagate_earlier_start_time_from(
                self, step_index - 1, step_before_insertion_start_time)
            inserted_step.arrival_time = start_time_for_backward
        else:
            inserted_step.arrival_time = step_before_insertion.end_time + traveling_duration_before

        # Update times after insertion
        step_after_insertion = self[step_index + 1]
        traveling_duration_after = self.instance.compute_traveling_duration(task, step_after_insertion.activity)
        step_after_insertion_arrival_time = start_time_for_forward + task.duration + traveling_duration_after
        step_after_insertion.arrival_time = step_after_insertion_arrival_time
        if step_after_insertion.start_time < step_after_insertion_arrival_time:
            last_step_with_time_change_index = SlackTimeComputer.propagate_later_start_time_from(
                self, step_index + 1, step_after_insertion_arrival_time)

        # Return indices of the range of steps which start time has been changed
        return first_step_with_time_change_index, last_step_with_time_change_index

    ######################
    # Mutations - Public #
    ######################

    def remove_step(self, step_index: int):
        """
        Remove the step from this sequence at the given index; tightens times immediately unless called
        within a SlackTimeComputer.deferred_tightening() block.

        Assumptions (only checked in debug):
        - 1. the given step index is between 1 (included) and the number of steps - 1 (included)
        - 2. the activity at the given step index is a Task
        - 3. the times of the sequence are consistent

        Args:
            step_index: The index of the step that is removed from this sequence.

        Returns:
            Whether the change is feasible.
        """
        # Remark: the assumptions are checked in _feasibly_remove_step
        assert self.is_time_consistent, "The times of the sequence are not consistent before removing."
        self._feasibly_remove_step(step_index, not self.is_tightening_suspended, True)
        assert self.is_time_consistent, "The times of the sequence are not consistent after removing."
        return True

    def remove_task(self, task: Task):
        """
        Remove the task from this sequence; tightens times immediately unless called within a
        SlackTimeComputer.deferred_tightening() block.

        Assumptions (only checked in debug):
        - 1. the task is in the sequence
        - 2. the times of the sequence are consistent

        Args:
            task: The task to remove from this sequence.

        Returns:
            Whether the change is feasible.
        """
        assert self.contains(task), f"Task {task} is not in the sequence"
        return self.remove_step(self.get_step_index_of(task))

    def remove_all_tasks(self):
        """
        Remove all the steps which correspond to tasks from this sequence; tightens times immediately
        unless called within a SlackTimeComputer.deferred_tightening() block.

        Returns:
            Whether the change is feasible.
        """
        # Remark: the assumptions are checked in _feasibly_remove_step
        assert self.is_time_consistent, "The times of the sequence are not consistent before removing."
        self._feasibly_remove_all_tasks(not self.is_tightening_suspended, True)
        assert self.is_time_consistent, "The times of the sequence are not consistent after removing."
        return True

    def insert_task_at(
            self, entering_task: Task, step_index: int, start_time: Optional[int] = None,
            start_time_for_backward: Optional[int] = None, start_time_for_forward: Optional[int] = None
    ):
        """
        Insert the given task at the given step index, with the given start time if one is provided, or
        the best feasible start time as found by Evaluator.evaluate_insertion_at() otherwise. Tightens
        times immediately unless called within a SlackTimeComputer.deferred_tightening() block.

        Args:
            entering_task: The task to insert.
            step_index: The index of the step where the given task is inserted.
            start_time: The start time at which the task is performed. If None, it is computed by
              Evaluator.evaluate_insertion_at(), along with start_time_for_backward and start_time_for_forward.
            start_time_for_backward: The artificial start time of the task to insert used for the
              computation of the times of the steps before the task to insert, when the insertion is
              infeasible. None when the insertion is feasible.
            start_time_for_forward: The artificial start time of the task to insert used for the
              computation of the times of the steps after the task to insert, when the insertion is
              infeasible. None when the insertion is feasible.

        Returns:
            A pair made of a boolean indicating whether the change is feasible, and a pair of indices of
            the first and last step which start time has been changed.
        """

        if start_time is None:
            # NB: Times must be computed even when the entering task is skill-infeasible for the employee:
            # this method only reports time feasibility, so callers that want to force an infeasible insertion anyway
            # (e.g. Solution.insert_task_after_activity(..., ignore_skill_constraint=True))
            # still need real start times rather than the None values left by a skill-infeasible early return.
            evaluation = Evaluator.evaluate_insertion_at(
                self, entering_task, step_index, compute_times_only_if_skill_constraints_satisfied=False)
            start_time = evaluation.start_time
            start_time_for_backward = evaluation.earliest_start_time_for_upstream
            start_time_for_forward = evaluation.latest_start_time_for_downstream
        insertion_is_feasible = start_time_for_backward is None

        # If the insertion is feasible (that is to say there are no start time for backward and forward),
        # then do the change and return a boolean True as it is feasible
        if insertion_is_feasible:
            assert self.is_time_consistent, "The times of the sequence are not consistent before inserting"
            first_step_with_time_change_index, last_step_with_time_change_index = \
                self._feasibly_insert_task_at(entering_task, step_index, start_time,
                                              not self.is_tightening_suspended, True)
            assert self.is_time_consistent, "The times of the sequence are not consistent after inserting"
            return True, (first_step_with_time_change_index, last_step_with_time_change_index)

        # If the insertion is not feasible,
        # then do the change and return a boolean False as it is not feasible
        else:
            first_step_with_time_change_index, last_step_with_time_change_index = \
                self._infeasibly_insert_task_at(entering_task, step_index, start_time,
                                                cast(int, start_time_for_backward), cast(int, start_time_for_forward))
            return False, (first_step_with_time_change_index, last_step_with_time_change_index)

    def replace_task_by_another_at(
            self, entering_task: Task, step_index: int, start_time: Optional[int] = None,
            start_time_for_backward: Optional[int] = None, start_time_for_forward: Optional[int] = None
    ):
        """
        Replace the task at the given step index by the given entering task, which must not already be in
        this sequence, removing the former step and inserting the entering task in its place. Removal and
        insertion are both performed within a SlackTimeComputer.deferred_tightening() block, so times are
        tightened at most once, after both steps, rather than in between them.

        Assumptions (only checked in debug):

        - 1. the entering task is not already in the sequence;
        - 2. the given step index is between 1 (included) and the number of steps - 1 (included);
        - 3. the activity at the given step index is a Task;
        - 4. the times of the sequence are consistent.

        Args:
            entering_task: The task to insert in place of the one removed.
            step_index: The index of the step whose task is replaced.
            start_time: The start time at which the entering task is performed.
              If None, it is computed by Evaluator.evaluate_insertion_at(),
              along with start_time_for_backward and start_time_for_forward.
            start_time_for_backward: The artificial start time of the entering task used for the
              computation of the times of the steps before it, when the insertion is infeasible.
              None when the insertion is feasible.
            start_time_for_forward: The artificial start time of the entering task used for the
              computation of the times of the steps after it, when the insertion is infeasible.
              None when the insertion is feasible.

        Returns:
            A pair made of a boolean indicating whether the change is feasible,
            and a pair of indices of the first and last step which start time has been changed.
        """

        # Check assumptions
        # Remark: the assumptions are already checked in remove_step and insert_task_at

        with SlackTimeComputer.deferred_tightening(self):
            # Remove the given step from this sequence
            self.remove_step(step_index)

            # Insert the task in this sequence at the given step index
            result = self.insert_task_at(entering_task, step_index,
                                         start_time, start_time_for_backward, start_time_for_forward)
        return result
