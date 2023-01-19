#! /usr/bin/env python3
# coding: utf-8


# Third party library
import numpy as np

# Local libraries
from src.modeling.activity import Activity
from src.modeling.comeback import ComeBack, COMING_BACK_HOME_STRING
from src.modeling.departure import Departure, LEAVING_HOME_STRING
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.utils.constants import LINE_BREAK_STRING, INSTANCE_NAME_PREFIX, INSTANCE_NAME_PREFIX_BIS, \
    INSTANCE_VERSION_SYMBOL, SNAKE_CASE, CAMEL_CASE
from src.utils.location import Location
from src.utils.speed import convert_speed_from_to, M_PER_S_STRING, KM_PER_MIN_STRING, KM_PER_H_STRING
from src.utils.time import convert_time_string_to_nb_minutes, convert_nb_minutes_to_time_string
from src.utils.timeset import TimeInterval


# Class Instance
class Instance:

    def __init__(self, name: str = "Untitled", speed: float = 1):
        self._name = name
        self._employees = dict()
        self._tasks = dict()
        self._has_task_unavailabilities = False
        self._has_employee_unavailabilities = False
        self._lunch_break = dict()
        self._hypothetical_activities = dict()
        self._speed = speed
        self._version = None

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
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def name_case_type(self):
        if INSTANCE_NAME_PREFIX in self.name:
            return SNAKE_CASE
        elif INSTANCE_NAME_PREFIX_BIS in self.name:
            return CAMEL_CASE
        else:
            raise ValueError(f"The case type of the instance name {self.name} is not supported")

    @property
    def name_case_type_is_snake_case(self):
        return self.name_case_type == SNAKE_CASE

    @property
    def name_case_type_is_camel_case(self):
        return self.name_case_type == CAMEL_CASE

    @property
    def core_name(self):
        if self.name_case_type_is_snake_case:
            return self._name.replace(INSTANCE_NAME_PREFIX, "")
        elif self.name_case_type_is_camel_case:
            return self._name.replace(INSTANCE_NAME_PREFIX_BIS, "")
        else:
            raise ValueError(f"The case type of the instance name {self.name} is not supported")

    @property
    def full_name(self):
        if self.version is None:
            return self.name
        else:
            return self.name + INSTANCE_VERSION_SYMBOL + str(self.version)

    ###########
    # Version #
    ###########

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, version: int):
        self._version = version

    #############
    # Employees #
    #############

    @property
    def employees(self) -> list[Employee]:
        return list(self._employees.values())
        # return set(self._employees.values())

    @property
    def employees_names(self) -> list[str]:
        return list(self._employees.keys())
        # return set(self._employees.keys())

    @property
    def nb_employees(self):
        return len(self._employees)

    @property
    def total_employees_availability_duration(self):
        return sum([employee.end_time_UB - employee.start_time_LB for employee in self.employees])

    def get_employee_by_name(self, employee_name: str) -> Employee:
        try:
            return self._employees[employee_name]
        except KeyError:
            raise ValueError(f"The given employee's name {employee_name} is not one of the employees' names")

    def get_employees_with_skill_level_higher_than(self, skill_level: int):
        return [employee for employee in self.employees if employee.skill_level >= skill_level]

    def add_employee(self, name: str, start_time_LB: int, end_time_UB: int, location: Location, skill_level: int):
        if name in self._employees.keys():
            raise ValueError(f"The given employee {name} is already among the employees of this instance")
        else:
            self._employees[name] = Employee(name, start_time_LB, end_time_UB, location, skill_level)

    @property
    def has_employee_unavailabilities(self):
        return self._has_employee_unavailabilities

    #########
    # Tasks #
    #########

    @property
    def tasks(self) -> list[Task]:
        return list(self._tasks.values())

    @property
    def tasks_names(self) -> list[str]:
        return list(self._tasks.keys())

    @property
    def nb_tasks(self):
        return len(self._tasks)

    @property
    def total_tasks_duration(self):
        return sum([task.duration for task in self.tasks])

    def get_task_by_name(self, task_name: str) -> Task:
        try:
            return self._tasks[task_name]
        except KeyError:
            raise ValueError(f"The given task's name {task_name} is not one of the tasks' names")

    def add_task(self, name: str, duration: int, start_time_LB: int, end_time_UB: int,
                 skill_level: int, location: Location):
        if name in self._tasks.keys():
            raise ValueError(f"The given task {name} is already among the tasks of the instance")
        else:
            self._tasks[name] = Task(name, duration, start_time_LB, end_time_UB, skill_level, location)

    @property
    def has_task_unavailabilities(self):
        return self._has_task_unavailabilities

    ###############
    # Lunch break #
    ###############

    @property
    def lunch_break_time_LB(self) -> int:
        try:
            return self._lunch_break["TW"].lower_bound
        except KeyError:
            raise AttributeError("There is no lunch break in this instance")

    @property
    def lunch_break_time_UB(self) -> int:
        try:
            return self._lunch_break["TW"].upper_bound
        except KeyError:
            raise AttributeError("There is no lunch break in this instance")

    @property
    def lunch_break_duration(self) -> int:
        try:
            return self._lunch_break["duration"]
        except KeyError:
            raise AttributeError("There is no lunch break in this instance")

    @property
    def has_lunch_break(self):
        return bool(self._lunch_break)

    def set_lunch_break(self, lunch_break_lower_bound: int, lunch_break_upper_bound: int, lunch_break_duration: int):
        self._lunch_break["TW"] = TimeInterval(lunch_break_lower_bound, lunch_break_upper_bound)
        self._lunch_break["duration"] = lunch_break_duration

    ###########################
    # Hypothetical activities #
    ###########################

    def get_hypothetical_activity_by_names(self, activity_name: str, employee_name: str):
        try:
            return self._hypothetical_activities[employee_name][activity_name]
        except KeyError:
            if bool(self._hypothetical_activities):
                if employee_name in self._hypothetical_activities.keys():
                    ValueError(f"The given employee's name {employee_name} is not one of the employees' names")
                else:
                    ValueError(f"The given activity's name {activity_name} is not one of the hypothetical tasks"
                               f" of {employee_name}")
            else:
                return AttributeError("The _instance must be updated before using this function")

    def _fill_hypothetical_activities(self):
        self._hypothetical_activities = dict()
        for employee_name, employee in self._employees.items():
            employee_activities = dict()
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
        """
        Returns  of the employees in the instance
        NB: the speed unit is km/min

        :return:
        """
        return self._speed

    @speed.setter
    def speed(self, speed: float):
        """
        Set the speed of the employees in the instance.
        NB: the speed unit is km/min

        :param speed: the speed of the employees in the instance in km/min
        :return:
        """
        self._speed = speed

    def set_speed(self, speed: float, unit: str):
        if unit in [M_PER_S_STRING, KM_PER_H_STRING, KM_PER_MIN_STRING]:
            self.speed = convert_speed_from_to(speed, unit, KM_PER_MIN_STRING)
        else:
            raise ValueError(f"The given unit {unit} is not among the accepted units")

    ############
    # Location #
    ############

    @property
    def has_geographic_locations(self):
        return bool(list(self._employees.values())[0].location.is_geographic())

    #############
    # Traveling #
    #############

    def compute_traveling_duration(self, activity1: Activity, activity2: Activity):
        return int(np.ceil(activity1.distance_to(activity2) / self.speed))

    ########
    # Copy #
    ########

    def copy(self, name: str = None):
        if self.has_task_unavailabilities:
            raise NotImplementedError("Instance copy for instance having task unavailabilities is not implemented")
        instance_name = self._name + "_copy" if name is None else name
        instance = Instance(instance_name, self._speed)
        for employee in self.employees:
            instance.add_employee(employee.name, employee.start_time_LB, employee.end_time_UB,
                                  employee.location, employee.skill_level)
            employee_copy = instance.get_employee_by_name(employee.name)
            for unavailability in employee.unavailabilities:
                employee_copy.add_unavailability(unavailability.location, unavailability.start_time_LB,
                                                 unavailability.end_time_UB)
        for task in self.tasks:
            instance.add_task(task.name, task.duration, task.start_time_LB, task.end_time_UB,
                              task.skill_level, task.location)
        instance.update()
        return instance

    ###################
    # Import / Export #
    ###################

    @classmethod
    def from_dict(cls, dictionary):
        """
        Create an instance from a dictionary
        NB: the current version of this function does not support task and employees unavailabilities

        :param dictionary: the dictionary containing the instance's data
        :return: the instance (Instance)
        """
        instance = cls(dictionary['name'])
        instance.set_speed(dictionary['speed']['value'], dictionary['speed']['unit'])
        for employee_name, employee_data in dictionary['employees'].items():
            start_time = convert_time_string_to_nb_minutes(employee_data['availability']['start_time'])
            end_time = convert_time_string_to_nb_minutes(employee_data['availability']['end_time'])
            location = Location(employee_data['location']['latitude'], employee_data['location']['longitude'])
            skill_level = int(employee_data['skill level'])
            instance.add_employee(employee_name, start_time, end_time, location, skill_level)
        for task_name, task_data in dictionary['tasks'].items():
            start_time = convert_time_string_to_nb_minutes(task_data['availability']['start_time'])
            end_time = convert_time_string_to_nb_minutes(task_data['availability']['end_time'])
            location = Location(task_data['location']['latitude'], task_data['location']['longitude'])
            duration = int(task_data['duration'])
            skill_level = int(task_data['skill level'])
            instance.add_task(task_name, duration, start_time, end_time, skill_level, location)
        instance.update()
        return instance

    def to_dict(self):
        """
        Create a dictionary from the instance
        NB: the current version of this function does not support task and employees unavailabilities

        :return: the dictionary
        """
        dictionary = {'name': self.name, 'speed': {'value': self.speed, 'unit': KM_PER_MIN_STRING},
                      'employees': dict(), 'tasks': dict()}
        for employee in self.employees:
            dictionary['employees'][employee.name] = {
                'availability': {'start_time': convert_nb_minutes_to_time_string(employee.start_time_LB),
                                 'end_time': convert_nb_minutes_to_time_string(employee.end_time_UB)},
                'location': {'latitude': employee.location.latitude, 'longitude': employee.location.longitude},
                'skill level': employee.skill_level
            }
        for task in self.tasks:
            dictionary['tasks'][task.name] = {
                'availability': {'start_time': convert_nb_minutes_to_time_string(task.start_time_LB),
                                 'end_time': convert_nb_minutes_to_time_string(task.end_time_UB)},
                'location': {'latitude': task.location.latitude, 'longitude': task.location.longitude},
                'duration': task.duration,
                'skill level': task.skill_level
            }
        return dictionary
