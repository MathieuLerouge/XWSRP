# Standard libraries
import copy
from typing import cast, Optional

# Third-party library
import numpy as np

# Local libraries
from src.modeling.activity import Activity
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.kpis import KPIs
from src.modeling.step import Step
from src.modeling.task import Task


############
# Sequence #
############

class Sequence:
    """
    An employee's sequence, i.e. an ordered list of steps (activities with arrival, start, and end times)
    for a working day, starting with a Departure step and ending with a ComeBack step.
    """

    def __init__(self, instance: Instance, employee: Employee, steps: Optional[list[Step]] = None):
        """
        Args:
            instance: The instance this sequence belongs to.
            employee: The employee whose activities this sequence describes.
            steps: The ordered steps making up the sequence.
                If None, a default sequence made of a Departure step and a ComeBack step,
                both set at the employee's start_time_lb, is created.
        """
        self._instance = instance
        self._employee = employee
        if steps is None:
            steps = [Step(Departure(employee), employee.start_time_lb, employee.start_time_lb, employee.start_time_lb),
                     Step(ComeBack(employee), employee.start_time_lb, employee.start_time_lb, employee.start_time_lb)]
        self._steps: list[Step] = steps
        self._kpis: Optional[KPIs] = None

    def __getitem__(self, index: int) -> Step:
        return self._steps[index]

    def __setitem__(self, index: int, step: Step):
        self._steps[index] = step

    def __len__(self):
        return len(self._steps)

    def __repr__(self):
        return self._steps.__repr__()

    def to_string(self, with_times: bool = False) -> str:
        """
        Returns a string representation of the sequence.

        Args:
            with_times: If True, include each step's arrival, start, and end times in the representation.
                If False, include only the activities' names.

        Returns:
            str: A string representation of the sequence.
        """
        if with_times:
            return self.__repr__()
        else:
            return "[" + "; ".join([step.activity.name for step in self._steps]) + "]"

    @property
    def instance(self):
        """The problem instance this sequence belongs to."""
        return self._instance

    @property
    def employee(self):
        """The employee whose activities this sequence describes."""
        return self._employee

    @property
    def nb_steps(self):
        """Number of steps in the sequence, including the Departure and ComeBack steps."""
        return len(self._steps)

    @property
    def nb_performed_tasks(self) -> int:
        """
        Number of Task activities actually performed in the sequence.

        Raises:
            AttributeError: If the KPIs of this sequence have not been computed yet.
        """
        if self._kpis is None:
            raise AttributeError("The KPIs of this sequence have not been computed yet")
        return self._kpis.nb_performed_tasks

    @property
    def total_working_duration(self) -> int:
        """
        Total time, in minutes, spent performing tasks in the sequence.

        Raises:
            AttributeError: If the KPIs of this sequence have not been computed yet.
        """
        if self._kpis is None:
            raise AttributeError("The KPIs of this sequence have not been computed yet")
        return self._kpis.total_working_duration

    @property
    def total_traveling_duration(self) -> int:
        """
        Total time, in minutes, spent traveling between steps in the sequence.

        Raises:
            AttributeError: If the KPIs of this sequence have not been computed yet.
        """
        if self._kpis is None:
            raise AttributeError("The KPIs of this sequence have not been computed yet")
        return self._kpis.total_traveling_duration

    @property
    def total_traveling_distance(self) -> float:
        """
        Total distance traveled between steps in the sequence, in km, rounded to 3 decimals.

        Raises:
            AttributeError: If the KPIs of this sequence have not been computed yet.
        """
        if self._kpis is None:
            raise AttributeError("The KPIs of this sequence have not been computed yet")
        return np.round(self._kpis.total_traveling_distance, 3)

    @property
    def total_idle_time(self) -> int:
        """
        Total idle time, in minutes, spent waiting between steps in the sequence.

        Raises:
            AttributeError: If the KPIs of this sequence have not been computed yet.
        """
        if self._kpis is None:
            raise AttributeError("The KPIs of this sequence have not been computed yet")
        return self._kpis.total_idle_time

    @property
    def has_kpis(self):
        """Whether the KPIs of this sequence have already been computed."""
        return self._kpis is not None

    @property
    def kpis(self) -> Optional[KPIs]:
        """A copy of this sequence's computed KPIs, or None if they have not been computed yet."""
        return self._copy_kpis()

    @property
    def is_time_consistent(self):
        """
        Whether the arrival, start, and end times of every step in the sequence are consistent with each
        other: the first step's arrival, start, and end times are equal, each step's arrival time matches
        the previous step's end time plus the traveling duration between them, no step starts before it
        arrives, each step's end time equals its start time plus its activity's duration, and the last
        step's arrival and start times are equal.
        """
        if not (self[0].arrival_time == self[0].start_time == self[0].end_time):
            return False
        for previous_step_index, step in enumerate(self._steps[1:]):
            previous_step = self._steps[previous_step_index]
            traveling_duration_between_steps = \
                self.instance.compute_traveling_duration(previous_step.activity, step.activity)
            if previous_step.end_time + traveling_duration_between_steps != step.arrival_time:
                return False
            if step.arrival_time > step.start_time:
                return False
            if step.start_time + step.activity.duration != step.end_time:
                return False
        if self[-1].arrival_time != self[-1].start_time:
            return False
        return True

    ##########################
    # Operations on sequence #
    ##########################

    def get_step(self, index: int) -> Step:
        return self[index]

    def get_steps(self, index_start: int = 0, index_end: Optional[int] = None) -> list[Step]:
        """
        Returns the steps of the sequence between index_start (included) and index_end (excluded).

        Args:
            index_start: Index of the first step to return.
            index_end: Index one past the last step to return. If None, returns the steps through the
                end of the sequence.

        Returns:
            list[Step]: The requested steps.
        """
        return self._steps[index_start:index_end] if index_end is not None else self._steps[index_start:]

    def append(self, step: Step):
        """
        Appends a step at the end of the sequence.

        Args:
            step: The step to append.

        Raises:
            PermissionError: If the sequence already ends with a ComeBack step.
        """
        if len(self._steps) > 0 and isinstance(self._steps[-1].activity, ComeBack):
            raise PermissionError("No step can be added after a return")
        self._steps.append(step)

    def insert(self, index: int, step: Step):
        self._steps.insert(index, step)

    def pop(self, index: int = -1):
        return self._steps.pop(index)

    def _copy_steps(self) -> list[Step]:
        return [step.copy() for step in self._steps]

    def _copy_kpis(self) -> Optional[KPIs]:
        return copy.deepcopy(self._kpis)

    def copy(self):
        sequence = Sequence(self._instance, self._employee, self._copy_steps())
        sequence._kpis = self._copy_kpis()
        return sequence

    ##############
    # Activities #
    ##############

    def get_contained_activities(self, include_departure: bool = True, including_coming_back: bool = True,
                                 include_unavailabilities: bool = True,
                                 in_alpha_order: bool = False) -> list[Activity]:
        """
        Returns the activities contained in the sequence's steps.

        Args:
            include_departure: If True, include the Departure activity at the start of the sequence.
            including_coming_back: If True, include the ComeBack activity at the end of the sequence.
            include_unavailabilities: If True, include non-Task activities among the steps between the
                Departure and ComeBack activities. If False, only Task activities are included from that range.
            in_alpha_order: If True, sort the activities between the Departure and ComeBack activities
                alphabetically by name. If False, keep them in the sequence's order.

        Returns:
            list[Activity]: The requested activities.
        """
        activities = []
        if include_departure:
            activities.append(self._steps[0].activity)
        if in_alpha_order:
            activities_pairs = []
            for step in self._steps[1:-1]:
                if isinstance(step.activity, Task) or include_unavailabilities:
                    activities_pairs.append((step.activity.name, step.activity))
            activities_pairs.sort()
            for _, activity in activities_pairs:
                activities.append(activity)
        else:
            for step in self._steps[1:-1]:
                if isinstance(step.activity, Task) or include_unavailabilities:
                    activities.append(step.activity)
        if including_coming_back:
            activities.append(self._steps[-1].activity)
        return activities

    def get_contained_tasks(self, in_alpha_order: bool = False) -> list[Task]:
        """
        Returns the Task activities contained in the sequence, excluding Departure and ComeBack.

        Args:
            in_alpha_order: If True, sort the tasks alphabetically by name. If False, keep them in the
                sequence's order.

        Returns:
            list[Task]: The requested tasks.
        """
        return cast(
            list[Task],
            self.get_contained_activities(
                include_departure=False, including_coming_back=False, include_unavailabilities=False,
                in_alpha_order=in_alpha_order
            )
        )

    def contains(self, activity: Activity) -> bool:
        """Whether the given activity is one of the sequence's steps' activities."""
        return activity in self.get_contained_activities()

    def get_step_of(self, activity: Activity) -> Step:
        """
        Returns the step corresponding to the given activity.

        Args:
            activity: The activity whose corresponding step is requested.

        Returns:
            Step: The step whose activity is the given activity.

        Raises:
            ValueError: If the given activity is not one of this sequence's steps' activities.
        """
        for step in self._steps:
            if step.activity == activity:
                return step
        raise ValueError(f"The given activity {activity.name} is not in this sequence {self}")

    def get_step_index_of(self, activity: Activity) -> int:
        """
        Returns the index in this sequence of the step corresponding to the given activity.

        Args:
            activity: The activity whose corresponding step's index is requested.

        Returns:
            int: The index of the step whose activity equals the given activity.

        Raises:
            ValueError: If the given activity is not one of this sequence's steps' activities.
        """
        activity_index = 0
        while activity_index < self.nb_steps and self._steps[activity_index].activity != activity:
            activity_index += 1
        if activity_index >= self.nb_steps:
            raise ValueError(f"The given activity {activity.name} is not in this sequence {self}")
        return activity_index

    def get_step_before(self, activity: Activity) -> Optional[Step]:
        """
        Returns the step preceding the one corresponding to the given activity.

        Args:
            activity: The activity whose preceding step is requested.

        Returns:
            Optional[Step]: The preceding step, or None if the given activity's step is the first one
                in the sequence.
        """
        index = self.get_step_index_of(activity)
        if index == 0:
            return None
        return self._steps[index - 1]

    def get_activity_before(self, activity: Activity) -> Optional[Activity]:
        """
        Returns the activity preceding the given activity in the sequence.

        Args:
            activity: The activity whose preceding activity is requested.

        Returns:
            Optional[Activity]: The preceding activity, or None if the given activity is the first one
                in the sequence.
        """
        step = self.get_step_before(activity)
        return step.activity if step is not None else None

    def get_step_after(self, activity: Activity) -> Optional[Step]:
        """
        Returns the step following the one corresponding to the given activity.

        Args:
            activity: The activity whose following step is requested.

        Returns:
            Optional[Step]: The following step, or None if the given activity's step is the last one
                in the sequence.
        """
        index = self.get_step_index_of(activity)
        if index == self.nb_steps - 1:
            return None
        return self._steps[index + 1]

    def get_activity_after(self, activity: Activity) -> Optional[Activity]:
        """
        Returns the activity following the given activity in the sequence.

        Args:
            activity: The activity whose following activity is requested.

        Returns:
            Optional[Activity]: The following activity, or None if the given activity is the last one
                in the sequence.
        """
        step = self.get_step_after(activity)
        return step.activity if step is not None else None

    def get_first_task_step_index(self) -> Optional[int]:
        """
        Returns the index of the first step in the sequence whose activity is a Task.

        Returns:
            Optional[int]: The index of the first Task step, or None if the sequence contains no Task step.
        """
        index = None
        for step_index in range(1, self.nb_steps - 1):
            if isinstance(self._steps[step_index].activity, Task):
                index = step_index
                break
        return index

    def get_last_task_step_index(self) -> Optional[int]:
        """
        Returns the index of the last step in the sequence whose activity is a Task.

        Returns:
            Optional[int]: The index of the last Task step, or None if the sequence contains no Task step.
        """
        index = None
        for step_index in range(self.nb_steps - 2, 0, -1):
            if isinstance(self._steps[step_index].activity, Task):
                index = step_index
                break
        return index

    def get_step_indices_of_contained_tasks(self) -> list[int]:
        """
        Returns the indices of all steps in the sequence whose activity is a Task.

        Returns:
            list[int]: The indices, in increasing order, of the sequence's Task steps.
        """
        tasks_indices = []
        for step_index in range(1, self.nb_steps - 1):
            if isinstance(self._steps[step_index].activity, Task):
                tasks_indices.append(step_index)
        return tasks_indices

    #########
    # Times #
    #########

    def compute_end_times_based_on_fixed_start_times(self):
        """
        Recomputes every step's end time from its (already set) start time and its activity's duration.
        """
        for step in self._steps:
            step.end_time = step.start_time + step.activity.duration

    def compute_times_based_on_fixed_start_times(self, lunch_break_description: Optional[dict[str, str]] = None,
                                                 update_coming_back_times: bool = True):
        """
        Recomputes every step's arrival and end time from the fixed start times already set on each step.

        Args:
            lunch_break_description: A dict with a 'stepAfter' key giving the name of the activity right
                after which the lunch break takes place, used to add the lunch break's duration to that
                step's arrival time. If None, no lunch break is applied.
            update_coming_back_times: If True and the last step's computed arrival time is within the
                employee's working-time window, also sets the last step's start and end times to its
                arrival time.
        """
        self._steps[0].arrival_time = self._steps[0].start_time
        self._steps[0].end_time = self._steps[0].start_time
        for previous_step_index, step in enumerate(self._steps[1:]):
            previous_step = self._steps[previous_step_index]
            step.arrival_time = (
                previous_step.end_time +
                self._instance.compute_traveling_duration(previous_step.activity, step.activity)
            )
            if lunch_break_description is not None and lunch_break_description['stepAfter'] == step.activity.name:
                step.arrival_time += self._instance.lunch_break_duration
            step.end_time = step.start_time + step.activity.duration
        if update_coming_back_times:
            if self._steps[-1].arrival_time <= self.employee.end_time_ub:
                self._steps[-1].start_time = self._steps[-1].arrival_time
                self._steps[-1].end_time = self._steps[-1].start_time

    def update_times_according_to_earliest_policy(self):
        """
        Updates every step's times according to the earliest-time policy.

        Raises:
            NotImplementedError: Always; this method is not yet implemented.
        """
        # TODO to implement
        raise NotImplementedError("Code not yet implemented")

    # TODO adapt to lunch breaks
    def shift_steps_times_backward_from(self, step_index: int, start_time: int) -> int:
        """
        Assumption: instance without lunch breaks.

        Args:
            step_index: Index of the step whose start time is changed, and from which times of previous
                steps are changed in consequence.
            start_time: New start time of the step at step_index.

        Returns:
            int: The index of the first step whose start time was changed.
        """
        time_variation = self._steps[step_index].start_time - start_time
        while time_variation > 0 and step_index >= 0:
            step = self[step_index]
            step.start_time -= time_variation
            step.end_time -= time_variation
            time_variation = max(step.arrival_time - step.start_time, 0)
            step.arrival_time -= time_variation
            step_index -= 1
        return step_index + 1

    # TODO adapt to lunch breaks
    def shift_steps_times_forward_from(self, step_index: int, start_time: int) -> int:
        """
        Assumption: instance without lunch breaks.

        Args:
            step_index: Index of the step whose start time is changed, and from which times of next
                steps are changed in consequence.
            start_time: New start time of the step at step_index.

        Returns:
            int: The index of the last step whose start time was changed.
        """
        time_variation = start_time - self._steps[step_index].start_time
        if step_index == 0 and time_variation > 0:
            self._steps[0].arrival_time = start_time
        while time_variation > 0 and step_index <= len(self._steps) - 2:
            step = self._steps[step_index]
            next_step = self._steps[step_index + 1]
            step.start_time += time_variation
            step.end_time += time_variation
            next_step.arrival_time += time_variation
            time_variation = max(next_step.arrival_time - next_step.start_time, 0)
            step_index += 1
        self._steps[-1].start_time = self._steps[-1].arrival_time
        self._steps[-1].end_time = self._steps[-1].arrival_time
        return step_index

    ########
    # KPIs #
    ########

    def compute_kpis(self):
        """
        Computes and stores this sequence's KPIs (number of performed tasks, total working duration,
        total traveling duration and distance, and total idle time) based on its current steps.
        """
        nb_realized_tasks = 0
        total_working_duration = 0
        total_traveling_duration = 0
        total_traveling_distance = 0.0
        total_idle_time = 0
        for step_index, step in enumerate(self._steps[:-1]):
            if isinstance(step.activity, Task):
                nb_realized_tasks += 1
                total_working_duration += step.activity.duration
            distance = step.activity.distance_to(self._steps[step_index + 1].activity)
            total_traveling_duration += int(np.ceil(distance / self.instance.speed))
            total_traveling_distance += distance
            total_idle_time += step.start_time - step.arrival_time
        self._kpis = KPIs(nb_realized_tasks, total_working_duration, total_traveling_duration,
                          total_traveling_distance, total_idle_time)
