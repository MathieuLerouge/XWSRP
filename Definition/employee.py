###########
# Modules #
###########


# Project modules
from activity import *


##################
# Class Employee #
##################


class Employee:

    name = None
    location = None
    skillLevel = None
    startTime = None
    endTime = None
    nbUnavailabilities = None
    unavailabilities = None

    def __init__(self, name, location, skillLevel, startTime, endTime):
        self.name = name
        self.location = location
        self.skillLevel = skillLevel
        self.startTime = startTime
        self.endTime = endTime
        self.nbUnavailabilities = 0
        self.unavailabilities = dict()

    def __eq__(self, employee):
        return self.name == employee.name

    def __repr__(self):
        return "Employee " + self.name

    def addUnavailability(self, location, startTime, endTime):
        alreadyInUnavailabilitiesIndicator = False
        for unavailability in self.unavailabilities:
            if unavailability.location == location and \
                    unavailability.startTime == startTime and \
                    unavailability.endTime == endTime:
                alreadyInUnavailabilitiesIndicator = True
                print("Given unavailability is already among the unavailabilities of " + self.name)
        if not (alreadyInUnavailabilitiesIndicator):
            self.nbUnavailabilities += 1
            unavailabilityName = "U" + str(self.nbUnavailabilities)
            self.unavailabilities[unavailabilityName] = \
                Unavailability(
                    employee=self,
                    name=unavailabilityName,
                    location=location,
                    startTime=startTime,
                    endTime=endTime
                )

    def getUnavailability(self, unavailabilityName):
        return self.unavailabilities[unavailabilityName]

    def getUnavailabilities(self):
        return self.unavailabilities.values()
