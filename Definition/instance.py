## TODO
## Change addEmployee and addTask to have the field of Employee and Task constructors

###########
# Modules #
###########


# Project modules
from activity import *



##################
# Class Instance #
##################


class Instance:


    name = None
    employees = None
    tasks = None
    activities = None
    lunchBreakStartTime = None
    lunchBreakEndTime = None
    lunchBreakDuration = None
    speed = None


    def __init__(self, name = "EmptyInstance"):
        self.name = name
        self.employees = dict()
        self.tasks = dict()



    #-----------#
    # Employees #
    #-----------#


    # Assumption: employeeName is among employees.keys()
    def getEmployee(self, employeeName):
        return self.employees[employeeName]


    def getEmployees(self):
        return list(self.employees.values())


    def getEmployeesNames(self):
        return list(self.employees.keys())


    def hasEmployee(self, employeeName):
        if employeeName in self.employees.keys():
            return True
        else:
            print(f"{employeeName} is not one of the employees")
            return False


    def addEmployee(self, employee):
        if employee.name in self.employees.keys():
            print(employee + " is already among the employees")
        else:
            self.employees[employee.name] = employee


    def addEmployees(self, employees):
        for employee in employees:
            self.addEmployee(employee)



    #-------#
    # Tasks #
    #-------#


    # Assumption: taskName is among tasks.keys()
    def getTask(self, taskName):
        return self.tasks[taskName]


    def getTasks(self):
        return list(self.tasks.values())


    def getTasksNames(self):
        return list(self.tasks.keys())


    def hasTask(self, taskName):
        if taskName in self.tasks.keys():
            return True
        else:
            print(f"{taskName} is not one of the tasks")
            return False


    def addTask(self, task):
        if task.name in self.tasks.keys():
            print(task.name + " is already among the tasks")
        else:
            self.tasks[task.name] = task


    def addTasks(self, tasks):
        for task in tasks:
            self.addTask(task)



    #-------------#
    # Lunch break #
    #-------------#


    def hasLunchBreaks(self):
        return self.lunchBreakDuration != None


    def setLunchBreakParameters(self, lunchBreakStartTime, lunchBreakEndTime, lunchBreakDuration):
        self.lunchBreakStartTime = lunchBreakStartTime
        self.lunchBreakEndTime = lunchBreakEndTime
        self.lunchBreakDuration = lunchBreakDuration



    #------------#
    # Activities #
    #------------#


    def getActivity(self, activityName, employeeName):
        if self.activities == None:
            self.updateActivities()
        return self.activities[employeeName][activityName]


    def updateActivities(self):
        self.activities = dict()
        for employeeName, employee in self.employees.items():
            employeeActivities = dict()
            employeeActivities['Start'] = Home(employee, start = True)
            for taskName, task in self.tasks.items():
                employeeActivities[taskName] = task
            for unavailabilityName, unavailability in employee.unavailabilities.items():
                employeeActivities[unavailabilityName] = unavailability
            employeeActivities['End'] = Home(employee, start = False)
            self.activities[employeeName] = employeeActivities



    #------------------------#
    # Locations and distance #
    #------------------------#


    def hasGeographicLocations(self):
        return list(self.employees.values())[0].location.isGeographic()


    def computeTravelingDistance(self, activity1: Activity, activity2: Activity):
        return activity1.distanceTo(activity2)


    def computeTravelingDuration(self, activity1: Activity, activity2: Activity):
        return int(np.ceil(activity1.distanceTo(activity2)/self.speed))



    #---------#
    # Display #
    #---------#


    def __repr__(self):
        return self.name
