#! /usr/bin/env python3
# coding: utf-8


# Local libraries
from model.task import Task
from model.unavailability import Unavailability
from utils.location import Location
from utils.time import convert_nb_minutes_to_time_string
from utils.timeset import TimeInterval


# Class Employee
class Employee:

    def __init__(self, name: str, start_time_LB: int, end_time_UB: int, location: Location, skill_level: int):
        self._name = name
        self._start_time_LB = start_time_LB
        self._end_time_UB = end_time_UB
        self._location = location
        self._skill_level = skill_level
        self._nb_unavailabilities = 0
        self._unavailabilities = dict()

    def __eq__(self, employee):
        if isinstance(employee, Employee):
            return self.name == employee._name
        else:
            return False

    def __hash__(self):
        return hash(self._name)

    def __repr__(self):
        return f"{self.name}: working during {TimeInterval(self._start_time_LB, self._end_time_UB)} " \
               f"located at {self.location} having skill {self._skill_level} " \
               f"and having {self._nb_unavailabilities} unavailability(ies)"

    @property
    def name(self):
        return self._name

    @property
    def start_time_LB(self):
        return self._start_time_LB

    def get_start_time_LB(self, as_integer: bool = True):
        if as_integer:
            return self._start_time_LB
        else:
            return convert_nb_minutes_to_time_string(self._start_time_LB)

    @property
    def end_time_UB(self):
        return self._end_time_UB

    def get_end_time_UB(self, as_integer: bool = True):
        if as_integer:
            return self._end_time_UB
        else:
            return convert_nb_minutes_to_time_string(self._end_time_UB)

    @property
    def TW(self):
        return TimeInterval(self._start_time_LB, self._end_time_UB)

    @property
    def location(self):
        return self._location

    @property
    def skill_level(self):
        return self._skill_level

    @property
    def nb_unavailabilities(self):
        return self._nb_unavailabilities

    @property
    def unavailabilities(self) -> list[Unavailability]:
        return list(self._unavailabilities.values())

    def add_unavailability(self, location: Location, start_time: int, end_time: int):
        for unavailability in self._unavailabilities:
            if unavailability.location == location and unavailability.start_time == start_time and \
                    unavailability.end_time_UB == end_time:
                raise ValueError(f"The given unavailability is already among {self.name}'s unavailabilities")
        self._nb_unavailabilities += 1
        unavailability_name = "U" + str(self._nb_unavailabilities)
        self._unavailabilities[unavailability_name] = \
            Unavailability(employee=self, name=unavailability_name, location=location,
                           start_time=start_time, end_time=end_time)

    def get_unavailability_by_name(self, unavailability_name: str) -> Unavailability:
        return self._unavailabilities[unavailability_name]

    def is_capable_of_performing(self, task: Task):
        return self._skill_level >= task.skill_level
