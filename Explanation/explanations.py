# TOBEREMOVED

###########
# Modules #
###########


# Project modules
from Definition.solution import *
from Drawing.comparison_drawer import *
from Drawing.solution_drawer import *
from Optimization.local_change import *



##############################
# Functions - Questions list #
##############################


def getQuestionsTemplates():
    questionsTemplates = []
    questionsTemplates.append("Why employee {0} does not realize task {1} instead of the task {2} in his planning?")
    questionsTemplates.append("Why employee {0} does not realize task {1} just after the activity {2} in his planning?")
    questionsTemplates.append("Why employee {0} does not realize task {1} in addition the tasks of his planning?")
    questionsTemplates.append("Why employee {0} does not realize task {1} in his planning?")
    questionsTemplates.append("Why employee {0} does realize task {1} in his planning?")
    return questionsTemplates




####################
# Functions - Swap #
####################


def answerQuestionAboutReplacing(solution: Solution, employeeName, enteringTaskName, leavingTaskName):

    # Define variables
    employee = solution.instance.employees[employeeName]
    sequence = solution.sequences[employeeName]
    enteringTask = solution.instance.tasks[enteringTaskName]
    leavingTaskIndex = 0
    while leavingTaskIndex < len(sequence) and sequence[leavingTaskIndex].activity.name != leavingTaskName:
        leavingTaskIndex += 1
    if leavingTaskIndex >= len(sequence):
        print(f"{leavingTaskName} is not realized by {employeeName}")
        return False, solution

    # Check skill level
    if employee.skillLevel < enteringTask.skillLevel:
        print(f"{employeeName} does not have enough skills to do {enteringTaskName},")
        print(f"therefore {employeeName} can not do {enteringTaskName} instead of {leavingTaskName}.")
        return False, solution

    # Check start-to-entering-task feasibility
    previousStep = sequence[leavingTaskIndex - 1]
    minStartTimeOfEnteringTask = max(
        previousStep.startTime - previousStep.BTS + previousStep.activity.duration + \
        solution.instance.computeTravelingDuration(previousStep.activity, enteringTask),
        enteringTask.startTime)
    if minStartTimeOfEnteringTask + enteringTask.duration > enteringTask.endTime:
        print(f"Let assume that {enteringTaskName} is put in {employeeName}'s planning instead of {leavingTaskName}.")
        print(f"By realizing the activities from {sequence[0].activity.name} to {previousStep.activity.name} and then {enteringTaskName}, " +
        f"{employeeName} can end {enteringTaskName} at {convert_nb_minutes_to_time_string(minStartTimeOfEnteringTask + enteringTask.duration)} at the earliest, " +
        f"which is later than {convert_nb_minutes_to_time_string(enteringTask.endTime)} when {enteringTaskName} must be realized.")
        print(f"Therefore {employeeName} can not do {enteringTaskName} instead of {leavingTaskName}.")
        return False, solution

    # Check entering-task-to-end feasibility
    nextStep = sequence[leavingTaskIndex + 1]
    minStartTimeOfNextActivity = max(
        minStartTimeOfEnteringTask + enteringTask.duration + solution.instance.computeTravelingDuration(enteringTask, nextStep.activity),
        nextStep.activity.startTime)
    if minStartTimeOfNextActivity > nextStep.startTime + nextStep.FTS:
        print(f"Let assume that {enteringTaskName} is put in {employeeName}'s planning instead of {leavingTaskName}.")
        print(f"By realizing the activities from {sequence[0].activity.name} to {previousStep.activity.name} and then {enteringTaskName}, " +
        f"{employeeName} can start {nextStep.activity.name} at {convert_nb_minutes_to_time_string(minStartTimeOfNextActivity)} at the earliest, " +
        f"which is later than {convert_nb_minutes_to_time_string(nextStep.startTime + nextStep.FTS)}, " +
        f"that is the latest time for starting {nextStep.activity.name} such that {employeeName} is able to " +
              f"realize the activities from {nextStep.activity.name} to {sequence[-1].activity.name}.")
        print(f"Therefore {employeeName} can not do {enteringTaskName} instead of {leavingTaskName}.")
        return False, solution

    # Compute new solution and compare KPIs
    print(f"{employeeName} can do {enteringTaskName} instead of {leavingTaskName}.")
    newSolution = solution.copy()
    newSolution.name = "New solution"
    applyActivitySwap(newSolution, employeeName, leavingTaskIndex, enteringTask, startTime = minStartTimeOfEnteringTask)
    newSolution.computeTimeSlacks()
    drawComparisonBetweenSolutions(solution1 = solution, solution2 = newSolution)
    showFigures(blockComputation = False)
    if promptYesNoQuestion("Do you want to go with the new solution?"):
        return True, newSolution
    return False, solution



#########################
# Functions - Insertion #
#########################


def answerQuestionAboutInserting(solution: Solution, employeeName, enteringTaskName, beforeInsertionActivityName):

    # Define variables
    employee = solution.instance.employees[employeeName]
    sequence = solution.sequences[employeeName]
    enteringTask = solution.instance.tasks[enteringTaskName]
    beforeInsertionActivityIndex = 0
    while beforeInsertionActivityIndex < len(sequence) and sequence[beforeInsertionActivityIndex].activity.name != beforeInsertionActivityName:
        beforeInsertionActivityIndex += 1
    if beforeInsertionActivityIndex >= len(sequence):
        print(f"{beforeInsertionActivityIndex} is not realized by {employeeName}")
        return False, solution
    afterInsertionActivityIndex = beforeInsertionActivityIndex + 1
    afterInsertionActivityName = sequence[afterInsertionActivityIndex].activity.name

    # Check skill level
    if employee.skillLevel < enteringTask.skillLevel:
        print(f"{employeeName} does not have enough skills to do {enteringTaskName},")
        print(f"therefore {employeeName} can not do {enteringTaskName} instead of {leavingTaskName}.")
        return False, solution

    # Check start-to-entering-task feasibility
    previousStep = sequence[beforeInsertionActivityIndex]
    minStartTimeOfEnteringTask = max(
        previousStep.startTime - previousStep.BTS + previousStep.activity.duration + \
        solution.instance.computeTravelingDuration(previousStep.activity, enteringTask),
        enteringTask.startTime)
    if minStartTimeOfEnteringTask + enteringTask.duration > enteringTask.endTime:
        print(f"Let assume that {enteringTaskName} is inserted in {employeeName}'s planning just after {beforeInsertionActivityName}.")
        print(f"{employeeName} can end {enteringTaskName} at {convert_nb_minutes_to_time_string(minStartTimeOfEnteringTask + enteringTask.duration)} at the earliest " +
        f"while {enteringTaskName} must be ended by {convert_nb_minutes_to_time_string(enteringTask.endTime)}.")
        print(f"Therefore {employeeName} can not do {enteringTaskName} just after {beforeInsertionActivityName}.")
        return False, solution

    # Check entering-task-to-end feasibility
    nextStep = sequence[afterInsertionActivityIndex]
    minStartTimeOfNextActivity = max(
        minStartTimeOfEnteringTask + enteringTask.duration + solution.instance.computeTravelingDuration(enteringTask, nextStep.activity),
        nextStep.activity.startTime)
    if minStartTimeOfNextActivity > nextStep.startTime + nextStep.FTS:
        print(f"Let assume that {enteringTaskName} is put in {employeeName}'s planning just after {beforeInsertionActivityName}.")
        print(f"{employeeName} can start {nextStep.activity.name} at {convert_nb_minutes_to_time_string(minStartTimeOfNextActivity)} at the earliest, " +
        f"while {nextStep.activity.name} must be started at {convert_nb_minutes_to_time_string(nextStep.startTime + nextStep.FTS)} at the latest " +
        f"to allow {employeeName} to realize {nextStep.activity.name} and the following activities.")
        print(f"Therefore {employeeName} can not do {enteringTaskName} just after {beforeInsertionActivityName}.")
        return False, solution

    # Compute new solution and compare KPIs
    print(f"{employeeName} can do {enteringTaskName} between {beforeInsertionActivityName} and {afterInsertionActivityName}.")
    newSolution = solution.copy()
    newSolution.name = "New solution"
    applyActivityInsertion(newSolution, employeeName, beforeInsertionActivityIndex, enteringTask, startTime = minStartTimeOfEnteringTask)
    newSolution.computeTimeSlacks()
    drawComparisonBetweenSolutions(solution1 = solution, solution2 = newSolution)
    showFigures(blockComputation = False)
    if promptYesNoQuestion("Do you want to go with the new solution?"):
        return True, newSolution
    return False, solution



def answerQuestionAboutInsertingInAddition(solution: Solution, employeeName, enteringTaskName):

    # Define variables
    employee = solution.instance.employees[employeeName]
    sequence = solution.sequences[employeeName]
    enteringTask = solution.instance.tasks[enteringTaskName]

    # Check skill level
    if employee.skillLevel < enteringTask.skillLevel:
        print(f"{employeeName} does not have enough skills to do {enteringTaskName},")
        print(f"therefore {employeeName} can not do {enteringTaskName} instead of {leavingTaskName}.")
        return False, solution

    # Find best insertion
    durationDetour, bestInsertionIndex, minStartTimeOfEnteringTask = findBestTaskInsertion(solution, employeeName, enteringTask)

    if durationDetour == None:

        # Check feasibility of going directly to the task
        if bestInsertionIndex == None:
            print(f"Let assume that {enteringTaskName} is inserted at the very beginning of {employeeName}'s planning.")
            print(f"{employeeName} can end {enteringTaskName} at {convert_nb_minutes_to_time_string(minStartTimeOfEnteringTask + enteringTask.duration)} at the earliest, " +
            f"while {enteringTaskName} must be ended at {convert_nb_minutes_to_time_string(enteringTask.endTime)}.")
            print(f"Inserting {enteringTaskName} later in {employeeName}'s planning can only make it worst.")
            print(f"Therefore {employeeName} can not do {enteringTaskName} in addition to the tasks of his planning.")
            return False, solution

        # Check feasibility of any insertion
        else:
            beforeInsertionStep = sequence[bestInsertionIndex]
            afterInsertionStep = sequence[bestInsertionIndex + 1]
            minStartTimeOfNextActivity = max(afterInsertionStep.activity.startTime,
                minStartTimeOfEnteringTask + enteringTask.duration + solution.instance.computeTravelingDuration(enteringTask, afterInsertionStep.activity))
            print(f"All insertion of {enteringTaskName} in {employeeName}'s planning have been tested and none of them are feasible.")
            print(f"For instance, let assume that {enteringTaskName} is inserted in {employeeName}'s planning between {beforeInsertionStep.activity.name} and {afterInsertionStep.activity.name}.")
            print(f"{employeeName} can start {afterInsertionStep.activity.name} at {convert_nb_minutes_to_time_string(minStartTimeOfNextActivity)} at the earliest, " +
            f"while {afterInsertionStep.activity.name} must be started at {convert_nb_minutes_to_time_string(afterInsertionStep.startTime + afterInsertionStep.FTS)} at the latest " +
            f"to allow {employeeName} to realize {afterInsertionStep.activity.name} and the following activities.")
            print(f"Therefore {employeeName} can not do {enteringTaskName} in addition to the tasks of his planning.")
            return False, solution

    # Compute new solution and compare KPIs
    else:
        activityNameBefore = sequence[bestInsertionIndex].activity.name
        print(f"{employeeName} can do {enteringTaskName} in addition to the tasks of his planning by inserting it after {activityNameBefore}.")
        newSolution = solution.copy()
        newSolution.name = "New solution"
        applyActivityInsertion(newSolution, employeeName, bestInsertionIndex, enteringTask, startTime = minStartTimeOfEnteringTask)
        newSolution.computeTimeSlacks()
        drawComparisonBetweenSolutions(solution1 = solution, solution2 = newSolution)
        showFigures(blockComputation = False)
        if promptYesNoQuestion("Do you want to go with the new solution?"):
            return True, newSolution
        return False, solution



def answerQuestionAboutInsertingAtAllCosts(solution: Solution, employeeName, enteringTaskName):

    print("Not yet code")
    return False, solution



########################
# Functions - Terminal #
########################


def promptYesNoQuestion(question):
    print(f"XPer: {question} [Y/N]")
    answer = input("XPee: ")
    if answer in ["Y", "y", "Yes", "yes"]:
        return True
    elif answer in ["N", "n", "No", "no"]:
        return False
    else:
        print("XPer: You gave an incorrect answer, please use Y for yes or N for no")
        print("")
        return promptYesNoQuestion(question)


def checkIfUserHasAnyQuestion():
    return promptYesNoQuestion("Do you have any questions?")


def findOutAndAnswerUserQuestion(solution: Solution):

    tabulation = "      "
    print("XPer: Which question do you want to ask among the following? [Give the number corresponding to your question] ")
    print(tabulation + "1. Why employee _ does not realize task _ instead of the task _ in his planning?")
    print(tabulation + "2.1. Why employee _ does not realize task _ just after the activity _ in his planning?")
    print(tabulation + "2.2. Why employee _ does not realize task _ in addition the tasks of his planning?")

    try:
        answer = float(input("XPee: "))

        if np.any(np.isin(answer, [1, 2.1, 2.2, 2.3], assume_unique = True)):
            print("XPer: Then please fill the following data")
            employeeName = input(tabulation + "- Employee's name: ")
            if not(solution.instance.hasEmployee(employeeName)):
                return False, solution
            enteringTaskName = input(tabulation + "- Non-realized entering task's name: ")
            if not(solution.instance.hasTask(enteringTaskName)):
                return False, solution
            if answer == 1:
                leavingTaskName = input(tabulation + "- Realized leaving task's name: ")
                if not(solution.instance.hasTask(leavingTaskName)):
                    return False, solution
                print("")
                return answerQuestionAboutReplacing(solution, employeeName, enteringTaskName, leavingTaskName)
            elif answer == 2.1:
                beforeInsertionActivityName = input(tabulation + "- Activity's name before insertion: ")
                print("")
                return answerQuestionAboutInserting(solution, employeeName, enteringTaskName, beforeInsertionActivityName)
            elif answer == 2.2:
                print("")
                return answerQuestionAboutInsertingInAddition(solution, employeeName, enteringTaskName)
            elif answer == 2.3:
                print("")
                return answerQuestionAboutInsertingByForce(solution, employeeName, enteringTaskName)

        else:
            print("XPer: You gave an incorrect number")
            return False, solution

    except ValueError:
        print("XPer: You did not give a number")
        return False, solution
