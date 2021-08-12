#! /usr/bin/env python3
# coding: utf-8

# Local libraries
from model.assignedactivity import AssignedActivity
from utils.location import Location


# Class Unavailability
class Unavailability(AssignedActivity):

    def __init__(self, employee, name: str, start_time: int, end_time: int, location: Location):
        super().__init__(employee, name, (end_time - start_time), start_time, end_time, 0, location)
