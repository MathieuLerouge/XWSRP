###########
# Modules #
###########

# Project modules
from Definition.solution import *
from Tools.time import *



#############
# Functions #
#############


def checkCoveringConstraints(solution):

    satisfaction = True

    nonRealizedTasksNames = [
        taskName for taskName in solution.tasksDescriptions.keys()
            if not(solution.tasksDescriptions[taskName]['realized'])
    ]
    if len(nonRealizedTasksNames) > 0:
        satisfaction = False
        for taskName in nonRealizedTasksNames:
            print(f"According to the given plan, the task {taskName} is not realized")

    return satisfaction


def checkTimeWindowsConstraints(solution):

    satisfaction = True

    # Check that tasks are realized within availability time windows
    for taskName, taskDescription in solution.tasksDescriptions.items():
        task = solution.instance.tasks[taskName]
        if taskDescription['realized']:
            startTime = taskDescription['startTime']
            endTime = startTime + task.duration
            # - Task
            taskAvailableWhenRealized = False
            for availabilityTimeWindow in task.availabilityTimeWindows.intervals:
                if availabilityTimeWindow.containsAll([startTime, endTime]):
                    taskAvailableWhenRealized = True
                    break
            if not(taskAvailableWhenRealized):
                satisfaction = False
                print(f"According to the given plan, the task {taskName} is supposed to " +
                    f"be realized over [{convert_nb_minutes_to_time_string(startTime)};{convert_nb_minutes_to_time_string(endTime)}] " +
                    f"while it is actually available over {task.availabilityTimeWindows.toTimeString()}")
            # - Employee
            employee = solution.instance.employees[taskDescription["employeeName"]]
            if startTime < employee.startTime:
                satisfaction = False
                print(f"According to the given plan, the task {taskName} is supposed to " +
                    f"be realized over [{convert_nb_minutes_to_time_string(startTime)};{convert_nb_minutes_to_time_string(endTime)}] " +
                    f"by employee {employee.name} " +
                    f"while he/she actually starts working at {convert_nb_minutes_to_time_string(employee.startTime)}")
            if employee.endTime < endTime:
                satisfaction = False
                print(f"According to the given plan, the task {taskName} is supposed to " +
                    f"be realized over [{convert_nb_minutes_to_time_string(startTime)};{convert_nb_minutes_to_time_string(endTime)}] " +
                    f"by employee {employee.name} " +
                    f"while he/she actually ends working at {convert_nb_minutes_to_time_string(employee.endTime)}")
            for unavailabilityName, unavailability in employee.unavailabilities.items():
                if unavailability.availabilityTimeWindows[0].contains(startTime) or \
                    unavailability.availabilityTimeWindows[0].contains(endTime):
                    satisfaction = False
                    print(f"According to the given plan, the task {taskName} is supposed to " +
                        f"be realized over [{convert_nb_minutes_to_time_string(startTime)};{convert_nb_minutes_to_time_string(endTime)}] by employee {employee.name} " +
                        f"while he/she is actually unavailable over {unavailability.availabilityTimeWindows[0].toTimeString()} " +
                          f"due to his/her unavailability {unavailabilityName}")

    # Check that lunch breaks are taken within dedicated time windows
    if solution.instance.hasLunchBreaks():
        for employeeName, employee in solution.instance.employees.items():
            lunchBreakStartTime = solution.lunchBreaksDescriptions[employeeName]['startTime']
            lunchBreakEndTime = lunchBreakStartTime + solution.instance.lunchBreakDuration
            if lunchBreakStartTime < solution.instance.lunchBreakStartTime or \
                solution.instance.lunchBreakEndTime < lunchBreakEndTime:
                satisfaction = False
                print(f"According to the given plan, {str(employee)} is supposed to " +
                    f"take a lunch break over [{convert_nb_minutes_to_time_string(lunchBreakStartTime)};{convert_nb_minutes_to_time_string(lunchBreakEndTime)}] " +
                    f"while lunch break must actually be within " +
                    f"[{convert_nb_minutes_to_time_string(solution.instance.lunchBreakStartTime)};{convert_nb_minutes_to_time_string(solution.instance.lunchBreakEndTime)}]")

    return satisfaction


def checkSequenceConstraints(solution, toleranceInMinutes = 0):

    satisfaction = True

    for employeeName, sequence in solution.sequences.items():

        if len(sequence) > 2:

            employee = solution.instance.employees[employeeName]

            # Check start-to-first-step sequence (if first step is a task)
            firstStep = sequence[1]
            if firstStep.activity.isTask():
                if sequence[0].startTime < employee.startTime - toleranceInMinutes:
                    satisfaction = False
                    print(f"According to the given plan, {str(employee)} is supposed to " +
                        f"do the task {firstStep.activity.name} at {convert_nb_minutes_to_time_string(firstStep.startTime)} " +
                        f"therefore, {employeeName} is supposed to leave its initial location at " +
                        f"{convert_nb_minutes_to_time_string(sequence[0].startTime)} " +
                        f"but he/she actually starts to work not before {convert_nb_minutes_to_time_string(employee.startTime)}")

            # Check step-to-step sequence (including unavailabilities)
            for previousStepIndex, step in enumerate(sequence[1: -1]):
                if step.arrivalTime > step.startTime + toleranceInMinutes:
                    satisfaction = False
                    previousStep = sequence[previousStepIndex]
                    if solution.instance.hasLunchBreaks() and solution.lunchBreaksDescriptions[employeeName]['taskAfter'] == step.activity.name:
                        print(f"According to the given plan, {str(employee)} is supposed to " +
                            f"do {str(previousStep.activity)} at {convert_nb_minutes_to_time_string(previousStep.startTime)}, " +
                            f"then take a lunch break and then do {str(step.activity)} at {convert_nb_minutes_to_time_string(step.startTime)} " +
                            f"therefore, {employeeName} is supposed to travel from {previousStep.activity.name} to {step.activity.name} " +
                              f"in less than {step.startTime - previousStep.endTime - solution.instance.lunchBreakDuration} min " +
                              f"but it actually takes {solution.computeTravelingDuration(previousStep, step)} min")
                    else:
                        print(f"According to the given plan, {str(employee)} is supposed to " +
                            f"do {str(previousStep.activity)} at {convert_nb_minutes_to_time_string(previousStep.startTime)} " +
                            f"and then do {str(step.activity)} at {convert_nb_minutes_to_time_string(step.startTime)} " +
                            f"therefore, {employeeName} is supposed to travel from {previousStep.activity.name} to {step.activity.name} " +
                              f"in less than {step.startTime - previousStep.endTime} min " +
                              f"but it actually takes {solution.computeTravelingDuration(previousStep, step)} min")

            # Check last-step-to-end sequence (if last step is a task)
            lastStep = sequence[-2]
            if lastStep.activity.isTask():
                if sequence[-1].arrivalTime > employee.endTime + toleranceInMinutes:
                    satisfaction = False
                    print(f"According to the given plan, {str(employee)} is supposed to " +
                        f"do {str(lastStep.activity)} at {convert_nb_minutes_to_time_string(lastStep.startTime)} "
                        f"and then go at his/her final location, "
                        f"therefore {employeeName} is supposed to be at his/her final location at " +
                        f"{convert_nb_minutes_to_time_string(sequence[-1].arrivalTime)} " +
                        f"but {employeeName} actually ends to work at {convert_nb_minutes_to_time_string(employee.endTime)}")

    return satisfaction


def checkSkillConstraints(solution):
    satisfaction = True
    for taskName, taskDescription in solution.tasksDescriptions.items():
        if taskDescription['realized']:
            employee = solution.instance.employees[taskDescription["employeeName"]]
            task = solution.instance.tasks[taskName]
            if employee.skillLevel < task.skillLevel:
                satisfaction = False
                print(f"According to the given plan, {str(employee)} is supposed to " +
                    f"do task {task.name}, which has a skill level equal to {task.skillLevel}, " + \
                    f"but he/she has a skill level which is equal to {employee.skillLevel}")
    return satisfaction


def checkFeasibility(solution, covering = False, timeWindows = True, sequence = True, skill = True, toleranceInMinutes = 0):
    if (not(covering) or checkCoveringConstraints(solution)) & \
        (not(timeWindows) or checkTimeWindowsConstraints(solution)) & \
        (not(sequence) or checkSequenceConstraints(solution, toleranceInMinutes)) & \
        (not(skill) or checkSkillConstraints(solution)):
        return True
    else:
        return False
