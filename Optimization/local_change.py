# TODO: migrate to solutionForLS

###########
# Modules #
###########


# Project modules
from Definition.solution import *
from Optimization.solution_for_LS import *



######################
# Functions - Common #
######################


# Assumption: task is set to be realized
# and is about to be removed from employee sequence
def unrealizeTask(solution: SolutionForLS, task):
    print("unrealizeTask() is deprecated, use SolutionForLS._setTaskDescToNonrealized()")
    solution._setTaskDescToNonrealized(task)
    # taskDescription = solution.tasksDescriptions[task.name]
    # taskDescription['realized'] = False
    # del taskDescription['employeeName']
    # del taskDescription['startTime']



######################
# Functions - Remove #
######################


# Assumption: solution.sequences[employeeName][stepToRemoveIndex] is a task
def removeStepFromEmployeePlanning(solution: SolutionForLS, employeeName, stepIndex, updateTimes = True, updateTS = True, updateKPIs = True):
    print("removeTaskFromEmployeePlanning() is deprecated, use SolutionForLS.removeTaskFromEmployeePlanning()")
    solution.removeStepFromEmployeePlanning(employeeName, stepIndex, updateTimes, updateTS, updateKPIs)
    # # Define sequence
    # sequence = solution.sequences[employeeName]
    #
    # # Save former sequence's KPIs (if needed)
    # formerTotalTravelingDuration, formerTotalTravelingDistance, formerTotalIdleTime = None, None, None
    # if updateKPIs:
    #     formerTotalTravelingDuration, formerTotalTravelingDistance, formerTotalIdleTime = solution.computeSequenceKPIs(sequence)
    #
    # # Remove step from sequence and corresponding task from realized tasks
    # removedStep = sequence.pop(stepToRemoveIndex)
    # removedTask = removedStep.activity
    # unrealizeTask(solution, removedTask)
    # removedStep.clear()
    #
    # # Update times around the deletion (if needed)
    # if updateTimes:
    #     stepBeforeRemoval = sequence[stepToRemoveIndex - 1]
    #     stepAfterRemoval = sequence[stepToRemoveIndex]
    #     stepAfterRemoval.arrivalTime = stepBeforeRemoval.endTime + solution.computeTravelingDuration(stepBeforeRemoval, stepAfterRemoval)
    #
    # # Update time slacks (if needed)
    # if updateTS:
    #     # BTS of steps from sequence[0] (included) to sequence[stepBeforeRemovalIndex] (included) are correct
    #     # BTS of steps following sequence[stepAfterRemovalIndex] (included) must be updated
    #     solution.propagateBTSForwardFrom(employeeName, stepIndex = stepToRemoveIndex)
    #     # FTS of steps from sequence[-1] (included) to sequence[stepAfterRemovalIndex] (included) are correct
    #     # FTS of steps preceding sequence[stepBeforeRemovalIndex] (included) must be updated
    #     solution.propagateFTSBackwardFrom(employeeName, stepIndex = stepToRemoveIndex - 1)
    #
    # # Update KPIs (if needed)
    # if updateKPIs:
    #     solution.KPIs['nbRealizedTasks'] -= 1
    #     solution.KPIs['totalWorkingDuration'] -= removedTask.duration
    #     newTotalTravelingDuration, newTotalTravelingDistance, newTotalIdleTime = solution.computeSequenceKPIs(sequence)
    #     solution.KPIs['totalTravelingDuration'] += newTotalTravelingDuration - formerTotalTravelingDuration
    #     solution.KPIs['totalTravelingDistance'] += newTotalTravelingDistance - formerTotalTravelingDistance
    #     solution.KPIs['totalIdleTime'] += newTotalIdleTime - formerTotalIdleTime



####################
# Functions - Swap #
####################


# Assumption: solution.sequences[employeeName][leavingStepIndex] is a task
def applyActivitySwap(solution: SolutionForLS, employeeName, leavingStepIndex, enteringTask: Task, startTime):
    print("Deprecated: applyActivitySwap is deprecated, use Solution.replaceTaskByAnotherAt()")
    solution.replaceTaskByAnotherAt(employeeName, solution.sequences[employeeName][leavingStepIndex].activity, enteringTask, startTime, updateKPIs = True)

    # # Remove entering activity from planning if already realized
    # enteringTaskDescription = solution.tasksDescriptions[enteringTask.name]
    # if enteringTaskDescription['realized']:
    #     stepIndex = solution.getActivityIndexInEmployeeSequence(enteringTaskDescription['employeeName'], enteringTask.name)
    #     removeStepFromEmployeePlanning(solution, enteringTaskDescription['employeeName'], stepIndex)
    #
    # # Save information about former sequence
    # sequence = solution.sequences[employeeName]
    # formerTotalTravelingDuration, formerTotalTravelingDistance, formerTotalIdleTime = solution.computeSequenceKPIs(sequence)
    # step = sequence[leavingStepIndex]
    # leavingTask = step.activity
    #
    # # Swap leaving and entering activities
    # step.clear()
    # step.set(activity = enteringTask, startTime = startTime, endTime = startTime + enteringTask.duration)
    #
    # # Update times before swap (upstream)
    # previousStep = sequence[leavingStepIndex - 1]
    # travelingDurationFromPreviousStep = solution.computeTravelingDuration(previousStep, step)
    # previousStartTime = startTime - (travelingDurationFromPreviousStep + previousStep.activity.duration)
    # if previousStartTime < previousStep.startTime:
    #     sequence.shiftTimesBackwardFrom(stepIndex = leavingStepIndex - 1, startTime = previousStartTime, tasksDescs = solution.tasksDescriptions)
    #     step.arrivalTime = startTime
    # else:
    #     step.arrivalTime = previousStep.endTime + travelingDurationFromPreviousStep
    #
    # # Update times after swap (downstream)
    # nextStep = sequence[leavingStepIndex + 1]
    # travelingDurationToNextStep = solution.computeTravelingDuration(step, nextStep)
    # nextArrivalTime = step.endTime + travelingDurationToNextStep
    # nextStep.arrivalTime = nextArrivalTime
    # if nextStep.startTime < nextArrivalTime:
    #     solution.updateTimesDownstream(employeeName, stepIndex = leavingStepIndex + 1, startTime = nextArrivalTime)
    #
    # # Update time slacks
    # sequence.updateBTSForwardFrom(leavingStepIndex)
    # sequence.updateFTSBackwardFrom(leavingStepIndex)
    #
    # # Update tasks' realization
    # unrealizeTask(solution, leavingTask)
    # enteringTaskDescription = solution.tasksDescriptions[enteringTask.name]
    # enteringTaskDescription['realized'] = True
    # enteringTaskDescription['employeeName'] = employeeName
    # enteringTaskDescription['startTime'] = startTime
    #
    # # Update KPIs
    # # solution.KPIs['nbRealizedTasks'] does not change
    # solution.KPIs['totalWorkingDuration'] += enteringTask.duration - leavingTask.duration
    # newTotalTravelingDuration, newTotalTravelingDistance, newTotalIdleTime = solution.computeSequenceKPIs(sequence)
    # solution.KPIs['totalTravelingDuration'] += newTotalTravelingDuration - formerTotalTravelingDuration
    # solution.KPIs['totalTravelingDistance'] += newTotalTravelingDistance - formerTotalTravelingDistance
    # solution.KPIs['totalIdleTime'] += newTotalIdleTime - formerTotalIdleTime



#########################
# Functions - Insertion #
#########################


def findBestTaskInsertion(solution:Solution, employeeName, enteringTask):
    print("Deprecated: findBestTaskInsertion is deprecated, use SolutionForLS.insertTaskAfterActivity()")

    # insertionIndex = 0
    # bestInsertionIndex = None
    # bestStartTimeOfEnteringTask = None
    # bestDurationDetour = None
    # bestLate = None
    #
    # sequence = solution.sequences[employeeName]
    #
    # while insertionIndex < len(sequence) - 1:
    #     stepBefore = sequence[insertionIndex]
    #     travelingDurationFromStepBefore = solution.instance.computeTravelingDuration(stepBefore.activity, enteringTask)
    #     startTimeOfEnteringTask = max(stepBefore.activity.startTime,
    #         stepBefore.startTime - stepBefore.BTS + stepBefore.activity.duration + travelingDurationFromStepBefore)
    #
    #     if startTimeOfEnteringTask + enteringTask.duration <= enteringTask.endTime:
    #         stepAfter = sequence[insertionIndex + 1]
    #         travelingDurationToStepAfter = solution.instance.computeTravelingDuration(enteringTask, stepAfter.activity)
    #         startTimeOfNextStep = max(stepAfter.activity.startTime,
    #             startTimeOfEnteringTask + enteringTask.duration + travelingDurationToStepAfter)
    #
    #         if startTimeOfNextStep <= stepAfter.startTime + stepAfter.FTS:
    #             durationDetour = travelingDurationFromStepBefore + travelingDurationToStepAfter -\
    #                 solution.computeTravelingDuration(stepBefore, stepAfter)
    #             if bestDurationDetour == None or durationDetour < bestDurationDetour:
    #                 bestDurationDetour = durationDetour
    #                 bestInsertionIndex = insertionIndex
    #                 bestStartTimeOfEnteringTask = startTimeOfEnteringTask
    #
    #         else:
    #             late = startTimeOfNextStep - stepAfter.startTime - stepAfter.FTS
    #             if bestLate == None or late < bestLate:
    #                 bestLate = late
    #                 bestInsertionIndex = insertionIndex
    #                 bestStartTimeOfEnteringTask = startTimeOfEnteringTask
    #
    #         insertionIndex += 1
    #
    #     else:
    #         insertionIndex = len(sequence)
    #
    # return bestDurationDetour, bestInsertionIndex, bestStartTimeOfEnteringTask


# Assumption: beforeInsertionActivityIndex is in [0; len(solution.sequences[employeeName]) - 2]
def applyActivityInsertion(solution: Solution, employeeName, beforeInsertionActivityIndex, enteringTask: Task, startTime):
    print("Deprecated: applyActivityInsertion() is deprecated, use SolutionForLS.insertTaskAfterActivity()")

    # # Remove entering activity from planning if already realized
    # enteringTaskDescription = solution.tasksDescriptions[enteringTask.name]
    # if enteringTaskDescription['realized']:
    #     enteringStepIndex = solution.getActivityIndexInEmployeeSequence(enteringTaskDescription['employeeName'], enteringTask.name)
    #     removeTaskFromEmployeePlanning(solution, enteringTaskDescription['employeeName'], enteringStepIndex)
    #
    # # Store information about former sequence
    # sequence = solution.sequences[employeeName]
    # formerTotalTravelingDuration, formerTotalTravelingDistance, formerTotalIdleTime = solution.computeSequenceKPIs(sequence)
    #
    # # Create new step
    # step = Step(activity = enteringTask, startTime = startTime, endTime = startTime + enteringTask.duration)
    # sequence.insert(beforeInsertionActivityIndex + 1, step)
    # enteringActivityIndex = beforeInsertionActivityIndex + 1
    # afterInsertionActivityIndex = enteringActivityIndex + 1
    #
    # # Update times before insertion (upstream)
    # previousStep = sequence[beforeInsertionActivityIndex]
    # travelingDurationFromPreviousStep = solution.computeTravelingDuration(previousStep, step)
    # previousStartTime = startTime - (travelingDurationFromPreviousStep + previousStep.activity.duration)
    # if previousStartTime < previousStep.startTime:
    #     sequence.shiftTimesBackwardFrom(stepIndex = beforeInsertionActivityIndex, startTime = previousStartTime, tasksDescs = solution.tasksDescriptions)
    #     step.arrivalTime = startTime
    # else:
    #     step.arrivalTime = previousStep.endTime + travelingDurationFromPreviousStep
    #
    # # Update times after insertion (downstream)
    # nextStep = sequence[afterInsertionActivityIndex]
    # travelingDurationToNextStep = solution.computeTravelingDuration(step, nextStep)
    # nextArrivalTime = step.endTime + travelingDurationToNextStep
    # nextStep.arrivalTime = nextArrivalTime
    # if nextStep.startTime < nextArrivalTime:
    #     #solution.updateTimesDownstream(employeeName, stepIndex = afterInsertionActivityIndex, startTime = nextArrivalTime)
    #     sequence.shiftTimesForwardFrom(stepIndex = afterInsertionActivityIndex, startTime = nextArrivalTime, tasksDescs = solution.tasksDescriptions)
    #
    # # Update time slacks
    # # solution.propagateBTSForwardFrom(employeeName, stepIndex = enteringActivityIndex)
    # # solution.propagateFTSBackwardFrom(employeeName, stepIndex = enteringActivityIndex)
    # sequence.updateBTSForwardFrom(enteringActivityIndex)
    # sequence.updateFTSBackwardFrom(enteringActivityIndex)
    #
    # # Update tasks' realization
    # enteringTaskDescription = solution.tasksDescriptions[enteringTask.name]
    # enteringTaskDescription['realized'] = True
    # enteringTaskDescription['employeeName'] = employeeName
    # enteringTaskDescription['startTime'] = startTime
    #
    # # Update KPIs
    # solution.KPIs['nbRealizedTasks'] += 1
    # solution.KPIs['totalWorkingDuration'] += enteringTask.duration
    # newTotalTravelingDuration, newTotalTravelingDistance, newTotalIdleTime = solution.computeSequenceKPIs(sequence)
    # solution.KPIs['totalTravelingDuration'] += newTotalTravelingDuration - formerTotalTravelingDuration
    # solution.KPIs['totalTravelingDistance'] += newTotalTravelingDistance - formerTotalTravelingDistance
    # solution.KPIs['totalIdleTime'] += newTotalIdleTime - formerTotalIdleTime
    #
    # return solution


def applyActivityInfeasibleInsertion(solution: Solution, employeeName, beforeInsertionActivityIndex, enteringTask: Task, startTimeForUpstream, startTimeForDownstream):
    print("Deprecated: applyActivityInfeasibleInsertion() is deprecated, use SolutionForLS.insertTaskAfterActivity()")

    # # Remove entering activity from planning if already realized
    # enteringTaskDescription = solution.tasksDescriptions[enteringTask.name]
    # if enteringTaskDescription['realized']:
    #     enteringStepIndex = solution.getActivityIndexInEmployeeSequence(enteringTaskDescription['employeeName'], enteringTask.name)
    #     removeTaskFromEmployeePlanning(solution, enteringTaskDescription['employeeName'], enteringStepIndex)
    #
    # # Store information about former sequence
    # sequence = solution.sequences[employeeName]
    # #formerTotalTravelingDuration, formerTotalTravelingDistance, formerTotalIdleTime = solution.computeSequenceKPIs(sequence)
    #
    # # Create new step
    # meanStartTime = (startTimeForDownstream + startTimeForUpstream) // 2
    # step = Step(activity = enteringTask, startTime = meanStartTime, endTime = meanStartTime + enteringTask.duration)
    # sequence.insert(beforeInsertionActivityIndex + 1, step)
    # enteringActivityIndex = beforeInsertionActivityIndex + 1
    # afterInsertionActivityIndex = enteringActivityIndex + 1
    #
    # # Update times before insertion (upstream)
    # previousStep = sequence[beforeInsertionActivityIndex]
    # travelingDurationFromPreviousStep = solution.computeTravelingDuration(previousStep, step)
    # previousStartTime = startTimeForUpstream - (travelingDurationFromPreviousStep + previousStep.activity.duration)
    # if previousStartTime < previousStep.startTime:
    #     sequence.shiftTimesBackwardFrom(stepIndex = beforeInsertionActivityIndex, startTime = previousStartTime, tasksDescs = solution.tasksDescriptions)
    #     step.arrivalTime = startTimeForUpstream
    # else:
    #     step.arrivalTime = previousStep.endTime + travelingDurationFromPreviousStep
    #
    # # Update times after insertion (downstream)
    # nextStep = sequence[afterInsertionActivityIndex]
    # travelingDurationToNextStep = solution.computeTravelingDuration(step, nextStep)
    # nextArrivalTime = startTimeForDownstream + enteringTask.duration + travelingDurationToNextStep
    # nextStep.arrivalTime = nextArrivalTime
    # if nextStep.startTime < nextArrivalTime:
    #     solution.updateTimesDownstream(employeeName, stepIndex = afterInsertionActivityIndex, startTime = nextArrivalTime)
    #
    # # Update time slacks
    # #solution.propagateBTSForwardFrom(employeeName, stepIndex = enteringActivityIndex)
    # #solution.propagateFTSBackwardFrom(employeeName, stepIndex = enteringActivityIndex)
    #
    # # Update tasks' realization
    # enteringTaskDescription = solution.tasksDescriptions[enteringTask.name]
    # enteringTaskDescription['realized'] = True
    # enteringTaskDescription['employeeName'] = employeeName
    # enteringTaskDescription['startTime'] = meanStartTime
    #
    # # Update KPIs
    # #solution.KPIs['nbRealizedTasks'] += 1
    # #solution.KPIs['totalWorkingDuration'] += enteringTask.duration
    # #newTotalTravelingDuration, newTotalTravelingDistance, newTotalIdleTime = solution.computeSequenceKPIs(sequence)
    # #solution.KPIs['totalTravelingDuration'] += newTotalTravelingDuration - formerTotalTravelingDuration
    # #solution.KPIs['totalTravelingDistance'] += newTotalTravelingDistance - formerTotalTravelingDistance
    # #solution.KPIs['totalIdleTime'] += newTotalIdleTime - formerTotalIdleTime
    #
    # return solution
