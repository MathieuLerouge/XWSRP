# Standard library
import copy

# Third party library
import numpy as np

# Local libraries
from src.modeling.activity import Activity
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.step import Step
from src.modeling.task import Task
from src.modeling.constants import *


# Class Sequence
class Sequence:

    def __init__(self, instance: Instance, employee: Employee, steps: list[Step] = None):
        self._instance = instance
        self._employee = employee
        if steps is None:
            steps = []
        self._steps = steps
        self._KPIs = dict()

    def __getitem__(self, index: int) -> Step:
        return self._steps[index]

    def __setitem__(self, index: int, step: Step):
        self._steps[index] = step

    def __len__(self):
        return len(self._steps)

    def __repr__(self):
        return self._steps.__repr__()

    def to_string(self, with_times: bool = False):
        if with_times:
            self.__repr__()
        else:
            return "[".join([step.activity.name + "; " for step in self._steps]).removesuffix('; ').join("]")

    @property
    def instance(self):
        return self._instance

    @property
    def employee(self):
        return self._employee

    @property
    def nb_steps(self):
        return len(self._steps)

    @property
    def nb_realized_tasks(self) -> int:
        return self._KPIs[NB_PERFORMED_TASKS_KEY]

    @property
    def total_working_duration(self) -> int:
        return self._KPIs[TOTAL_WORKING_DURATION_KEY]

    @property
    def total_traveling_duration(self) -> int:
        return self._KPIs[TOTAL_TRAVELING_DURATION_KEY]

    @property
    def total_traveling_distance(self) -> float:
        return np.round(self._KPIs[TOTAL_TRAVELING_DISTANCE_KEY], 3)

    @property
    def total_idle_time(self) -> int:
        return self._KPIs[TOTAL_IDLE_TIME_KEY]

    @property
    def has_KPIs(self):
        return bool(self._KPIs)

    @property
    def is_time_consistent(self):
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

    def get_step(self, index):
        return self[index]

    def get_steps(self, index_start: int = 0, index_end: int = None) -> list[Step]:
        return self._steps[index_start:index_end] if index_end is not None else self._steps[index_start:]

    def append(self, step: Step):
        self._steps.append(step)

    def insert(self, index: int, step: Step):
        self._steps.insert(index, step)

    def pop(self, index: int = -1):
        return self._steps.pop(index)

    def _copy_steps(self):
        return [step.copy() for step in self._steps]

    def _copy_KPIs(self):
        return copy.deepcopy(self._KPIs)

    def copy(self):
        sequence = Sequence(self._instance, self._employee, self._copy_steps())
        sequence._KPIs = self._copy_KPIs()
        return sequence

    def clear(self):
        while not (self._steps.empty()):
            step = self._steps.pop()
            step.clear()
        self._steps = None
        self._KPIs = None

    ##############
    # Activities #
    ##############

    def get_contained_activities(self, include_departure: bool = True, including_coming_back: bool = True,
                                 include_unavailabilities: bool = True, in_alpha_order: bool = False):
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

    def get_contained_tasks(self, in_alpha_order=False):
        return self.get_contained_activities(False, False, False, in_alpha_order)

    def contains(self, activity: Activity):
        return activity in self.get_contained_activities()

    def get_step_index_of(self, activity: Activity):
        """Get the index in this sequence of the step corresponding to the given activity.

        The given activity must correspond to one of the steps contained in the sequence,
        otherwise a ValueError is raised

        :param activity: the activity that one want to get the index of its corresponding step
        :return: index (int)
        """
        activity_index = 0
        while activity_index < self.nb_steps and self._steps[activity_index].activity.name != activity.name:
            activity_index += 1
        if activity_index >= self.nb_steps:
            raise ValueError(f"The given activity {activity.name} is not in this sequence {self}")
        return activity_index

    def get_step_indices_of_contained_tasks(self):
        tasks_indices = []
        for step_index in range(1, self.nb_steps - 1):
            if isinstance(self._steps[step_index].activity, Task):
                tasks_indices.append(step_index)
        return tasks_indices

    #########
    # Times #
    #########

    def compute_end_times_based_on_fixed_start_times(self):
        for step in self._steps:
            step.end_time = step.start_time + step.activity.duration

    def compute_times_based_on_fixed_start_times(self, lunch_break_description: dict = None,
                                                 update_coming_back_times: bool = True):
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
            self._steps[-1].start_time = self._steps[-1].arrival_time
            self._steps[-1].end_time = self._steps[-1].start_time

    def update_times_according_to_earliest_policy(self):
        # TODO to implement
        raise NotImplementedError("Code not yet implemented")

    # TODO adapt to lunch breaks
    def shift_steps_times_backward_from(self, step_index: int, start_time: int):
        """
        Assumption: instance without lunch breaks.

        :param step_index: index (int) of the step whose start time is changed
        and from which times of previous steps are changed in consequence
        :param start_time: start time of the step (int)
        :return: index (int) of the first step which start time is changed
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
    def shift_steps_times_forward_from(self, step_index: int, start_time: int):
        """
        Assumption: instance without lunch breaks.

        :param step_index: index (int) of the step which start time is changed
        and from which times of next steps are changed in consequence
        :param start_time: start time of the step (int)
        :return: index (int) of the last step which start time is changed
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

    def get_KPI(self, key: str):
        try:
            return self._KPIs[key]
        except KeyError:
            raise ValueError(f"There is no KPI corresponding to the given key {key}")

    def compute_KPIs(self):
        nb_realized_tasks = 0
        total_working_duration = 0
        total_traveling_duration = 0
        total_traveling_distance = 0
        total_idle_time = 0
        for step_index, step in enumerate(self._steps[:-1]):
            if isinstance(step.activity, Task):
                nb_realized_tasks += 1
                total_working_duration += step.activity.duration
            distance = step.activity.distance_to(self._steps[step_index + 1].activity)
            total_traveling_duration += int(np.ceil(distance / self.instance.speed))
            total_traveling_distance += distance
            total_idle_time += step.start_time - step.arrival_time
        self._KPIs = dict()
        self._KPIs[NB_PERFORMED_TASKS_KEY] = nb_realized_tasks
        self._KPIs[TOTAL_WORKING_DURATION_KEY] = total_working_duration
        self._KPIs[TOTAL_TRAVELING_DISTANCE_KEY] = total_traveling_distance
        self._KPIs[TOTAL_TRAVELING_DURATION_KEY] = total_traveling_duration
        self._KPIs[TOTAL_IDLE_TIME_KEY] = total_idle_time
