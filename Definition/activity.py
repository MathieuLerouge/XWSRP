###########
# Modules #
###########


# Project modules
from Tools.integer_set import *
from Tools.location import *



##################
# Class Activity #
##################


class Activity:


    name = None
    employeeName = None
    location = None
    duration = None
    skillLevel = None
    startTime = None
    endTime = None
    availabilityTimeWindows = None


    def isDeparture(self):
        return False


    def isReturn(self):
        return False


    def isTask(self):
        return False


    def isUnavailability(self):
        return self.isEmployeeUnavailability()


    def isEmployeeUnavailability(self):
        return False


    def distanceTo(self, activity):
        return self.location.distanceTo(activity.location)


    def getTypeSymbol(self):
        return "activity"


    # def __hash__(self):
    #     return hash(repr(self))



##############
# Class Task #
##############


class Task(Activity):


    def __init__(self, name, location, duration, skillLevel, startTime, endTime):
        self.name = name
        self.location = location
        self.duration = duration
        self.skillLevel = skillLevel
        self.startTime = startTime
        self.endTime = endTime
        self.availabilityTimeWindows = IntervalUnion(
            interval = IntegerInterval(
                lowerBound = startTime,
                upperBound = endTime
            )
        )


    def __eq__(self, task):
        if isinstance(task, Task) and task.name == self.name:
            return True
        else:
            return False


    def __hash__(self):
        return hash(repr(self))


    def __repr__(self):
        return "Task " + self.name


    def applyUnavailability(self, startTime, endTime):
        self.availabilityTimeWindows = self.availabilityTimeWindows.computeSubstractionBy(
            interval = IntegerInterval(
                lowerBound = startTime,
                upperBound = endTime
            )
        )


    def isTask(self):
        return True


    def getTypeSymbol(self):
        return "task"



##############
# Class Home #
##############


class Home(Activity):


    def __init__(self, employee, start = True):
        if start:
            self.name = "Start"
        else:
            self.name = "End"
        self.employee = employee
        #self.employeeName = employee.name
        self.location = employee.location
        self.duration = 0
        self.startTime = employee.startTime
        self.endTime = employee.endTime
        self.availabilityTimeWindows = IntervalUnion(
            interval = IntegerInterval(
                lowerBound = employee.startTime,
                upperBound = employee.endTime
            )
        )


    def __repr__(self):
        return self.employee.name + "'s " + self.name


    def isDeparture(self):
        if self.name == "Start":
            return True
        else:
            return False


    def isReturn(self):
        return not(self.isDeparture())


    def getEmployee(self):
        return self.employee


    def getTypeSymbol(self):
        if self.isDeparture():
            return "departure"
        else:
            return "return"



########################
# Class Unavailability #
########################


class Unavailability(Activity):


    def __init__(self, employee, name, location, startTime, endTime):
        self.employee = employee
        self.name = name
        self.location = location
        self.duration = endTime - startTime
        self.startTime = startTime
        self.endTime = endTime
        self.availabilityTimeWindows = IntervalUnion(
            interval = IntegerInterval(
                lowerBound = startTime,
                upperBound = endTime
            )
        )


    def __repr__(self):
        return f"{self.employee}'s unavailability {self.name}"


    def isEmployeeUnavailability(self):
        return True


    def getEmployee(self):
        return self.employee


    def getTypeSymbol(self):
        return "unavailability"
