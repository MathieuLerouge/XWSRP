###########
# Modules #
###########

# Project modules
from Definition.instance import *
from Definition.activity import *



#####################
# Class IPModelData #
#####################

class IPModelData:

    instance = None
    startIndex = 0
    endIndex = -1
    employees = None
    employeesIndices = None
    tasks = None
    tasksIndices = None
    employeesActivities = None
    employeesActivitiesIndices = None

    def __init__(self, instance, modelType):

        self.instance = instance

        # Employees
        self.employees = dict()
        self.employeesIndices = []
        for i, (name, employee) in enumerate(instance.employees.items()):
            self.employees[i + 1] = employee
            self.employeesIndices.append(i + 1)

        # Tasks
        self.tasks = dict()
        self.tasksIndices = []
        for j, (name, task) in enumerate(instance.tasks.items()):
            self.tasks[j + 1] = task
            self.tasksIndices.append(j + 1)

        # Generalized tasks per employee
        self.employeesActivities = dict()
        self.employeesActivitiesIndices = dict()
        for i in self.employeesIndices:
            self.employeesActivities[i] = dict()
            self.employeesActivitiesIndices[i] = []

            # Starting fake task
            self.employeesActivities[i][self.startIndex] = Home(
                employee = self.employees[i],
                start = True
            )
            self.employeesActivitiesIndices[i].append(self.startIndex)

            # Real tasks and unavailabilities
            j = 1
            for task in instance.tasks.values():
                self.employeesActivities[i][j] = task
                self.employeesActivitiesIndices[i].append(j)
                j += 1
            for unavailability in self.employees[i].unavailabilities.values():
                self.employeesActivities[i][j] = unavailability
                self.employeesActivitiesIndices[i].append(j)
                j += 1

            # Ending fake task
            self.employeesActivities[i][self.endIndex] = Home(
                employee = self.employees[i],
                start = False
            )
            self.employeesActivitiesIndices[i].append(self.endIndex)

    def getEmployeesIndices(self):
        return self.employeesIndices

    def getEmployee(self, employeeIndex):
        return self.employees[employeeIndex]

    def getTasksIndices(self):
        return self.tasksIndices

    def getTask(self, taskIndex):
        return self.tasks[taskIndex]

    def getEmployeeActivity(self, employeeIndex, activityIndex):
        return self.employeesActivities[employeeIndex][activityIndex]

    def getEmployeeUnavailability(self, employeeIndex, unavailabilityIndex):
        if not(unavailabilityIndex in self.getEmployeeUnavailabilitiesIndices(employeeIndex)):
            print(f"Employee {employeeIndex} does not have unavailability {unavailabilityIndex}")
            return None
        else:
            return self.getEmployeeActivity(employeeIndex, unavailabilityIndex)

    def getEmployeeActivitiesIndices(self, employeeIndex,
        includingStart = True, includingEnd = True,
        includingUnavailabilities = True):
        firstIndex = 0
        if not(includingStart):
            firstIndex = 1
        secondIndex = len(self.employeesActivitiesIndices[employeeIndex]) - 1
        if not(includingUnavailabilities):
            secondIndex = len(self.tasksIndices) + 1
        indices = self.employeesActivitiesIndices[employeeIndex][firstIndex:secondIndex]
        if includingEnd:
            indices.append(self.endIndex)
        return indices

    def getEmployeeUnavailabilitiesIndices(self, employeeIndex):
        firstIndex = len(self.tasksIndices) + 1
        secondIndex = len(self.employeesActivitiesIndices[employeeIndex]) - 1
        return self.employeesActivitiesIndices[employeeIndex][firstIndex:secondIndex]

    def getEmployeeTasksAvailabilityTWIndices(self, employeeIndex, activityIndex):
        return range(self.employeesActivities[employeeIndex][activityIndex].availabilityTimeWindows.nbIntervals)

    def getTravelingDuration(self, employeeIndex, activityIndex1, activityIndex2):
        return self.instance.computeTravelingDuration(
            activity1 = self.getEmployeeActivity(employeeIndex = employeeIndex, activityIndex = activityIndex1),
            activity2 = self.getEmployeeActivity(employeeIndex = employeeIndex, activityIndex = activityIndex2)
            )
