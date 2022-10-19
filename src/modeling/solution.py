# Standard library
import copy

# Third-party library
import numpy as np

# Local libraries
from src.modeling.activity import Activity
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.departure import Employee
from src.modeling.instance import Instance
from src.modeling.sequence import Sequence
from src.modeling.step import Step
from src.modeling.task import Task
from src.modeling.constants import *
from src.utils.constants import LINE_BREAK_STRING

# Global variables
DISPLACEMENT_STRING = ">>"
TASK_REALIZATION_KEY = 'realized'
TASK_ASSIGNEE_KEY = 'employee_name'
TASK_START_TIME_KEY = 'start_time'
ACTIVITY_BEFORE_LUNCH_KEY = 'activity_before'
ACTIVITY_AFTER_LUNCH_KEY = 'activity_after'
LUNCH_START_TIME_KEY = 'start_time'


# TODO: create a class Realization / Performance
# Class Solution
class Solution:

    def __init__(self, instance: Instance, name: str = None, sequences: dict[str, Sequence] = None,
                 tasks_realizations: dict = None, lunch_breaks_realizations: dict = None):
        self._instance = instance
        self._name = name if name is not None else "Solution" + instance.name
        if sequences is None:
            sequences = dict()
            for employee in self._instance.employees:
                sequences[employee.name] = Sequence(instance, employee)
        self._sequences = sequences
        if tasks_realizations is None:
            tasks_realizations = dict()
            for task_name in self._instance.tasks_names:
                tasks_realizations[task_name] = dict()
                tasks_realizations[task_name][TASK_REALIZATION_KEY] = False
        self._tasks_realizations = tasks_realizations
        self._lunch_breaks_realizations = lunch_breaks_realizations
        self._KPIs = dict()

    def __getitem__(self, employee_name: str):
        try:
            return self._sequences[employee_name]
        except KeyError:
            raise ValueError(f"{employee_name} is not one of the employees of the instance")

    def __repr__(self):
        representation = ""
        if self._sequences is not None:
            for employee_name in self._instance.employees_names:
                sequence = self._sequences[employee_name]
                representation += employee_name + ": "
                for step_index, step in enumerate(sequence.get_steps(index_end=-1)):
                    representation += f"{str(step)} {DISPLACEMENT_STRING} "
                    representation += str(self.compute_traveling_duration(step, sequence[step_index + 1]))
                    representation += f" {DISPLACEMENT_STRING} "
                representation += str(sequence[-1]) + LINE_BREAK_STRING
            representation = representation[:-2]
        return representation

    def __gt__(self, other):
        if not isinstance(other, Solution):
            raise TypeError(f"The other object has a type {type(other)} instead of {Solution}")
        else:
            return (self.total_working_duration > other.total_working_duration or
                    (self.total_working_duration == other.total_working_duration and
                     self.total_traveling_duration < other.total_traveling_duration))

    @property
    def instance(self):
        return self._instance

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def performed_tasks(self):
        return [task for task in self._instance.tasks if self.get_task_realization(task)]

    @property
    def performed_tasks_names(self):
        return [task.name for task in self._instance.tasks if self.get_task_realization(task)]

    @property
    def not_performed_tasks(self):
        return [task for task in self._instance.tasks if not self.get_task_realization(task)]

    @property
    def not_performed_tasks_names(self):
        return [task.name for task in self._instance.tasks if not self.get_task_realization(task)]

    @property
    def nb_performed_tasks(self) -> int:
        try:
            return self._KPIs[NB_REALIZED_TASKS_KEY]
        except KeyError:
            raise AttributeError("KPIs are not computed")

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

    ########
    # Copy #
    ########

    def _copy_sequences(self):
        sequences = dict()
        for employee_name, sequence in self._sequences.items():
            sequences[employee_name] = sequence.copy()
        return sequences

    def _copy_tasks_realizations(self):
        return copy.deepcopy(self._tasks_realizations)

    def _copy_lunch_breaks_realizations(self):
        return copy.deepcopy(self._lunch_breaks_realizations)

    def _copy_KPIs(self):
        return copy.deepcopy(self._KPIs)

    def copy_deprecated(self, copy_name=False):
        name = self._name if copy_name else self._name + "_copy"
        solution = Solution(self._instance, name, self._copy_sequences(), self._copy_tasks_realizations(),
                            self._copy_lunch_breaks_realizations())
        solution._KPIs = self._copy_KPIs()
        return solution

    def copy(self, name: str = None):
        solution_name = self._name + "_copy" if name is None else name
        solution = Solution(self._instance, solution_name, self._copy_sequences(), self._copy_tasks_realizations(),
                            self._copy_lunch_breaks_realizations())
        solution._KPIs = self._copy_KPIs()
        return solution

    #############
    # Sequences #
    #############

    def get_sequence(self, employee: Employee):
        return self._sequences[employee.name]

    def get_sequence_by_name(self, employee_name: str):
        return self._sequences[employee_name]

    ##############
    # Activities #
    ##############

    def get_task_realization(self, task: Task) -> bool:
        return self._tasks_realizations[task.name][TASK_REALIZATION_KEY]

    def set_task_realization(self, task: Task, boolean: bool):
        self._tasks_realizations[task.name][TASK_REALIZATION_KEY] = boolean

    def get_task_assignee(self, task: Task):
        if self.get_task_realization(task):
            return self._instance.get_employee_by_name(self._tasks_realizations[task.name][TASK_ASSIGNEE_KEY])
        else:
            raise ValueError(f"The task {task} is not realized, it does not have assignee")

    def get_tasks_performed_by(self, employee: Employee, in_sequence_order=True):
        if in_sequence_order:
            return self.get_sequence(employee).get_contained_activities(
                include_departure=False, include_unavailabilities=False, including_coming_back=False)
        else:
            return [task for task in self._instance.tasks
                    if self.get_task_realization(task) and self.get_task_assignee(task) == employee]

    def get_tasks_not_performed_by(self, employee: Employee):
        return [task for task in self._instance.tasks
                if not self.get_task_realization(task) or self.get_task_assignee(task) != employee]

    def get_activity_realization(self, activity: Activity):
        if not isinstance(activity, Task):
            return True
        else:
            return self.get_task_realization(activity)

    def get_activity_assignee(self, activity: Activity):
        if not isinstance(activity, Task):
            return activity.employee
        else:
            return self.get_task_assignee(activity)

    def set_task_assignee(self, task: Task, employee: Employee):
        if self.get_task_realization(task):
            self._tasks_realizations[task.name][TASK_ASSIGNEE_KEY] = employee.name
        else:
            raise ValueError(f"The task {task} is not realized, it must be set realized before having any assignee")

    def get_task_start_time(self, task: Task) -> int:
        try:
            return self._tasks_realizations[task.name][TASK_START_TIME_KEY]
        except KeyError:
            raise ValueError(f"The task {task} is not realized, it does not have start time")

    def set_task_start_time(self, task: Task, start_time: int):
        if self.get_task_realization(task):
            self._tasks_realizations[task.name][TASK_START_TIME_KEY] = start_time
        else:
            raise ValueError(f"The task {task} is not realized, it must be set realized before having any start time")

    def get_employee_lunch_break_start_time(self, employee: Employee):
        return self._lunch_breaks_realizations[employee.name][TASK_START_TIME_KEY]

    def get_activity_before_employee_lunch(self, employee: Employee) -> Activity:
        return self._lunch_breaks_realizations[employee.name][ACTIVITY_BEFORE_LUNCH_KEY]

    def get_activity_after_employee_lunch(self, employee: Employee) -> Activity:
        return self._lunch_breaks_realizations[employee.name][ACTIVITY_AFTER_LUNCH_KEY]

    def filter_tasks_names(self, employee: Employee, excluding_tasks_with_higher_skills: bool,
                           excluding_realized_tasks: bool, excluding_tasks_unassigned_to_employee: bool,
                           excluding_tasks_assigned_to_employee: bool):
        tasks_names = []
        if employee is None:
            for task in self._instance.tasks:
                if not (excluding_realized_tasks and self.get_task_realization(task)):
                    tasks_names.append(task.name)
        else:
            for task in self._instance.tasks:
                if excluding_tasks_unassigned_to_employee:
                    if self.get_task_realization(task) and self.get_task_assignee(task) == employee:
                        tasks_names.append(task.name)
                else:
                    if (not (excluding_realized_tasks and self.get_task_realization(task)) and
                        not (excluding_tasks_with_higher_skills and employee.skill_level < task.skill_level) and
                        not (excluding_tasks_assigned_to_employee and self.get_task_realization(task) and
                             self.get_task_assignee(task) == employee)):
                        tasks_names.append(task.name)
        return tasks_names

    ############################################
    # Sequences - Update based on realizations #
    ############################################

    def compute_sequences_based_on_realizations(self):
        self._order_steps_in_sequences()
        if self._instance.has_lunch_break:
            self._compute_lunch_breaks_realizations()
        self._compute_departure_and_comeback_times()
        self._compute_steps_arrival_times()

    def _order_steps_in_sequences(self):

        # Find the tasks realized by each employee
        employees_assigned_tasks = dict()
        for employee_name in self._instance.employees_names:
            employees_assigned_tasks[employee_name] = []
        for task in self._instance.tasks:
            if self.get_task_realization(task):
                employees_assigned_tasks[self.get_task_assignee(task).name].append(
                    (self.get_task_start_time(task), task.name)
                )

        # Create employees' sequences
        for employee in self._instance.employees:

            # Create employee's sequence of tasks without unavailabilities
            employees_assigned_tasks[employee.name].sort()
            sequence = Sequence(self._instance, employee)
            sequence.append(
                Step(activity=Departure(employee=employee), arrival_time=employee.start_time_LB,
                     start_time=employee.start_time_LB, end_time=employee.start_time_LB)
            )
            for start_time, task_name in employees_assigned_tasks[employee.name]:
                task = self._instance.get_task_by_name(task_name)
                sequence.append(
                    Step(activity=task, start_time=start_time, end_time=start_time + task.duration)
                )
            sequence.append(
                Step(activity=ComeBack(employee=employee),
                     start_time=employee.end_time_UB, end_time=employee.end_time_UB)
            )

            # Add employee's unavailabilities
            for unavailability in employee.unavailabilities:
                insertion_index = len(sequence) - 1
                for j, step in enumerate(sequence.get_steps(index_start=1, index_end=-1)):
                    if unavailability.start_time_LB < step.start_time:
                        insertion_index = j + 1
                        break
                step = Step(activity=unavailability, start_time=unavailability.start_time_LB,
                            end_time=unavailability.end_time_UB)
                sequence.insert(insertion_index, step)

            self._sequences[employee.name] = sequence

    def _compute_steps_end_times(self):
        for sequence in self._sequences.values():
            sequence.compute_end_times_based_on_fixed_start_times()

    def _compute_lunch_breaks_realizations(self):

        if self._instance.has_lunch_break:
            self._lunch_breaks_realizations = dict()

            for employee_name, sequence in self._sequences.items():
                lunch_break_realization = dict()

                candidate_step_after_index_min = 1
                while sequence[candidate_step_after_index_min].start_time < (
                        self._instance.lunch_break_time_LB + self._instance.lunch_break_duration):
                    candidate_step_after_index_min += 1
                candidate_step_after_index_max = candidate_step_after_index_min
                while sequence[candidate_step_after_index_max].end_time <= (
                        self._instance.lunch_break_time_UB - self._instance.lunch_break_duration
                ):
                    candidate_step_after_index_max += 1

                for candidate_step_after_index in range(candidate_step_after_index_min,
                                                        candidate_step_after_index_max + 1):
                    candidate_step_before = sequence[candidate_step_after_index - 1]
                    candidate_step_after = sequence[candidate_step_after_index]
                    traveling_duration_between_steps = self.compute_traveling_duration(
                        candidate_step_before, candidate_step_after
                    )
                    duration_before_being_able_to_lunch = max(
                        0, self._instance.lunch_break_time_LB - candidate_step_before.end_time
                    )
                    traveling_duration_before_lunch = min(
                        duration_before_being_able_to_lunch, traveling_duration_between_steps
                    )
                    lunch_break_start_time = max(
                        self._instance.lunch_break_time_LB,
                        candidate_step_before.end_time + traveling_duration_before_lunch
                    )
                    if (lunch_break_start_time + self._instance.lunch_break_duration +
                        traveling_duration_between_steps - traveling_duration_before_lunch) <= \
                            candidate_step_after.start_time:
                        lunch_break_realization[ACTIVITY_BEFORE_LUNCH_KEY] = candidate_step_before.activity
                        lunch_break_realization[ACTIVITY_AFTER_LUNCH_KEY] = candidate_step_after.activity
                        lunch_break_realization[TASK_START_TIME_KEY] = max(
                            candidate_step_before.end_time, self._instance.lunch_break_time_LB
                        )
                        break

                if not (TASK_START_TIME_KEY in lunch_break_realization.keys()):
                    print("LB problem!")
                    lunch_break_realization[ACTIVITY_BEFORE_LUNCH_KEY] = \
                        sequence[candidate_step_after_index_min - 1].activity
                    lunch_break_realization[ACTIVITY_AFTER_LUNCH_KEY] = \
                        sequence[candidate_step_after_index_min].activity
                    lunch_break_realization[TASK_START_TIME_KEY] = max(
                        sequence[candidate_step_after_index_min - 1].end_time,
                        self._instance.lunch_break_time_LB
                    )

                self._lunch_breaks_realizations[employee_name] = lunch_break_realization

    def _compute_departure_and_comeback_times(self):

        for employee_name, sequence in self._sequences.items():

            employee = self._instance.get_employee_by_name(employee_name)
            lunch_break_realization = dict()
            lunch_break_duration = 0
            if self._instance.has_lunch_break:
                lunch_break_realization = self._lunch_breaks_realizations[employee_name]
                lunch_break_duration = self._instance.lunch_break_duration
            else:
                lunch_break_realization[ACTIVITY_BEFORE_LUNCH_KEY] = sequence[0].activity
                lunch_break_realization[ACTIVITY_AFTER_LUNCH_KEY] = sequence[-1].activity

            # Case where the employee does not move
            if len(sequence) == 2:
                sequence[0].arrival_time = employee.start_time_LB
                sequence[0].start_time = sequence[0].arrival_time
                sequence[0].end_time = sequence[0].arrival_time
                sequence[1].arrival_time = employee.start_time_LB + lunch_break_duration
                sequence[1].start_time = sequence[1].arrival_time
                sequence[1].end_time = sequence[1].arrival_time

            # Case where the employee does move
            else:

                # Fill start step
                sequence[0].start_time = (sequence[1].start_time -
                                          self.compute_traveling_duration(sequence[0], sequence[1]))
                if lunch_break_realization[ACTIVITY_BEFORE_LUNCH_KEY] == sequence[0].activity:
                    sequence[0].start_time -= lunch_break_duration
                sequence[0].arrival_time = sequence[0].start_time
                sequence[0].end_time = sequence[0].start_time

                # Fill end step
                sequence[-1].arrival_time = (sequence[-2].end_time +
                                             self.compute_traveling_duration(sequence[-2], sequence[-1]))
                if lunch_break_realization[ACTIVITY_AFTER_LUNCH_KEY] == sequence[-1].activity:
                    sequence[-1].arrival_time += lunch_break_duration
                sequence[-1].start_time = sequence[-1].arrival_time
                sequence[-1].end_time = sequence[-1].arrival_time

    # TODO: change effect of lunch break on arrival time, cf BordeauxV2
    def _compute_steps_arrival_times(self):

        for employee_name, sequence in self._sequences.items():

            if len(sequence) > 2:

                lunch_break_realization = dict()
                lunch_break_duration = 0
                if self._instance.has_lunch_break:
                    lunch_break_realization = self._lunch_breaks_realizations[employee_name]
                    lunch_break_duration = self._instance.lunch_break_duration
                else:
                    lunch_break_realization[ACTIVITY_BEFORE_LUNCH_KEY] = sequence[0].activity
                    lunch_break_realization[ACTIVITY_AFTER_LUNCH_KEY] = sequence[-1].activity

                for previous_step_index, step in enumerate(sequence.get_steps(index_start=1, index_end=-1)):
                    previous_step = sequence[previous_step_index]
                    step.arrival_time = previous_step.end_time + self.compute_traveling_duration(previous_step, step)
                    if lunch_break_realization[ACTIVITY_AFTER_LUNCH_KEY] == step.activity:
                        step.arrival_time += lunch_break_duration

    ####################################################
    # Sequences - Updates according to earliest policy #
    ####################################################

    def update_times_according_to_earliest_policy(self):
        for sequence in self._sequences.values():
            sequence.update_times_according_to_earliest_policy()

    ########
    # KPIs #
    ########

    def get_KPI(self, key: str):
        try:
            return self._KPIs[key]
        except KeyError:
            raise ValueError(f"There is no KPI corresponding to the given key {key}")

    def compute_KPIs(self):
        self._KPIs = dict()
        for KPI_key in KPI_KEYS:
            self._KPIs[KPI_key] = 0
        for sequence in self._sequences.values():
            sequence.compute_KPIs()
            for KPI_key in KPI_KEYS:
                self._KPIs[KPI_key] += sequence.get_KPI(KPI_key)

    #############
    # Traveling #
    #############

    # TODO: remove if not necessary
    # def computeTravelingDistance(self, step1: Step, step2: Step):
    #     return self._instance.compute_traveling_distance(step1.activity, step2.activity)

    def compute_traveling_duration(self, step1: Step, step2: Step):
        return self._instance.compute_traveling_duration(step1.activity, step2.activity)


def compare_solutions(solution1: Solution, solution2: Solution):
    KPIs_descriptions = dict()
    KPIs_descriptions[NB_REALIZED_TASKS_KEY] = {
        'sense': 'max', 'full_name': "number of realized tasks", 'unit': ""
    }
    KPIs_descriptions[TOTAL_WORKING_DURATION_KEY] = {
        'sense': 'max', 'full_name': "total working duration", 'unit': "min"
    }
    KPIs_descriptions[TOTAL_TRAVELING_DURATION_KEY] = {
        'sense': 'min', 'full_name': "total traveling duration", 'unit': "min"
    }
    KPIs_descriptions[TOTAL_IDLE_TIME_KEY] = {
        'sense': 'min', 'full_name': "total idle time", 'unit': "min"
    }
    text = f"Choosing {solution2.name} instead of {solution1.name} implies that:" + LINE_BREAK_STRING
    for key, desc in KPIs_descriptions.items():
        sense = 1 if KPIs_descriptions[key]['sense'] == 'max' else -1
        KPI1 = solution1.get_KPI(key)
        KPI2 = solution2.get_KPI(key)
        if (KPI2 - KPI1) * sense > 0:
            feedback = "(+)"
        elif (KPI2 - KPI1) * sense == 0:
            feedback = "(=)"
        else:
            feedback = "(-)"
        variation = KPI2 - KPI1
        trend = ""
        if variation > 0:
            trend = "increases"
        elif variation < 0:
            trend = "decreases"
        if trend == "":
            text += f"{feedback} the {KPIs_descriptions[key]['full_name']} stays the same;"
        else:
            text += f"{feedback} the {KPIs_descriptions[key]['full_name']} {trend} " \
                    f"by {abs(variation)}{KPIs_descriptions[key]['unit']};"
        text += LINE_BREAK_STRING
    text = text[: -len(LINE_BREAK_STRING) - 1] + "."
    return text
