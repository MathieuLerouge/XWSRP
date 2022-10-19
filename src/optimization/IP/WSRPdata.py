#! /usr/bin/env python3
# coding: utf-8


# Local libraries
from src.modeling.activity import Activity
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.task import Task


# Global variables
LEAVING_HOME_INDEX = 0
COMING_BACK_HOME_INDEX = -1


# Class WSRPIPModelData
class WSRPIPModelData:

    def __init__(self, instance: Instance):

        # Instance
        self._instance = instance

        # Employees
        self._employees = dict()
        self._employees_indices = []
        for i, employee in enumerate(instance.employees):
            self._employees[i + 1] = employee
            self._employees_indices.append(i + 1)

        # Tasks
        self._tasks = dict()
        self._tasks_indices = []
        for j, task in enumerate(instance.tasks):
            self._tasks[j + 1] = task
            self._tasks_indices.append(j + 1)

        # Hypothetical activities
        self._hypothetical_activities = dict()
        self._hypothetical_activities_indices = dict()
        for i in self._employees_indices:
            self._hypothetical_activities[i] = dict()
            self._hypothetical_activities_indices[i] = []

            # Departure
            self._hypothetical_activities[i][LEAVING_HOME_INDEX] = Departure(self._employees[i])
            self._hypothetical_activities_indices[i].append(LEAVING_HOME_INDEX)

            # Tasks
            j = 1
            for task in instance.tasks:
                self._hypothetical_activities[i][j] = task
                self._hypothetical_activities_indices[i].append(j)
                j += 1

            # Unavailabilities
            for unavailability in self._employees[i].unavailabilities:
                self._hypothetical_activities[i][j] = unavailability
                self._hypothetical_activities_indices[i].append(j)
                j += 1

            # Comeback
            self._hypothetical_activities[i][COMING_BACK_HOME_INDEX] = ComeBack(self._employees[i])
            self._hypothetical_activities_indices[i].append(COMING_BACK_HOME_INDEX)

    ############
    # Instance #
    ############

    @property
    def instance(self) -> Instance:
        return self._instance

    #############
    # Employees #
    #############

    @property
    def employees_indices(self):
        return self._employees_indices

    def get_employee_by_index(self, employee_index: int) -> Employee:
        try:
            return self._employees[employee_index]
        except IndexError:
            raise IndexError(f"The given index {employee_index} does not correspond to an employee")

    #########
    # Tasks #
    #########

    @property
    def tasks_indices(self):
        return self._tasks_indices

    def get_task_by_index(self, task_index: int) -> Task:
        try:
            return self._tasks[task_index]
        except IndexError:
            raise IndexError(f"The given index {task_index} does not correspond to a task")

    ###########################
    # Hypothetical activities #
    ###########################

    def get_hyp_activities_indices(self, employee_index: int, including_departure=True,
                                   including_comeback=True, including_unavailabilities=True):
        first_index = 0
        if not including_departure:
            first_index = 1
        second_index = len(self._hypothetical_activities_indices[employee_index]) - 1
        if not including_unavailabilities:
            second_index = len(self._tasks_indices) + 1
        indices = self._hypothetical_activities_indices[employee_index][first_index:second_index]
        if including_comeback:
            indices.append(COMING_BACK_HOME_INDEX)
        return indices

    def get_hyp_activity_by_indices(self, employee_index: int, activity_index: int) -> Activity:
        try:
            return self._hypothetical_activities[employee_index][activity_index]
        except IndexError:
            raise IndexError(f"The given indices {employee_index, activity_index} does not correspond to"
                             "a hypothetical activity")

    def get_hyp_activities_TW_indices(self, employee_index: int, activity_index: int):
        return range(len(self._hypothetical_activities[employee_index][activity_index].TWs))

    def get_traveling_duration(self, employee_index: int, activity_index1: int, activity_index2: int):
        return self._instance.compute_traveling_duration(
            activity1=self.get_hyp_activity_by_indices(employee_index, activity_index1),
            activity2=self.get_hyp_activity_by_indices(employee_index, activity_index2)
            )

    ####################
    # Unavailabilities #
    ####################

    def get_employee_unavailability_by_indices(self, employee_index: int, unavailability_index: int) -> Activity:
        try:
            return self.get_hyp_activity_by_indices(employee_index, unavailability_index)
        except IndexError:
            raise IndexError(f"The given indices {employee_index, unavailability_index} does not correspond to"
                             "a unavailability")

    def get_employee_unavailabilities_indices(self, employee_index: int):
        try:
            first_index = len(self._tasks_indices) + 1
            second_index = len(self._hypothetical_activities_indices[employee_index]) - 1
            return self._hypothetical_activities_indices[employee_index][first_index:second_index]
        except IndexError:
            raise IndexError(f"The given index {employee_index} does not correspond to an employee")
