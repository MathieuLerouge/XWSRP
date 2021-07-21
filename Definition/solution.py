###########
# Modules #
###########


# Basic modules
import copy
import numpy as np

# Project modules
from Definition.activity import *
from Definition.employee import *
from Definition.instance import *
from Tools.global_variables import *
from Tools.time import *



##############
# Class Step #
##############


class Step:

    activity = None
    arrivalTime = None
    startTime = None
    endTime = None


    def __init__(self, activity: Activity, arrivalTime = None, startTime = None, endTime = None):
        self.set(activity, arrivalTime, startTime, endTime)


    def __eq__(self, step):
        return isinstance(step, Step) and self.activity.name == step.activity.name and \
            self.startTime == step.startTime and self.endTime == step.endTime


    def __lt__(self, step):
        return self.startTime <= step.startTime and self.endTime <= step.endTime


    def set(self, activity: Activity, arrivalTime = None, startTime = None, endTime = None):
        self.activity = activity
        self.arrivalTime = arrivalTime
        self.startTime = startTime
        self.endTime = startTime + self.activity.duration if endTime is None else endTime


    def clear(self):
        self.activity = None
        self.arrivalTime = None
        self.startTime = None
        self.endTime = None


    def copy(self):
        return Step(self.activity, self.arrivalTime, self.startTime, self.endTime)


    def __repr__(self):
        bracketLeft = '{'
        bracketRight = '}'
        symbol = f"{bracketLeft}{self.activity.name}: "
        if self.arrivalTime != None:
            symbol += f"Ta = {convert_nb_minutes_to_time_string(self.arrivalTime)}, "
        symbol += f"Ts = {convert_nb_minutes_to_time_string(self.startTime)}"
        if self.endTime != None:
            symbol += f", Te = {convert_nb_minutes_to_time_string(self.endTime)}"
        symbol += f"{bracketRight}"
        return symbol



##################
# Class Sequence #
##################


class Sequence:


    instance = None
    steps = None
    KPIs = None


    #--------#
    # Basics #
    #--------#


    def __init__(self, instance: Instance, employee: Employee, steps = [], KPIs = None):
        self.instance = instance
        self.employee = employee
        self.steps = steps
        self.KPIs = KPIs


    def __getitem__(self, index):
        return self.steps[index]


    def __setitem__(self, index, step):
        self.steps[index]


    def __len__(self):
        return len(self.steps)


    def append(self, step):
        self.steps.append(step)


    def insert(self, index, step):
        self.steps.insert(index, step)


    def pop(self, index = -1):
        return self.steps.pop(index)

    def _copySteps(self):
        return [step.copy() for step in self.steps]

    def _copyKPIs(self):
        return copy.deepcopy(self.KPIs)


    def copy(self):
        return Sequence(self.instance, self.employee, self._copySteps(), self._copyKPIs())


    def clear(self):
        while not(self.steps.empty()):
            step = self.steps.pop()
            step.clear()
        self.steps = None
        self.KPIs = None


    def __repr__(self):
        return self.steps.__repr__()



    #------------#
    # Activities #
    #------------#


    def getActivities(self, includingStart = True, includingEnd = True,
        includingUnavailabilities = True, alphaOrdered = False):
        activities = []
        if includingStart:
            activities.append(self.steps[0].activity)
        if alphaOrdered:
            activitiesPairs = []
            for step in self.steps[1:-1]:
                if step.activity.isTask() or includingUnavailabilities:
                    activitiesPairs.append((step.activity.name, step.activity))
            activitiesPairs.sort()
            for _, activity in activitiesPairs:
                activities.append(activity)
        else:
            for step in self.steps[1:-1]:
                if step.activity.isTask() or includingUnavailabilities:
                    activities.append(step.activity)
        if includingEnd:
            activities.append(self.steps[0].activity)
        return activities


    def getTasks(self, alphaOrdered = False):
        return self.getActivities(False, False, False, alphaOrdered)


    def getActivitiesNames(self, includingStart = True, includingEnd = True,
        includingUnavailabilities = True, alphaOrdered = False):
        activitiesNames = []
        if includingStart:
            activitiesNames.append(self.steps[0].activity.name)
        if alphaOrdered:
            tasksNamesPairs = []
            unavailabilitiesNamesPairs = []
            for step in self.steps[1:-1]:
                if step.activity.isTask():
                    tasksNamesPairs.append((int(step.activity.name[1:]), step.activity.name))
                elif includingUnavailabilities:
                    unavailabilitiesNamesPairs.append((int(step.activity.name[1:]), step.activity.name))
            tasksNamesPairs.sort()
            unavailabilitiesNamesPairs.sort()
            activitiesNames += [taskName for _, taskName in tasksNamesPairs]
            activitiesNames += [unavailabilityName for _, unavailabilityName in unavailabilitiesNamesPairs]
        else:
            for step in self.steps[1:-1]:
                if step.activity.isTask() or includingUnavailabilities:
                    activitiesNames.append(step.activity.name)
        if includingEnd:
            activitiesNames.append(self.steps[0].activity.name)
        return activitiesNames


    def getTasksNames(self, alphaOrdered = False):
        return self.getActivitiesNames(False, False, False, alphaOrdered)


    def getStepIndexOfActivity(self, activityName):
        activityIndex = 0
        nbSteps = len(self.steps)
        while activityIndex < nbSteps and self.steps[activityIndex].activity.name != activityName:
            activityIndex += 1
        if activityIndex >= nbSteps:
            raise ValueError(f"{activityName} is not in this sequence {self}")
        return activityIndex


    def getStepIndicesOfTasks(self):
        tasksIndices = []
        for stepIndex in range(1, len(self.steps) - 1):
            if self.steps[stepIndex].activity.isTask():
                tasksIndices.append(stepIndex)
        return tasksIndices



    #-------#
    # Times #
    #-------#


    # Assumptions:
    # - no lunch breaks;
    # - no tasks unavailabilities.


    def shiftTimesBackwardFrom(self, stepIndex, startTime):
        timeVariation = self.steps[stepIndex].startTime - startTime
        while timeVariation > 0 and stepIndex >= 0:
            step = self.steps[stepIndex]
            step.startTime -= timeVariation
            step.endTime -= timeVariation
            timeVariation = max(step.arrivalTime - step.startTime, 0)
            step.arrivalTime -= timeVariation
            stepIndex -= 1
        return stepIndex + 1


    def shiftTimesForwardFrom(self, stepIndex, startTime):
        timeVariation = startTime - self.steps[stepIndex].startTime
        if stepIndex == 0 and timeVariation > 0:
            self.steps[0].arrivalTime = startTime
        while timeVariation > 0 and stepIndex <= len(self.steps) - 2:
            step = self.steps[stepIndex]
            nextStep = self.steps[stepIndex + 1]
            step.startTime += timeVariation
            step.endTime += timeVariation
            nextStep.arrivalTime += timeVariation
            timeVariation = max(nextStep.arrivalTime - nextStep.startTime, 0)
            stepIndex += 1
        self.steps[-1].startTime = self.steps[-1].arrivalTime
        self.steps[-1].endTime = self.steps[-1].arrivalTime
        return stepIndex


    def updateTimesGivenStartTimes(self, lunchBreakDescription = None, updateReturnTimes = True):
        self.steps[0].arrivalTime = self.steps[0].startTime
        self.steps[0].endTime = self.steps[0].startTime
        for previousStepIndex, step in enumerate(self.steps[1:]):
            previousStep = self.steps[previousStepIndex]
            step.arrivalTime = previousStep.endTime + self.instance.computeTravelingDuration(previousStep.activity, step.activity)
            if lunchBreakDescription != None and lunchBreakDescription['stepAfter'] == step.activity.name:
                step.arrivalTime += self.instance.lunchBreakDuration
            step.endTime = step.startTime + step.activity.duration
        if updateReturnTimes:
            self.steps[-1].startTime = self.steps[-1].arrivalTime
            self.steps[-1].endTime = self.steps[-1].startTime


    def updateTimesAccordingToEarliestPolicy(self):
        print("Code not yet implemented")



    #------#
    # KPIs #
    #------#


    def getKPI(self, KPIName):
        return self.KPIs[KPIName]


    def getKPIs(self):
        return self._copyKPIs()


    def updateKPIs(self):
        nbRealizedTasks = 0
        totalWorkingDuration = 0
        totalTravelingDuration = 0
        #totalTravelingDistance = 0
        totalIdleTime = 0
        for stepIndex, step in enumerate(self.steps[:-1]):
            if step.activity.isTask():
                nbRealizedTasks += 1
                totalWorkingDuration += step.activity.duration
            #distance = self.instance.computeTravelingDistance(step.activity, self.steps[stepIndex + 1].activity)
            #totalTravelingDistance += distance
            totalTravelingDuration += self.instance.computeTravelingDuration(step.activity, self.steps[stepIndex + 1].activity)
            totalIdleTime += step.startTime - step.arrivalTime
        #totalTravelingDistance = np.round(totalTravelingDuration*self.instance.speed)
        self.KPIs = dict()
        self.KPIs['nbRealizedTasks'] = nbRealizedTasks
        self.KPIs['totalWorkingDuration'] = totalWorkingDuration
        #self.KPIs['totalTravelingDistance'] = totalTravelingDistance
        self.KPIs['totalTravelingDuration'] = totalTravelingDuration
        self.KPIs['totalIdleTime'] = totalIdleTime



##################
# Class Solution #
##################


class Solution:

    instance = None
    name = None
    sequences = None
    tasksDescriptions = None
    lunchBreaksDescriptions = None
    KPIs = None
    optimization = None



    #--------#
    # Basics #
    #--------#


    def __init__(self, instance: Instance, name = None, sequences = None, tasksDescs = None, LBsDescs = None):
        self.instance = instance
        self.name = name if name != None else "Solution" + instance.name
        if sequences == None:
            sequences = dict()
            for employeeName in self.instance.getEmployeesNames():
                sequences[employeeName] = []
        self.sequences = sequences
        if tasksDescs == None:
            tasksDescs = dict()
            for taskName in self.instance.tasks.keys():
                tasksDescs[taskName] = dict()
                tasksDescs[taskName]['realized'] = False
        self.tasksDescriptions = tasksDescs
        self.lunchBreaksDescriptions = LBsDescs


    def _copySequences(self):
        sequences = dict()
        for employeeName, sequence in self.sequences.items():
            sequences[employeeName] = sequence.copy()
        return sequences


    def _copyTasksDescs(self):
        return copy.deepcopy(self.tasksDescriptions)


    def _copyLBsDescs(self):
        return copy.deepcopy(self.lunchBreaksDescriptions)


    def _copyKPIs(self):
        return copy.deepcopy(self.KPIs)


    def copy(self, copyName = None):
        name = self.name if copyName == None else copyName
        solution = Solution(self.instance, name, self._copySequences(), self._copyTasksDescs(), self._copyLBsDescs())
        solution.KPIs = self._copyKPIs()
        return solution



    #----------#
    # Distance #
    #----------#


    def computeTravelingDistance(self, step1: Step, step2: Step):
        return self.instance.computeTravelingDistance(step1.activity, step2.activity)


    def computeTravelingDuration(self, step1: Step, step2: Step):
        return self.instance.computeTravelingDuration(step1.activity, step2.activity)



    #------------#
    # Activities #
    #------------#


    def taskIsRealizedBy(self, task: Task):
        if self.tasksDescriptions[task.name]['realized']:
            #return True, self.tasksDescriptions[task.name]['employee']
            return True, self.instance.getEmployee(self.tasksDescriptions[task.name]['employeeName'])
        else:
            return False, None


    def activityIsRealizedBy(self, activity: Activity):
        if not(activity.isTask()):
            return True, activity.getEmployee()
        else:
            return self.taskIsRealizedBy(activity)


    def getFilteredTasksNames(self, employee, excludingTasksWithHigherSkills, excludingRealizedTasks, excludingNonEmployeesTasks, excludingEmployeesTasks):
        tasksNames = []
        if employee is None:
            for task in self.instance.getTasks():
                if not(excludingRealizedTasks and self.tasksDescriptions[task.name]['realized']):
                    tasksNames.append(task.name)
        else:
            for task in self.instance.getTasks():
                if excludingNonEmployeesTasks:
                    if self.tasksDescriptions[task.name]['realized'] and self.tasksDescriptions[task.name]['employeeName'] == employee.name:
                        tasksNames.append(task.name)
                else:
                    if not(excludingRealizedTasks and self.tasksDescriptions[task.name]['realized']) and \
                        not(excludingTasksWithHigherSkills and employee.skillLevel < task.skillLevel) and \
                        not(excludingEmployeesTasks and self.tasksDescriptions[task.name]['realized'] and self.tasksDescriptions[task.name]['employeeName'] == employee.name):
                        tasksNames.append(task.name)
        return tasksNames



    #---------------------#
    # Employee's sequence #
    #---------------------#


    def getSequence(self, employeeName):
        return self.sequences[employeeName]


    def getEmployeePossibleTasksNames(self, employee: Employee,
        includingTasksRealizedByOneself = True,  includingTasksRealizedByOthers = True, includingTasksWithHigherSkills = True):
        tasksNames = []
        for task in self.instance.getTasks():
            if includingTasksWithHigherSkills or employee.skillLevel >= task.skillLevel:
                if self.tasksDescriptions[task.name]['realized']:
                    if self.tasksDescriptions[task.name]['employeeName'] == employee.name:
                        if includingTasksRealizedByOneself:
                            tasksNames.append(task.name)
                    else:
                        if includingTasksRealizedByOthers:
                            tasksNames.append(task.name)
                else:
                    tasksNames.append(task.name)
        return tasksNames


    def _updateTimesInTasksDescriptionsForTasksOfStepsInRange(self, employee: Employee, startStepIndex, endStepIndex):
        sequence = self.sequences[employee.name]
        for step in sequence[startStepIndex: endStepIndex + 1]:
            if step.activity.isTask():
                self.tasksDescriptions[step.activity.name]['startTime'] = step.startTime



    #-------#
    # Times #
    #-------#


    def _setupSequencesStepsOrder(self):

        # Find the tasks realized by each employee
        employeesTasks = dict()
        for employeeName in self.instance.getEmployeesNames():
            employeesTasks[employeeName] = []
        for taskName, taskDescription in self.tasksDescriptions.items():
            if taskDescription['realized']:
                employeesTasks[taskDescription['employeeName']].append((taskDescription['startTime'], taskName))

        # Create employees' sequences
        for employeeName, employee in self.instance.employees.items():

            # Create employee's sequence of tasks without unavailabilities
            employeesTasks[employeeName].sort()
            sequence = Sequence(self.instance, employee, [])
            sequence.append(
                Step(activity = Home(employee = employee, start = True),
                    arrivalTime = employee.startTime, startTime = employee.startTime, endTime = employee.startTime)
                )
            for startTime, taskName in employeesTasks[employeeName]:
                task = self.instance.tasks[taskName]
                sequence.append(
                    Step(activity = task, startTime = startTime, endTime = startTime + task.duration)
                )
            sequence.append(
                Step(activity = Home(employee = employee, start = False),
                    startTime = employee.endTime, endTime = employee.endTime)
                )

            # Add employee's unavailabilities
            for unavailability in employee.unavailabilities.values():
                insertionIndex = len(sequence) - 1
                for j, step in enumerate(sequence[1:-1]):
                    if unavailability.startTime < step.startTime:
                        insertionIndex = j + 1
                        break
                step = Step(activity = unavailability, startTime = unavailability.startTime, endTime = unavailability.endTime)
                sequence.insert(insertionIndex, step)

            self.sequences[employeeName] = sequence


    def _setupLunchBreaksDescriptions(self):

        if self.instance.hasLunchBreaks():
            self.lunchBreaksDescriptions = dict()

            for employeeName, sequence in self.sequences.items():
                lunchBreakDescription = dict()

                candidateStepAfterIndexMin = 1
                while sequence[candidateStepAfterIndexMin].startTime < (self.instance.lunchBreakStartTime + self.instance.lunchBreakDuration):
                    candidateStepAfterIndexMin += 1
                candidateStepAfterIndexMax = candidateStepAfterIndexMin
                while sequence[candidateStepAfterIndexMax].endTime <= (self.instance.lunchBreakEndTime - self.instance.lunchBreakDuration):
                    candidateStepAfterIndexMax += 1

                for candidateStepAfterIndex in range(candidateStepAfterIndexMin, candidateStepAfterIndexMax + 1):
                    candidateStepBefore = sequence[candidateStepAfterIndex - 1]
                    candidateStepAfter = sequence[candidateStepAfterIndex]
                    travelingDurationBetweenSteps = self.computeTravelingDuration(candidateStepBefore, candidateStepAfter)
                    durationBeforeBeingAbleToLunch = max(0, self.instance.lunchBreakStartTime - candidateStepBefore.endTime)
                    travelingDurationBeforeLunch = min(durationBeforeBeingAbleToLunch, travelingDurationBetweenSteps)
                    lunchBreakStartTime = max(self.instance.lunchBreakStartTime, candidateStepBefore.endTime + travelingDurationBeforeLunch)
                    if (lunchBreakStartTime + self.instance.lunchBreakDuration) + (travelingDurationBetweenSteps - travelingDurationBeforeLunch) <= \
                        candidateStepAfter.startTime:
                        lunchBreakDescription['stepBefore'] = candidateStepBefore.activity.name
                        lunchBreakDescription['stepAfter'] = candidateStepAfter.activity.name
                        lunchBreakDescription['startTime'] = max(candidateStepBefore.endTime, self.instance.lunchBreakStartTime)
                        break

                if not('startTime' in lunchBreakDescription.keys()):
                    print("LB problem!")
                    lunchBreakDescription['stepBefore'] = sequence[candidateStepAfterIndexMin - 1]['name']
                    lunchBreakDescription['stepAfter'] = sequence[candidateStepAfterIndexMin]['name']
                    lunchBreakDescription['startTime'] = max(sequence[candidateStepAfterIndexMin - 1]['endTime'], self.instance.lunchBreakStartTime)

                self.lunchBreaksDescriptions[employeeName] = lunchBreakDescription


    def _setupDepartureAndReturnTimes(self):

        for employeeName, sequence in self.sequences.items():

            employee = self.instance.getEmployee(employeeName)
            lunchBreakDescription = dict()
            lunchBreakDuration = None
            if self.instance.hasLunchBreaks():
                lunchBreakDescription = self.lunchBreaksDescriptions[employeeName]
                lunchBreakDuration = self.instance.lunchBreakDuration
            else:
                lunchBreakDescription['stepBefore'] = sequence[0].activity.name
                lunchBreakDescription['stepAfter'] = sequence[-1].activity.name
                lunchBreakDuration = 0

            # Case where the employee does not move
            if len(sequence) == 2:
                sequence[0].arrivalTime = employee.startTime
                sequence[0].startTime = sequence[0].arrivalTime
                sequence[0].endTime = sequence[0].arrivalTime
                sequence[1].arrivalTime = employee.startTime + lunchBreakDuration
                sequence[1].startTime = sequence[1].arrivalTime
                sequence[1].endTime = sequence[1].arrivalTime

            # Case where the employee does move
            else:

                # Fill start step
                #sequence[0].startTime = int(np.floor(sequence[1].startTime - self.computeTravelingDuration(sequence[0], sequence[1])))
                sequence[0].startTime = sequence[1].startTime - self.computeTravelingDuration(sequence[0], sequence[1])
                if lunchBreakDescription['stepBefore'] == sequence[0].activity.name:
                    sequence[0].startTime -= lunchBreakDuration
                sequence[0].arrivalTime = sequence[0].startTime
                sequence[0].endTime = sequence[0].startTime

                # Fill end step
                #sequence[-1].arrivalTime = int(np.ceil(sequence[-2].endTime + self.computeTravelingDuration(sequence[-2], sequence[-1])))
                sequence[-1].arrivalTime = sequence[-2].endTime + self.computeTravelingDuration(sequence[-2], sequence[-1])
                if lunchBreakDescription['stepAfter'] == sequence[-1].activity.name:
                    sequence[-1].arrivalTime += lunchBreakDuration
                sequence[-1].startTime = sequence[-1].arrivalTime
                sequence[-1].endTime = sequence[-1].arrivalTime


    # TODO: change effect of lunch break on arrival time, cf BordeauxV2
    def _setupStepsArrivalTimes(self):

        for employeeName, sequence in self.sequences.items():

            if len(sequence) > 2:

                employee = self.instance.getEmployee(employeeName)
                lunchBreakDescription = dict()
                lunchBreakDuration = None
                if self.instance.hasLunchBreaks():
                    lunchBreakDescription = self.lunchBreaksDescriptions[employeeName]
                    lunchBreakDuration = self.instance.lunchBreakDuration
                else:
                    lunchBreakDescription['stepBefore'] = sequence[0].activity.name
                    lunchBreakDescription['stepAfter'] = sequence[-1].activity.name
                    lunchBreakDuration = 0

                for previousStepIndex, step in enumerate(sequence[1: -1]):
                    previousStep = sequence[previousStepIndex]
                    #step.arrivalTime = int(np.ceil(previousStep.endTime + self.computeTravelingDuration(previousStep, step)))
                    step.arrivalTime = previousStep.endTime + self.computeTravelingDuration(previousStep, step)
                    if lunchBreakDescription['stepAfter'] == step.activity.name:
                        step.arrivalTime += lunchBreakDuration


    def updateTimesAccordingToTasksDescriptions(self):
        self._setupSequencesStepsOrder()
        if self.instance.hasLunchBreaks():
            self._setupLunchBreaksDescriptions()
        self._setupDepartureAndReturnTimes()
        self._setupStepsArrivalTimes()


    def updateTimesAccordingToEarliestPolicy(self):
        for employeeName, sequence in self.sequences.items():
            sequence.updateTimesAccordingToEarliestPolicy(self.instance.getEmployee(employeeName), self.tasksDescriptions)



    #------#
    # KPIs #
    #------#


    def getKPI(self, KPIName):
        return self.KPIs[KPIName]


    def getKPIs(self):
        return self._copyKPIs()


    def _initializeKPIs(self):
        self.KPIs = dict()
        self.KPIs['nbRealizedTasks'] = 0
        self.KPIs['totalWorkingDuration'] = 0
        #self.KPIs['totalTravelingDistance'] = 0
        self.KPIs['totalTravelingDuration'] = 0
        self.KPIs['totalIdleTime'] = 0


    def updateKPIs(self):
        self._initializeKPIs()
        for sequence in self.sequences.values():
            sequence.updateKPIs()
            sequenceKPIs = sequence.getKPIs()
            for key, value in sequenceKPIs.items():
                self.KPIs[key] += value



    #--------------#
    # Optimization #
    #--------------#


    def setOptimizationData(self, methodId, runTime, parameters = None,
        optimalityGap = None, objectiveValue = None):
        self.optimization = dict()
        self.optimization['solvingMethodId'] = methodId
        self.optimization['solvingMethodParameters'] = parameters
        self.optimization['solvingRunTime'] = runTime
        self.optimization['optimalityGap'] = optimalityGap
        self.optimization['objectiveValue'] = objectiveValue
        self.name = "Solution" + self.instance.name + "ByV" + str(methodId)
        if parameters != None:
            self.name += "("
            for parameter in parameters:
                self.name += str(parameter) if parameter != None else "0"
                self.name += ","
            self.name += str(int(np.round(runTime))) + "s"
            self.name += ")"



    #---------#
    # Display #
    #---------#


    def __repr__(self):
        symbol = ""
        for employeeName in self.instance.getEmployeesNames():
            sequence = self.sequences[employeeName]
            symbol += employeeName + ": "
            for stepIndex, step in enumerate(sequence[:-1]):
                symbol += f"{str(step)} {moveSymbol} "
                symbol += str(self.computeTravelingDuration(step, sequence[stepIndex + 1]))
                symbol += f" {moveSymbol} "
            symbol += str(sequence[-1]) + lineBreakSymbol
        symbol = symbol[:-2]
        return symbol



    #------------#
    # Deprecated #
    #------------#


    def getActivityIndexInEmployeeSequence(self, employeeName, activityName):
        print("Deprecated: Solution.getActivityIndexInEmployeeSequence is deprecated, use Sequence.getStepIndexOfActivity()")
        return self.sequences[employeeName].getStepIndexOfActivity(activityName)


    # Assumption: startTime < step.startTime
    def updateTimesUpstream(self, employeeName, stepIndex, startTime):
        print("Deprecated: Solution.updateTimesUpstream is deprecated, use Sequence.shiftTimesBackwardFrom()")
        sequence = self.sequences[employeeName]
        sequence.shiftTimesBackwardFrom(stepIndex, startTime)


    # Assumption: startTime > step.startTime
    def updateTimesDownstream(self, employeeName, stepIndex, startTime):
        print("Deprecated: Solution.updateTimesDownstream is deprecated, use Sequence.shiftTimesForwardFrom()")
        sequence = self.sequences[employeeName]
        sequence.shiftTimesForwardFrom(stepIndex, startTime)


    def computeSequencesAndLunchBreaks(self):
        print("Deprecated: Solution.computeSequencesAndLunchBreaks is deprecated, use Solution.updateTimesAccordingToTasksDescriptions()")
        self.updateTimesAccordingToTasksDescriptions()


    def computeKPIs(self):
        print("Deprecated: Solution.computeKPIs is deprecated, use Solution.updateKPIs()")
        self.updateKPIs()
