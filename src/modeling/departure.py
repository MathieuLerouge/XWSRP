#! /usr/bin/env python3
# coding: utf-8


# Local libraries
from src.modeling.assignedactivity import AssignedActivity
from src.modeling.employee import Employee


# Global variable
LEAVING_HOME_STRING = "Start"


# Class Departure
class Departure(AssignedActivity):

    def __init__(self, employee: Employee):
        super().__init__(employee, LEAVING_HOME_STRING,
                         start_time_lb=employee.start_time_lb, end_time_ub=employee.end_time_ub,
                         location=employee.location)
