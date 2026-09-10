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
from src.modeling.lunchbreakperformance import LunchBreakPerformance
from src.modeling.sequence import Sequence
from src.modeling.step import Step
from src.modeling.task import Task
from src.modeling.taskperformance import TaskPerformance
from src.utils.constants import LINE_BREAK_STRING

# Global variables
DISPLACEMENT_STRING = ">>"
TASKS_PERFORMANCES_KEY = 'tasks performances'
SEQUENCES_KEY = 'sequences'


############
# Solution #
############

class Solution:
    """
    A candidate solution to a WSRP instance.

    It tracks which tasks are performed and by whom,
    each employee's ordered Sequence of steps (departure, tasks, lunch break, unavailabilities, comeback),
    each employee's lunch break, and the solution's computed KPIs.
    """

    def __init__(self, instance: Instance, name: Optional[str] = None,
                 sequences: Optional[dict[str, Sequence]] = None,
                 tasks_performances: Optional[dict[str, TaskPerformance]] = None,
                 lunch_breaks_performances: Optional[dict[str, LunchBreakPerformance]] = None):
        """
        Args:
            instance: Instance this solution is built for.
            name: Name of the solution. Defaults to the instance's default solution name.
            sequences: Mapping from employee name to that employee's Sequence.
                Defaults to an empty Sequence (departure/comeback only) per employee of the instance.
            tasks_performances: Mapping from task name to that task's TaskPerformance.
                Defaults to every task of the instance marked as not performed.
            lunch_breaks_performances: Mapping from employee name to that employee's LunchBreakPerformance.
            Left as None until computed by _compute_lunch_breaks_performances.
        """
        self._instance = instance
        self._name = name if name is not None else self._create_name()
        if sequences is None:
            sequences = dict()
            for employee in self._instance.employees:
                sequences[employee.name] = Sequence(instance, employee)
        self._sequences: dict[str, Sequence] = sequences
        if tasks_performances is None:
            tasks_performances = dict()
            for task_name in self._instance.tasks_names:
                tasks_performances[task_name] = TaskPerformance()
        self._tasks_performances: dict[str, TaskPerformance] = tasks_performances
        self._lunch_breaks_performances: Optional[dict[str, LunchBreakPerformance]] = lunch_breaks_performances
        self._kpis: Optional[KPIs] = None

    def __getitem__(self, employee_name: str):
        """
        Returns the Sequence of the employee with the given name.

        Args:
            employee_name: Name of the employee whose Sequence to return.

        Returns:
            The employee's Sequence.

        Raises:
            ValueError: If employee_name is not one of the instance's employees.
        """
        try:
            return self._sequences[employee_name]
        except KeyError:
            raise ValueError(f"{employee_name} is not one of the employees of the instance")

    def __eq__(self, other):
        """
        Returns whether this solution has exactly the same sequence of steps as other, per employee.

        instance, name, computed KPIs, and task/lunch-break performance records are intentionally excluded.
        The latter are derivable from the sequences themselves, so only the sequences determine equality.

        Args:
            other: Object to compare this solution to.

        Returns:
            bool: True if other is a Solution with the same Sequence (by employee name).
        """
        return isinstance(other, Solution) and self._sequences == other._sequences

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

    def __gt__(self, other: "Solution"):
        """
        Returns whether this solution is considered strictly better than other.

        A solution is better if it has a strictly greater total working duration, or an equal total working
        duration and a strictly lower total traveling duration.

        Args:
            other: Solution to compare this one to.

        Returns:
            True if this solution is strictly better than other, False otherwise.

        Raises:
            TypeError: If other is not a Solution.
        """
        if not isinstance(other, Solution):
            raise TypeError(f"The other object has a type {type(other).__name__} instead of {Solution.__name__}")
        else:
            return (self.total_working_duration > other.total_working_duration or
                    (self.total_working_duration == other.total_working_duration and
                     self.total_traveling_duration < other.total_traveling_duration))

    ############
    # Instance #
    ############

    @property
    def instance(self):
        """The Instance this solution is built for."""
        return self._instance

    ########
    # Name #
    ########

    @property
    def name(self):
        """Name of the solution."""
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def core_name(self):
        """Core name of the underlying instance (see Instance.core_name)."""
        return self.instance.core_name

    def _create_name(self):
        """Returns the solution's default name, derived from the instance."""
        return self.instance.create_default_solution_name()

    #############
    # Sequences #
    #############

    def get_sequence(self, employee: Employee):
        """Returns the Sequence of the given employee."""
        return self._sequences[employee.name]

    def get_sequence_by_name(self, employee_name: str):
        """Returns the Sequence of the employee with the given name."""
        return self._sequences[employee_name]

    #############
    # Employees #
    #############

    @property
    def performing_employees(self) -> list[Employee]:
        """Employees who perform at least one task in this solution."""
        return [employee for employee in self._instance.employees if self.get_sequence(employee).nb_performed_tasks > 0]

    @property
    def non_performing_employees(self) -> list[Employee]:
        """Employees who perform no task in this solution."""
        return [employee for employee in self._instance.employees if self.get_sequence(employee).nb_performed_tasks == 0]

    ##############
    # Activities #
    ##############

    @property
    def performed_tasks(self) -> list[Task]:
        """Tasks performed in this solution."""
        return [task for task in self._instance.tasks if self.get_task_performance_status(task)]

    @property
    def performed_tasks_names(self) -> list[str]:
        """Names of the tasks performed in this solution."""
        return [task.name for task in self._instance.tasks if self.get_task_performance_status(task)]

    @property
    def non_performed_tasks(self) -> list[Task]:
        """Tasks not performed in this solution."""
        return [task for task in self._instance.tasks if not self.get_task_performance_status(task)]

    @property
    def non_performed_tasks_names(self) -> list[str]:
        """Names of the tasks not performed in this solution."""
        return [task.name for task in self._instance.tasks if not self.get_task_performance_status(task)]

    @property
    def nb_performed_tasks(self) -> int:
        """
        Number of tasks performed in this solution.

        Raises:
            AttributeError: If the KPIs have not been computed yet (see compute_kpis).
        """
        if self._kpis is None:
            raise AttributeError("KPIs are not computed")
        return self._kpis.nb_performed_tasks

    @property
    def nb_non_performed_tasks(self):
        """Number of tasks not performed in this solution."""
        return self._instance.nb_tasks - self.nb_performed_tasks

    def get_task_performance_status(self, task: Task) -> bool:
        """Returns whether the given task is performed in this solution."""
        return self._tasks_performances[task.name].performed

    def set_task_performance_status(self, task: Task, performed: bool):
        """Sets whether the given task is performed in this solution."""
        self._tasks_performances[task.name].performed = performed

    def get_task_assignee(self, task: Task):
        """
        Returns the employee assigned to the given task.

        Args:
            task: Task whose assignee to return.

        Returns:
            The employee assigned to the task.

        Raises:
            ValueError: If the task is not performed in this solution.
        """
        if self.get_task_performance_status(task):
            return self._instance.get_employee_by_name(self._tasks_performances[task.name].assignee_name)
        else:
            raise ValueError(f"The task {task.name} is not performed, it does not have assignee")

    def get_tasks_performed_by(self, employee: Employee, in_sequence_order=True) -> list[Task]:
        """
        Returns the tasks performed by the given employee.

        Args:
            employee: Employee whose performed tasks to return.
            in_sequence_order: If True, return the tasks in the order they appear in the employee's Sequence.
                If False, return them in the instance's task order instead.

        Returns:
            The tasks performed by the employee.
        """
        if in_sequence_order:
            return cast(
                list[Task],
                self.get_sequence(employee).get_contained_activities(
                    include_departure=False, include_unavailabilities=False, including_coming_back=False
                )
            )
        else:
            return [task for task in self._instance.tasks
                    if self.get_task_performance_status(task) and self.get_task_assignee(task) == employee]

    def get_tasks_not_performed_by(self, employee: Employee) -> list[Task]:
        """
        Returns the tasks not performed by the given employee.

        This includes tasks not performed by anyone, and tasks performed by a different employee.
        """
        return [task for task in self._instance.tasks
                if not self.get_task_performance_status(task) or self.get_task_assignee(task) != employee]

    def get_activity_realization(self, activity: Activity) -> bool:
        """
        Returns whether the given activity is realized in this solution.

        Non-task activities (departure, comeback, unavailabilities, ...) are always considered realized; a task
        is realized only if it is performed in this solution.

        Args:
            activity: Activity to check.

        Returns:
            Whether the activity is realized.
        """
        if not isinstance(activity, Task):
            return True
        else:
            return self.get_task_performance_status(activity)

    def get_activity_assignee(self, activity: Activity):
        """
        Returns the employee performing the given activity.

        Args:
            activity: Activity whose performer to return.

        Returns:
            The employee performing the activity. For a Task, this is its assignee in this solution.
        """
        if not isinstance(activity, Task):
            return activity.employee
        else:
            return self.get_task_assignee(activity)

    def set_task_assignee(self, task: Task, employee: Employee):
        """
        Sets the employee assigned to the given task.

        Args:
            task: Task to assign.
            employee: Employee to assign the task to.

        Raises:
            ValueError: If the task is not performed in this solution.
        """
        if self.get_task_performance_status(task):
            self._tasks_performances[task.name].assignee_name = employee.name
        else:
            raise ValueError(f"The task {task.name} is not performed, "
                             f"it must be set performed before having any assignee")

    def get_task_start_time(self, task: Task) -> int:
        """
        Returns the start time of the given task, in minutes since midnight.

        Args:
            task: Task whose start time to return.

        Returns:
            The task's start time.

        Raises:
            ValueError: If the task is not performed in this solution.
        """
        if self.get_task_performance_status(task):
            return self._tasks_performances[task.name].start_time
        else:
            raise ValueError(f"The task {task.name} is not performed, it does not have start time")

    def set_task_start_time(self, task: Task, start_time: int):
        """
        Sets the start time of the given task.

        Args:
            task: Task whose start time to set.
            start_time: Start time to assign, in minutes since midnight.

        Raises:
            ValueError: If the task is not performed in this solution.
        """
        if self.get_task_performance_status(task):
            self._tasks_performances[task.name].start_time = start_time
        else:
            raise ValueError(f"The task {task.name} is not performed, "
                             f"it must be set performed before having any start time")

    def get_employee_lunch_break_start_time(self, employee: Employee):
        """Returns the start time of the given employee's lunch break, in minutes since midnight."""
        return self._lunch_breaks_performances[employee.name].start_time

    def get_activity_before_employee_lunch(self, employee: Employee) -> Activity:
        """Returns the activity right before the given employee's lunch break."""
        return self._lunch_breaks_performances[employee.name].activity_before

    def get_activity_after_employee_lunch(self, employee: Employee) -> Activity:
        """Returns the activity right after the given employee's lunch break."""
        return self._lunch_breaks_performances[employee.name].activity_after

    ###############################
    # Sequences - Update - Common #
    ###############################

    def _order_steps_in_sequences(self):
        """
        Rebuilds self._sequences from the current tasks performances.

        For each employee, chronologically orders their performed tasks into a new Sequence (Departure, tasks,
        Comeback), then inserts a Step for each of the employee's unavailabilities at the first position where
        it does not start after the following step.
        """

        # Find the tasks performed by each employee
        employees_assigned_tasks = dict()
        for employee_name in self._instance.employees_names:
            employees_assigned_tasks[employee_name] = []
        for task in self._instance.tasks:
            if self.get_task_performance_status(task):
                employees_assigned_tasks[self.get_task_assignee(task).name].append(
                    (self.get_task_start_time(task), task.name)
                )

        # Create employees' sequences
        for employee in self._instance.employees:

            # Create employee's sequence of tasks without unavailabilities
            employees_assigned_tasks[employee.name].sort()
            sequence = Sequence(self._instance, employee)
            for index, (start_time, task_name) in enumerate(employees_assigned_tasks[employee.name]):
                task = self._instance.get_task_by_name(task_name)
                sequence.insert(index + 1,
                                Step(activity=task, start_time=start_time, end_time=start_time + task.duration))
            sequence[-1] = Step(activity=ComeBack(employee=employee),
                                start_time=employee.end_time_ub, end_time=employee.end_time_ub)

            # Add employee's unavailabilities
            for unavailability in employee.unavailabilities:
                insertion_index = len(sequence) - 1
                for step_index, step in enumerate(sequence.get_steps(index_start=1, index_end=-1)):
                    if unavailability.start_time_lb < step.start_time:
                        insertion_index = step_index + 1
                        break
                step = Step(activity=unavailability, start_time=unavailability.start_time_lb,
                            end_time=unavailability.end_time_ub)
                sequence.insert(insertion_index, step)

            self._sequences[employee.name] = sequence

    def _compute_steps_end_times(self):
        """Recomputes each sequence's step end times from their (already fixed) start times."""
        for sequence in self._sequences.values():
            sequence.compute_end_times_based_on_fixed_start_times()

    def _compute_lunch_breaks_performances(self):
        """
        Computes and stores, for each employee, where their lunch break fits into their Sequence.

        For each employee, searches for a pair of consecutive steps around which the lunch break can be
        scheduled without violating the lunch break time window, and records the surrounding activities and the
        break's start time in self._lunch_breaks_performances. No-op if the instance has no lunch break.
        """

        if self._instance.has_lunch_break:
            self._lunch_breaks_performances = dict()

            for employee_name, sequence in self._sequences.items():
                activity_before: Optional[Activity] = None
                activity_after: Optional[Activity] = None
                start_time: Optional[int] = None

                candidate_step_after_index_min = 1
                while sequence[candidate_step_after_index_min].start_time < (
                        self._instance.lunch_break_time_lb + self._instance.lunch_break_duration):
                    candidate_step_after_index_min += 1
                candidate_step_after_index_max = candidate_step_after_index_min
                while sequence[candidate_step_after_index_max].end_time <= (
                        self._instance.lunch_break_time_ub - self._instance.lunch_break_duration
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
                        0, self._instance.lunch_break_time_lb - candidate_step_before.end_time
                    )
                    traveling_duration_before_lunch = min(
                        duration_before_being_able_to_lunch, traveling_duration_between_steps
                    )
                    lunch_break_start_time = max(
                        self._instance.lunch_break_time_lb,
                        candidate_step_before.end_time + traveling_duration_before_lunch
                    )
                    if (lunch_break_start_time + self._instance.lunch_break_duration +
                        traveling_duration_between_steps - traveling_duration_before_lunch) <= \
                            candidate_step_after.start_time:
                        activity_before = candidate_step_before.activity
                        activity_after = candidate_step_after.activity
                        start_time = max(candidate_step_before.end_time, self._instance.lunch_break_time_lb)
                        break

                if start_time is None:
                    print("LB problem!")
                    activity_before = sequence[candidate_step_after_index_min - 1].activity
                    activity_after = sequence[candidate_step_after_index_min].activity
                    start_time = max(
                        sequence[candidate_step_after_index_min - 1].end_time,
                        self._instance.lunch_break_time_lb
                    )

                self._lunch_breaks_performances[employee_name] = LunchBreakPerformance(
                    activity_before, activity_after, start_time
                )

    def _compute_departure_and_comeback_times(self):
        """
        Computes and sets the start/arrival/end times of each sequence's Departure and Comeback steps.

        Derives these times backward/forward from the first/last task step's times, accounting for traveling
        duration and, when the lunch break directly precedes/follows the Departure/Comeback, its duration.
        """

        for employee_name, sequence in self._sequences.items():

            employee = self._instance.get_employee_by_name(employee_name)
            lunch_break_duration = 0
            if self._instance.has_lunch_break:
                lunch_break_realization = self._lunch_breaks_performances[employee_name]
                lunch_break_duration = self._instance.lunch_break_duration
            else:
                lunch_break_realization = LunchBreakPerformance(sequence[0].activity, sequence[-1].activity)

            # Case where the employee does not move
            if len(sequence) == 2:
                sequence[0].arrival_time = employee.start_time_lb
                sequence[0].start_time = sequence[0].arrival_time
                sequence[0].end_time = sequence[0].arrival_time
                sequence[1].arrival_time = employee.start_time_lb + lunch_break_duration
                sequence[1].start_time = sequence[1].arrival_time
                sequence[1].end_time = sequence[1].arrival_time

            # Case where the employee does move
            else:

                # Fill start step
                sequence[0].start_time = (sequence[1].start_time -
                                          self.compute_traveling_duration(sequence[0], sequence[1]))
                if lunch_break_realization.activity_before == sequence[0].activity:
                    sequence[0].start_time -= lunch_break_duration
                sequence[0].arrival_time = sequence[0].start_time
                sequence[0].end_time = sequence[0].start_time

                # Fill end step
                sequence[-1].arrival_time = (sequence[-2].end_time +
                                             self.compute_traveling_duration(sequence[-2], sequence[-1]))
                if lunch_break_realization.activity_after == sequence[-1].activity:
                    sequence[-1].arrival_time += lunch_break_duration
                sequence[-1].start_time = sequence[-1].arrival_time
                sequence[-1].end_time = sequence[-1].arrival_time

    # TODO: change effect of lunch break on arrival time, cf BordeauxV2
    def _compute_steps_arrival_times(self):
        """
        Computes and sets the arrival time of every step, other than Departure and Comeback, in each sequence.

        Accounts for traveling duration and, when the lunch break directly precedes a step, its duration.
        """

        for employee_name, sequence in self._sequences.items():

            if len(sequence) > 2:

                lunch_break_duration = 0
                if self._instance.has_lunch_break:
                    lunch_break_realization = self._lunch_breaks_performances[employee_name]
                    lunch_break_duration = self._instance.lunch_break_duration
                else:
                    lunch_break_realization = LunchBreakPerformance(sequence[0].activity, sequence[-1].activity)

                for previous_step_index, step in enumerate(sequence.get_steps(index_start=1, index_end=-1)):
                    previous_step = sequence[previous_step_index]
                    step.arrival_time = previous_step.end_time + self.compute_traveling_duration(previous_step, step)
                    if lunch_break_realization.activity_after == step.activity:
                        step.arrival_time += lunch_break_duration

    ############################################
    # Sequences - Update based on performances #
    ############################################

    def compute_sequences_based_on_tasks_performances(self):
        """
        Rebuilds every employee's Sequence from the current tasks performances.

        Orders each employee's performed tasks and unavailabilities into a Sequence, computes the lunch break
        realizations (if the instance has one), then computes the Departure/Comeback and intermediate steps'
        times.
        """
        self._order_steps_in_sequences()
        if self._instance.has_lunch_break:
            self._compute_lunch_breaks_performances()
        self._compute_departure_and_comeback_times()
        self._compute_steps_arrival_times()

    #############################################
    # Sequences - Update based on ordered tasks #
    #############################################

    def compute_sequences_based_on_ordered_tasks(self, ordered_tasks: dict[str, list[str]]):
        """
        Rebuilds every given employee's Sequence from an explicit task order, then computes step times.

        Args:
            ordered_tasks: Mapping from employee name to the ordered list of task names they perform. Each
                task's start time is read from this solution's current tasks performances.
        """
        for employee_name in ordered_tasks:
            employee = self.instance.get_employee_by_name(employee_name)
            steps = [Step(Departure(employee), employee.start_time_lb, employee.start_time_lb, employee.start_time_lb)]
            for task_name in ordered_tasks[employee_name]:
                task = self._instance.get_task_by_name(task_name)
                start_time = self.get_task_start_time(task)
                steps.append(Step(task, start_time=start_time, end_time=start_time + task.duration))
            steps.append(Step(ComeBack(employee), start_time=employee.end_time_ub, end_time=employee.end_time_ub))
            self._sequences[employee_name] = Sequence(self._instance, employee, steps)
        self._compute_departure_and_comeback_times()
        self._compute_steps_arrival_times()

    ####################################################
    # Sequences - Updates according to earliest policy #
    ####################################################

    def update_times_according_to_earliest_policy(self):
        """Updates every sequence's step times so that each step starts as early as possible."""
        for sequence in self._sequences.values():
            sequence.update_times_according_to_earliest_policy()

    ########
    # KPIs #
    ########

    @property
    def total_working_duration(self) -> int:
        """
        Total working duration across all sequences, in minutes.

        Raises:
            AttributeError: If the KPIs have not been computed yet (see compute_kpis).
        """
        if self._kpis is None:
            raise AttributeError("KPIs are not computed")
        return self._kpis.total_working_duration

    @property
    def total_traveling_duration(self) -> int:
        """
        Total traveling duration across all sequences, in minutes.

        Raises:
            AttributeError: If the KPIs have not been computed yet (see compute_kpis).
        """
        if self._kpis is None:
            raise AttributeError("KPIs are not computed")
        return self._kpis.total_traveling_duration

    @property
    def total_traveling_distance(self) -> float:
        """
        Total traveling distance across all sequences, in kilometers, rounded to 3 decimals.

        Raises:
            AttributeError: If the KPIs have not been computed yet (see compute_kpis).
        """
        if self._kpis is None:
            raise AttributeError("KPIs are not computed")
        return np.round(self._kpis.total_traveling_distance, 3)

    @property
    def total_idle_time(self) -> int:
        """
        Total idle time across all sequences, in minutes.

        Raises:
            AttributeError: If the KPIs have not been computed yet (see compute_kpis).
        """
        if self._kpis is None:
            raise AttributeError("KPIs are not computed")
        return self._kpis.total_idle_time

    @property
    def has_kpis(self):
        """Whether the KPIs have been computed for this solution."""
        return self._kpis is not None

    @property
    def kpis(self) -> Optional[KPIs]:
        """A copy of this solution's computed KPIs, or None if they have not been computed yet."""
        return self._copy_kpis()

    def compute_kpis(self):
        """Computes and stores this solution's KPIs, as the sum of every sequence's KPIs."""
        kpis = KPIs()
        for sequence in self._sequences.values():
            sequence.compute_kpis()
            kpis = kpis + cast(KPIs, sequence.kpis)
        self._kpis = kpis

    #############
    # Traveling #
    #############

    def compute_traveling_duration(self, step1: Step, step2: Step):
        """Returns the traveling duration between step1's and step2's activities, in minutes."""
        return self._instance.compute_traveling_duration(step1.activity, step2.activity)

    ########
    # Copy #
    ########

    def _copy_sequences(self) -> dict[str, Sequence]:
        """Returns a deep copy of self._sequences."""
        sequences = dict()
        for employee_name, sequence in self._sequences.items():
            sequences[employee_name] = sequence.copy()
        return sequences

    def _copy_tasks_realizations(self) -> dict[str, TaskPerformance]:
        """Returns a deep copy of self._tasks_performances."""
        return copy.deepcopy(self._tasks_performances)

    def _copy_lunch_breaks_realizations(self) -> Optional[dict[str, LunchBreakPerformance]]:
        """Returns a deep copy of self._lunch_breaks_performances."""
        return copy.deepcopy(self._lunch_breaks_performances)

    def _copy_kpis(self) -> Optional[KPIs]:
        """Returns a deep copy of self._kpis."""
        return copy.deepcopy(self._kpis)

    def copy(self, name: Optional[str] = None) -> "Solution":
        """
        Returns a copy of this solution.

        Args:
            name: Name of the copy. Defaults to this solution's name with "_copy" appended.

        Returns:
            The copied Solution.
        """
        solution_name = self._name + "_copy" if name is None else name
        solution = Solution(self._instance, solution_name, self._copy_sequences(), self._copy_tasks_realizations(),
                            self._copy_lunch_breaks_realizations())
        solution._kpis = self._copy_kpis()
        return solution

    ###################
    # Import / Export #
    ###################

    @classmethod
    def from_dict(cls, dictionary, instance: Instance) -> "Solution":
        """
        Builds a Solution from a dictionary representation.

        Args:
            dictionary: Dictionary describing the solution, as produced by to_dict.
            instance: Instance the solution is built for. Must have the name recorded in dictionary.

        Returns:
            The built Solution.

        Raises:
            ValueError: If dictionary's recorded instance name does not match instance's name, or if dictionary
                describes sequences without describing tasks performances.
        """
        if dictionary['instance name'] != instance.name:
            raise ValueError(f"The name {instance.name} of the given instance does not match "
                             f"the instance name {dictionary['instance name']} in the given dictionary")
        if SEQUENCES_KEY in dictionary and TASKS_PERFORMANCES_KEY not in dictionary:
            raise ValueError("The framework does not support solution described via a dictionary such that"
                             "sequences are described but not tasks performances")
        solution = cls(instance, dictionary['name'])
        if TASKS_PERFORMANCES_KEY in dictionary:
            tasks_performances_dictionary = dictionary[TASKS_PERFORMANCES_KEY]
            for task_name, performance_dict in tasks_performances_dictionary.items():
                instance.get_task_by_name(task_name)
                solution._tasks_performances[task_name] = TaskPerformance.from_dict(performance_dict)
            if SEQUENCES_KEY in dictionary:
                solution.compute_sequences_based_on_ordered_tasks(dictionary[SEQUENCES_KEY])
            else:
                solution.compute_sequences_based_on_tasks_performances()
            solution.compute_kpis()
        return solution

    def to_dict(self, with_tasks_performances: bool = True, with_sequences: bool = False) -> dict:
        """
        Returns a dictionary representation of this solution.

        Args:
            with_tasks_performances: If True, include each task's performance status, and, when performed, its
                assignee and start time.
            with_sequences: If True, include each employee's ordered list of performed task names. Requires
                with_tasks_performances to also be True.

        Returns:
            The dictionary representation of this solution.

        Raises:
            ValueError: If with_sequences is True and with_tasks_performances is False.
        """
        if with_sequences and not with_tasks_performances:
            raise ValueError("The framework does not support solution described via a dictionary such that"
                             "sequences are described but not tasks performances")
        dictionary = {'instance name': self.instance.name, 'name': self.name}
        if with_tasks_performances:
            tasks_performances_dictionary = dict()
            for task in self.instance.tasks:
                tasks_performances_dictionary[task.name] = self._tasks_performances[task.name].to_dict()
            dictionary[TASKS_PERFORMANCES_KEY] = tasks_performances_dictionary
        if with_sequences:
            sequences_dictionary = dict()
            for employee in self.instance.employees:
                sequence = self.get_sequence(employee)
                sequences_dictionary[employee.name] = [task.name for task in sequence.get_contained_tasks()]
            dictionary[SEQUENCES_KEY] = sequences_dictionary
        return dictionary
