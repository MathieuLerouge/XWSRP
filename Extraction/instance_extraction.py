###########
# Modules #
###########


# Basic modules
import pandas as pd
import datetime as dt

# Project modules
from Tools.time import *
from Definition.instance import *
from Definition.employee import *
from Definition.activity import *



#############
# Functions #
#############


def extractInstanceFromFile(instanceFilePath, regionName,
    ignoreEmployeesUnavailabilities = False, ignoreTasksUnavailabilities = False):

    # Create an empty instance
    instance = Instance(name = regionName)

    # Extract file's sheet
    instanceData = dict()
    sheetNames = ['Employees', 'Employees Unavailabilities', 'Tasks', 'Tasks Unavailabilities']
    for sheetName in sheetNames:
        instanceData[sheetName] = pd.read_excel(instanceFilePath, sheet_name = sheetName)

    # Read the sheet Employees
    for _, employeeData in instanceData['Employees'].iterrows():
        instance.addEmployee(
            Employee(
                name = employeeData['EmployeeName'],
                location = Location(employeeData['Latitude'], employeeData['Longitude']),
                skillLevel = employeeData['Level'],
                startTime = convert_time_string_to_nb_minutes(employeeData['WorkingStartTime']),
                endTime = convert_time_string_to_nb_minutes(employeeData['WorkingEndTime'])
            )
        )

    # Read the sheet Employees Unavailabilities
    if not(ignoreEmployeesUnavailabilities):
        for _, employeeUnavailabilityData in instanceData['Employees Unavailabilities'].iterrows():
            employeeName = employeeUnavailabilityData['EmployeeName']
            instance.employees[employeeName].addUnavailability(
                location = Location(
                    firstCoordinate = employeeUnavailabilityData['Latitude'],
                    secondCoordinate = employeeUnavailabilityData['Longitude']
                ),
                startTime = convert_time_string_to_nb_minutes(employeeUnavailabilityData['Start']),
                endTime = convert_time_string_to_nb_minutes(employeeUnavailabilityData['End'])
            )

    # Read the sheet Tasks
    for _, taskData in instanceData['Tasks'].iterrows():
        instance.addTask(
            Task(
                name = taskData['TaskId'],
                location = Location(
                    firstCoordinate = taskData['Latitude'],
                    secondCoordinate = taskData['Longitude']
                ),
                duration = int(taskData['TaskDuration']),
                skillLevel = taskData['Level'],
                startTime = convert_time_string_to_nb_minutes(taskData['OpeningTime']),
                endTime = convert_time_string_to_nb_minutes(taskData['ClosingTime'])
            )
        )

    # Read the sheet Tasks Unavailabilities
    if not(ignoreTasksUnavailabilities):
        for _, taskUnavailabilityData in instanceData['Tasks Unavailabilities'].iterrows():
            taskName = taskUnavailabilityData['TaskId']
            instance.tasks[taskName].applyUnavailability(
                startTime = convert_time_string_to_nb_minutes(taskUnavailabilityData['Start']),
                endTime = convert_time_string_to_nb_minutes(taskUnavailabilityData['End'])
            )

    return instance
