# Standard library
from typing import Any, Optional

# Third-party library
import numpy as np

# Local libraries
from src.modeling.activity import Activity
from src.modeling.comeback import ComeBack, COMING_BACK_HOME_STRING
from src.modeling.departure import Departure, LEAVING_HOME_STRING
from src.modeling.employee import Employee
from src.modeling.lunchbreakrules import LunchBreakRules
from src.modeling.task import Task
from src.utils.constants import *
from src.utils.location import Location
from src.utils.speed import convert_speed_from_to, M_PER_S_STRING, KM_PER_MIN_STRING, KM_PER_H_STRING
from src.utils.time import convert_time_string_to_nb_minutes, convert_nb_minutes_to_time_string


############
# Instance #
############

class Instance:
    """
    A WSRP instance, including:
    a set of employees, a set of tasks, an optional lunch break,
    and the travel speed used to convert distances into travel durations.

    An employee's "hypothetical" activity corresponds to an activity that an optimization process may assign to them.
    An employee's "hypothetical" activities include their own Departure/ComeBack/Unavailability
    (which are employee-specific) plus every shared task.
    They exist so optimization models can reference "employee X potentially doing activity Y"
    before any Solution/Sequence decides which pairings are actually performed.
    """

    def __init__(self, name: str = "Untitled", speed: float = 1):
        """
        Args:
            name: Name of the instance.
            speed: Travel speed of the employees, in km/min.
        """
        self._name = name
        self._employees: dict[str, Employee] = dict()
        self._tasks: dict[str, Task] = dict()
        self._has_task_unavailabilities = False
        self._has_employee_unavailabilities = False
        self._lunch_break_rules: Optional[LunchBreakRules] = None
        self._hypothetical_activities: dict[str, dict[str, Activity]] = dict()
        self._speed = speed

    def __repr__(self):
        representation = self._name + LINE_BREAK_STRING
        representation += "- nb of employees: " + str(self.nb_employees) + LINE_BREAK_STRING
        representation += "- nb of tasks: " + str(self.nb_tasks) + LINE_BREAK_STRING
        representation += f"- speed: {self._speed}km/min"
        return representation

    ########
    # Name #
    ########

    @property
    def name(self):
        """Name of the instance."""
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def name_case_type(self):
        """
        Naming convention (SNAKE_CASE or CAMEL_CASE) used by this instance's name.

        Raises:
            ValueError: If the name doesn't carry either the snake_case or the camelCase instance-name prefix.
        """
        if INSTANCE_NAME_PREFIX in self.name:
            return SNAKE_CASE
        elif INSTANCE_NAME_PREFIX_BIS in self.name:
            return CAMEL_CASE
        else:
            raise ValueError(f"The case type of the instance name {self.name} is not supported")

    @property
    def name_case_type_is_snake_case(self):
        """Whether this instance's name follows the snake_case naming convention."""
        return self.name_case_type == SNAKE_CASE

    @property
    def name_case_type_is_camel_case(self):
        """Whether this instance's name follows the camelCase naming convention."""
        return self.name_case_type == CAMEL_CASE

    @property
    def core_name(self):
        """
        Name of the instance stripped of its snake_case/camelCase instance-name prefix.

        Raises:
            ValueError: If the name doesn't carry either the snake_case or the camelCase instance-name prefix.
        """
        if self.name_case_type_is_snake_case:
            return self._name.replace(INSTANCE_NAME_PREFIX, "")
        elif self.name_case_type_is_camel_case:
            return self._name.replace(INSTANCE_NAME_PREFIX_BIS, "")
        else:
            raise ValueError(f"The case type of the instance name {self.name} is not supported")

    def create_default_solution_name(self):
        """
        Returns the default solution name derived from this instance's name, using a solution prefix
        matching the instance name's naming convention (snake_case or camelCase).

        Raises:
            ValueError: If the name doesn't carry either the snake_case or the camelCase instance-name prefix.
        """
        if self.name_case_type_is_snake_case:
            return SOLUTION_NAME_PREFIX + self.core_name
        elif self.name_case_type_is_camel_case:
            return SOLUTION_NAME_PREFIX_BIS + self.core_name
        else:
            raise ValueError(f"The name case type is neither {SNAKE_CASE} nor {CAMEL_CASE}")

    #############
    # Employees #
    #############

    @property
    def employees(self) -> list[Employee]:
        """The employees of this instance."""
        return list(self._employees.values())
        # return set(self._employees.values())

    @property
    def employees_names(self) -> list[str]:
        """The names of the employees of this instance."""
        return list(self._employees.keys())
        # return set(self._employees.keys())

    @property
    def nb_employees(self):
        """Number of employees in this instance."""
        return len(self._employees)

    @property
    def total_employees_availability_duration(self):
        """Sum, over all employees, of each employee's working-time window duration (in minutes)."""
        return sum([employee.end_time_ub - employee.start_time_lb for employee in self.employees])

    def get_employee_by_name(self, employee_name: str) -> Employee:
        """
        Returns the employee registered under the given name.

        Args:
            employee_name: Name the employee was registered under (see add_employee).

        Returns:
            The matching Employee instance.

        Raises:
            ValueError: If employee_name isn't one of this instance's employees' names.
        """
        try:
            return self._employees[employee_name]
        except KeyError:
            raise ValueError(f"The given employee's name {employee_name} is not one of the employees' names")

    def get_employees_with_skill_level_higher_than(self, skill_level: int) -> list[Employee]:
        """
        Returns the employees of this instance whose skill level is at least skill_level.

        Args:
            skill_level: Minimum skill level to filter employees on.

        Returns:
            The matching employees.
        """
        return [employee for employee in self.employees if employee.skill_level >= skill_level]

    def add_employee(self, name: str, start_time_lb: int, end_time_ub: int, location: Location, skill_level: int):
        """
        Registers a new employee in this instance.

        Args:
            name: Unique identifier of the employee.
            start_time_lb: Lower bound, in minutes since midnight, of the employee's working-time window.
            end_time_ub: Upper bound, in minutes since midnight, of the employee's working-time window.
            location: Location the employee starts/ends their working day from.
            skill_level: Skill level of the employee, compared against a task's skill level to check eligibility.

        Raises:
            ValueError: If name is already one of this instance's employees' names.
        """
        if name in self._employees.keys():
            raise ValueError(f"The given employee {name} is already among the employees of this instance")
        else:
            self._employees[name] = Employee(name, start_time_lb, end_time_ub, location, skill_level)

    @property
    def has_employee_unavailabilities(self):
        """Whether at least one employee of this instance has a declared unavailability period."""
        return self._has_employee_unavailabilities

    #########
    # Tasks #
    #########

    @property
    def tasks(self) -> list[Task]:
        """The tasks of this instance."""
        return list(self._tasks.values())

    @property
    def tasks_names(self) -> list[str]:
        """The names of the tasks of this instance."""
        return list(self._tasks.keys())

    @property
    def nb_tasks(self):
        """Number of tasks in this instance."""
        return len(self._tasks)

    @property
    def total_tasks_duration(self):
        """Sum, over all tasks, of each task's duration (in minutes)."""
        return sum([task.duration for task in self.tasks])

    def get_task_by_name(self, task_name: str) -> Task:
        """
        Returns the task registered under the given name.

        Args:
            task_name: Name the task was registered under (see add_task).

        Returns:
            The matching Task instance.

        Raises:
            ValueError: If task_name isn't one of this instance's tasks' names.
        """
        try:
            return self._tasks[task_name]
        except KeyError:
            raise ValueError(f"The given task's name {task_name} is not one of the tasks' names")

    def add_task(self, name: str, duration: int, start_time_lb: int, end_time_ub: int,
                 skill_level: int, location: Location):
        """
        Registers a new task in this instance.

        Args:
            name: Unique identifier of the task.
            duration: Duration of the task, in minutes.
            start_time_lb: Lower bound, in minutes since midnight, of the task's time window.
            end_time_ub: Upper bound, in minutes since midnight, of the task's time window.
            skill_level: Skill level required to perform the task.
            location: Location the task is performed at.

        Raises:
            ValueError: If name is already one of this instance's tasks' names.
        """
        if name in self._tasks.keys():
            raise ValueError(f"The given task {name} is already among the tasks of the instance")
        else:
            self._tasks[name] = Task(name, duration, start_time_lb, end_time_ub, skill_level, location)

    @property
    def has_task_unavailabilities(self):
        """Whether at least one task of this instance has a declared unavailability period."""
        return self._has_task_unavailabilities

    ###############
    # Lunch break #
    ###############

    @property
    def lunch_break_time_lb(self) -> int:
        """
        Lower bound, in minutes since midnight, of the lunch break time window.

        Raises:
            AttributeError: If this instance has no lunch break.
        """
        if self._lunch_break_rules is None:
            raise AttributeError("There is no lunch break in this instance")
        return self._lunch_break_rules.lower_bound

    @property
    def lunch_break_time_ub(self) -> int:
        """
        Upper bound, in minutes since midnight, of the lunch break time window.

        Raises:
            AttributeError: If this instance has no lunch break.
        """
        if self._lunch_break_rules is None:
            raise AttributeError("There is no lunch break in this instance")
        return self._lunch_break_rules.upper_bound

    @property
    def lunch_break_duration(self) -> int:
        """
        Duration of the lunch break, in minutes.

        Raises:
            AttributeError: If this instance has no lunch break.
        """
        if self._lunch_break_rules is None:
            raise AttributeError("There is no lunch break in this instance")
        return self._lunch_break_rules.duration

    @property
    def has_lunch_break(self):
        """Whether this instance has a lunch break."""
        return self._lunch_break_rules is not None

    def set_lunch_break(self, lunch_break_lower_bound: int, lunch_break_upper_bound: int, lunch_break_duration: int):
        """
        Sets (or replaces) the lunch break of this instance.

        Args:
            lunch_break_lower_bound: Lower bound, in minutes since midnight, of the lunch break time window.
            lunch_break_upper_bound: Upper bound, in minutes since midnight, of the lunch break time window.
            lunch_break_duration: Duration of the lunch break, in minutes.
        """
        self._lunch_break_rules = LunchBreakRules(
            lunch_break_lower_bound, lunch_break_upper_bound, lunch_break_duration
        )

    ###########################
    # Hypothetical activities #
    ###########################

    def get_hypothetical_activity_by_names(self, activity_name: str, employee_name: str) -> Activity:
        """
        Returns the hypothetical activity registered for employee_name under activity_name.

        Args:
            activity_name: Name of the hypothetical activity to look up.
            employee_name: Name of the employee the activity is looked up for.

        Returns:
            The matching Activity instance.

        Raises:
            ValueError: If employee_name isn't one of this instance's employees' names,
                or activity_name isn't one of the hypothetical activities of that employee.
            AttributeError: If this instance's hypothetical activities haven't been built yet (see update).
        """
        try:
            return self._hypothetical_activities[employee_name][activity_name]
        except KeyError:
            if bool(self._hypothetical_activities):
                if employee_name not in self._hypothetical_activities.keys():
                    raise ValueError(f"The given employee's name {employee_name} is not one of the employees' names")
                else:
                    raise ValueError(
                        f"The given activity's name {activity_name} is not "
                        f"one of the hypothetical tasks of {employee_name}"
                    )
            else:
                raise AttributeError("The _instance must be updated before using this function")

    def _fill_hypothetical_activities(self):
        self._hypothetical_activities = dict()
        for employee_name, employee in self._employees.items():
            employee_activities: dict[str, Activity] = dict()
            employee_activities[LEAVING_HOME_STRING] = Departure(employee)
            for task_name, task in self._tasks.items():
                employee_activities[task_name] = task
            for unavailability in employee.unavailabilities:
                employee_activities[unavailability.name] = unavailability
            employee_activities[COMING_BACK_HOME_STRING] = ComeBack(employee)
            self._hypothetical_activities[employee_name] = employee_activities

    ##########
    # Update #
    ##########

    def update(self):
        """
        Refreshes this instance's derived state:
        rebuilds the hypothetical activities and recomputes whether any task or employee has a declared unavailability.
        Must be called after mutating tasks or employees before relying on
        has_task_unavailabilities, has_employee_unavailabilities, or hypothetical activities.
        """
        self._fill_hypothetical_activities()
        self._has_task_unavailabilities = False
        for task in self.tasks:
            if task.has_unavailability:
                self._has_task_unavailabilities = True
        for employee in self.employees:
            if employee.has_unavailabilities:
                self._has_employee_unavailabilities = True

    #########
    # Speed #
    #########

    @property
    def speed(self):
        """Travel speed of the employees in the instance, in km/min."""
        return self._speed

    @speed.setter
    def speed(self, speed: float):
        """
        Sets the travel speed of the employees in the instance.

        Args:
            speed: Travel speed of the employees in the instance, in km/min.
        """
        self._speed = speed

    def set_speed(self, speed: float, unit: str):
        """
        Sets the travel speed of the employees in the instance, converting it to km/min first.

        Args:
            speed: Travel speed of the employees in the instance, expressed in unit.
            unit: Unit speed is expressed in. Must be one of M_PER_S_STRING, KM_PER_H_STRING, KM_PER_MIN_STRING.

        Raises:
            ValueError: If unit isn't one of the accepted speed units.
        """
        if unit in [M_PER_S_STRING, KM_PER_H_STRING, KM_PER_MIN_STRING]:
            self.speed = convert_speed_from_to(speed, unit, KM_PER_MIN_STRING)
        else:
            raise ValueError(f"The given unit {unit} is not among the accepted units")

    ############
    # Location #
    ############

    @property
    def has_geographic_locations(self):
        """Whether the employees of this instance are located using geographic (rather than cartesian) coordinates."""
        return bool(list(self._employees.values())[0].location.is_geographic())

    #############
    # Traveling #
    #############

    def compute_traveling_duration(self, activity1: Activity, activity2: Activity) -> int:
        """
        Returns the travel duration, in minutes, between two activities' locations at this instance's speed.

        Args:
            activity1: Activity to travel from.
            activity2: Activity to travel to.

        Returns:
            The travel duration in minutes, rounded up to the nearest integer.
        """
        return int(np.ceil(activity1.distance_to(activity2) / self.speed))

    ########
    # Copy #
    ########

    def copy(self, name: Optional[str] = None) -> "Instance":
        """
        Returns a deep copy of this instance, including employees, their unavailabilities, and tasks.

        Args:
            name: Name of the copy. Defaults to this instance's name suffixed with "_copy".

        Returns:
            The new Instance.

        Raises:
            NotImplementedError: If this instance has task unavailabilities.
        """
        if self.has_task_unavailabilities:
            raise NotImplementedError("Instance copy for instance having task unavailabilities is not implemented")
        instance_name = self._name + "_copy" if name is None else name
        instance = Instance(instance_name, self._speed)
        for employee in self.employees:
            instance.add_employee(employee.name, employee.start_time_lb, employee.end_time_ub,
                                   employee.location, employee.skill_level)
            employee_copy = instance.get_employee_by_name(employee.name)
            for unavailability in employee.unavailabilities:
                employee_copy.add_unavailability(unavailability.location, unavailability.start_time_lb,
                                                  unavailability.end_time_ub)
        for task in self.tasks:
            instance.add_task(task.name, task.duration, task.start_time_lb, task.end_time_ub,
                               task.skill_level, task.location)
        instance.update()
        return instance

    ###################
    # Import / Export #
    ###################

    @classmethod
    def from_dict(cls, dictionary: dict) -> "Instance":
        """
        Creates an instance from a dictionary.

        Note that the current version of this function does not support task and employee unavailabilities.

        Args:
            dictionary: Dictionary containing the instance's data.

        Returns:
            The new Instance.

        Raises:
            ValueError: If an employee's or a task's location is neither geographic nor cartesian, or if a task
                cannot be added to the instance.
        """
        instance = cls(dictionary['name'])
        instance.set_speed(dictionary['speed']['value'], dictionary['speed']['unit'])
        for employee_name, employee_data in dictionary['employees'].items():
            start_time = convert_time_string_to_nb_minutes(employee_data['availability']['start_time'])
            end_time = convert_time_string_to_nb_minutes(employee_data['availability']['end_time'])
            if 'latitude' in employee_data['location']:
                location = Location(employee_data['location']['latitude'], employee_data['location']['longitude'])
            elif 'x' in employee_data['location']:
                location = Location(employee_data['location']['x'], employee_data['location']['y'], False)
            else:
                raise ValueError("The given location is not geographic nor cartesian")
            skill_level = int(employee_data['skill level'])
            instance.add_employee(employee_name, start_time, end_time, location, skill_level)
        for task_name, task_data in dictionary['tasks'].items():
            start_time = convert_time_string_to_nb_minutes(task_data['availability']['start_time'])
            end_time = convert_time_string_to_nb_minutes(task_data['availability']['end_time'])
            if 'latitude' in task_data['location']:
                location = Location(task_data['location']['latitude'], task_data['location']['longitude'])
            elif 'x' in task_data['location']:
                location = Location(task_data['location']['x'], task_data['location']['y'], False)
            else:
                raise ValueError("The given location is not geographic nor cartesian")
            duration = int(task_data['duration'])
            skill_level = int(task_data['skill level'])
            try:
                instance.add_task(task_name, duration, start_time, end_time, skill_level, location)
            except ValueError:
                raise ValueError(f"Cannot add {task_name} which data are:"
                                  f"duration: {duration}, start_time: {start_time}, end_time: {end_time}, "
                                  f"skill_level: {skill_level}, location: {location}")
        instance.update()
        return instance

    def to_dict(self) -> dict:
        """
        Creates a dictionary from the instance.

        Note that the current version of this function does not support task and employee unavailabilities.

        Returns:
            The dictionary representation of the instance.
        """
        dictionary: dict[str, Any] = {
            'name': self.name,
            'speed': {'value': self.speed, 'unit': KM_PER_MIN_STRING},
            'employees': dict(),
            'tasks': dict()
        }
        for employee in self.employees:
            dictionary['employees'][employee.name] = {
                'availability': {'start_time': convert_nb_minutes_to_time_string(employee.start_time_lb),
                                  'end_time': convert_nb_minutes_to_time_string(employee.end_time_ub)},
                'location': {'latitude': employee.location.latitude, 'longitude': employee.location.longitude},
                'skill level': employee.skill_level
            }
        for task in self.tasks:
            dictionary['tasks'][task.name] = {
                'availability': {'start_time': convert_nb_minutes_to_time_string(task.start_time_lb),
                                  'end_time': convert_nb_minutes_to_time_string(task.end_time_ub)},
                'location': {'latitude': task.location.latitude, 'longitude': task.location.longitude},
                'duration': task.duration, 'skill level': task.skill_level
            }
        return dictionary
