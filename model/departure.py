#! /usr/bin/env python3
# coding: utf-8


# Local libraries
from model.assignedactivity import AssignedActivity
from model.employee import Employee


# Global variable
LEAVING_HOME_STRING = "Start"


# Class Departure
class Departure(AssignedActivity):

    def __init__(self, employee: Employee):
        super().__init__(employee, LEAVING_HOME_STRING,
                         start_time_LB=employee.start_time_LB, end_time_UB=employee.end_time_UB,
                         location=employee.location)
