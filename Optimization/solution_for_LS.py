###########
# Modules #
###########


# Project modules
from Definition.activity import *
from Definition.instance import *
from Definition.solution import *
from Optimization.IP_model_for_sequence import *



###################
# Class StepForLS #
###################


class StepForLS(Step):

    BTS = None
    FTS = None


    def __init__(self, activity: Activity, arrivalTime = None, startTime = None, endTime = None, BTS = None, FTS = None):
        self.set(activity, arrivalTime, startTime, endTime, BTS, FTS)


    @classmethod
    def fromStep(cls, step: Step):
        return cls(step.activity, step.arrivalTime, step.startTime, step.endTime)


    def set(self, activity: Activity, arrivalTime = None, startTime = None, endTime = None, BTS = None, FTS = None):
        super().set(activity, arrivalTime, startTime, endTime)
        self.BTS = BTS
        self.FTS = FTS


    def clear(self):
        super().clear()
        self.BTS = None
        self.FTS = None


    def copy(self):
        return StepForLS(self.activity, self.arrivalTime, self.startTime, self.endTime, self.BTS, self.FTS)


    def __repr__(self):
        bracketLeft = '{'
        bracketRight = '}'
        symbol = f"{bracketLeft}{self.activity.name}: "
        if self.arrivalTime != None:
            symbol += f"Ta = {convert_nb_minutes_to_time_string(self.arrivalTime)}, "
        symbol += f"Ts = {convert_nb_minutes_to_time_string(self.startTime)}"
        if self.endTime != None:
            symbol += f", Te = {convert_nb_minutes_to_time_string(self.endTime)}"
        if self.BTS != None:
            symbol += f", BTS = {self.BTS}, FTS = {self.FTS}"
        symbol += f"{bracketRight}"
        return symbol



#######################
# Class SequenceForLS #
#######################


class SequenceForLS(Sequence):



    #--------#
    # Basics #
    #--------#


    def __init__(self, instance: Instance, employee: Employee, steps, KPIs = None):
        super().__init__(instance, employee, steps, KPIs)


    @classmethod
    def fromSequence(cls, sequence: Sequence):
        steps = [StepForLS.fromStep(step) for step in sequence]
        return SequenceForLS(sequence.instance, sequence.employee, steps, sequence._copyKPIs())


    def copy(self):
        return SequenceForLS(self.instance, self.employee, self._copySteps(), self._copyKPIs())



    #-------#
    # Times #
    #-------#


    # Assumptions:
    # - no lunch breaks;
    # - no tasks unavailabilities.


    # Rk: the function returns the index of the first step which start time has been changed
    def shiftTimesBackwardFrom(self, stepIndex, startTime):
        timeVariation = self.steps[stepIndex].startTime - startTime
        while timeVariation > 0 and stepIndex >= 0:
            step = self.steps[stepIndex]
            step.startTime -= timeVariation
            step.endTime -= timeVariation
            step.BTS -= timeVariation
            step.FTS += timeVariation
            timeVariation = max(step.arrivalTime - step.startTime, 0)
            step.arrivalTime -= timeVariation
            stepIndex -= 1
        return stepIndex + 1


    # Rk: the function returns the index of the last step which start time has been changed
    def shiftTimesForwardFrom(self, stepIndex, startTime):
        timeVariation = startTime - self.steps[stepIndex].startTime
        if stepIndex == 0 and timeVariation > 0:
            self.steps[0].arrivalTime = startTime
        while timeVariation > 0 and stepIndex <= len(self.steps) - 2:
            step = self.steps[stepIndex]
            nextStep = self.steps[stepIndex + 1]
            step.startTime += timeVariation
            step.endTime += timeVariation
            step.BTS += timeVariation
            step.FTS -= timeVariation
            nextStep.arrivalTime += timeVariation
            timeVariation = max(nextStep.arrivalTime - nextStep.startTime, 0)
            stepIndex += 1
        self.steps[-1].startTime = self.steps[-1].arrivalTime
        self.steps[-1].endTime = self.steps[-1].arrivalTime
        return stepIndex


    def tightenTimes(self, updateKPIs = True):
        idleTimeVariation = 0
        timeVariationForward = self.steps[0].FTS
        if timeVariationForward > 0:
            formerReturnTime = self.steps[-1].startTime
            self.shiftTimesForwardFrom(0, self.steps[0].startTime + timeVariationForward)
            self.steps[0].arrivalTime = self.steps[0].startTime
            idleTimeVariation += timeVariationForward - (self.steps[-1].startTime - formerReturnTime)
        timeVariationBackward = self.steps[-1].BTS
        if timeVariationBackward > 0:
            formerDepartureTime = self.steps[0].startTime
            self.shiftTimesBackwardFrom(len(self.steps) - 1, self.steps[-1].startTime - timeVariationBackward)
            idleTimeVariation += timeVariationBackward - (self.steps[0].startTime - formerDepartureTime)
        if updateKPIs:
            self.KPIs['totalIdleTime'] -= idleTimeVariation



    #-------------#
    # Time slacks #
    #-------------#


    # Assumptions:
    # - no lunch breaks;
    # - no tasks unavailabilities.


    # Assumption: stepIndex > 0 and BTS[stepIndex - 1] is computed
    def updateBTSForwardFrom(self, stepIndex):
        for previousStepIndex in range(stepIndex - 1, len(self.steps) - 1):
            step = self.steps[previousStepIndex + 1]
            previousStep = self.steps[previousStepIndex]
            step.BTS = min(step.startTime - step.activity.startTime,
                step.startTime - (previousStep.startTime - previousStep.BTS + previousStep.activity.duration + \
                    self.instance.computeTravelingDuration(previousStep.activity, step.activity)))


    # Assumption: stepIndex < -1 and FTS[stepIndex + 1] is computed
    def updateFTSBackwardFrom(self, stepIndex):
        for nextStepIndex in range(stepIndex + 1, 0, -1):
            step = self.steps[nextStepIndex - 1]
            nextStep = self.steps[nextStepIndex]
            step.FTS = min(step.activity.endTime - (step.startTime + step.activity.duration),
                nextStep.startTime + nextStep.FTS - (step.startTime + step.activity.duration + \
                    self.instance.computeTravelingDuration(step.activity, nextStep.activity)))


    def updateTimeSlacks(self):
        self.steps[0].BTS = self.steps[0].startTime - self.employee.startTime
        self.updateBTSForwardFrom(1)
        self.steps[-1].FTS = self.employee.endTime - self.steps[-1].startTime
        self.updateFTSBackwardFrom(len(self.steps) - 2)



    #------------#
    # Looking up #
    #------------#


    def findBestInsertion(self, task: Task, tabuIndices = []):

        assert self.steps[-1].arrivalTime == self.steps[-1].startTime and self.steps[-1].startTime == self.steps[-1].endTime, "Return times are not equal"

        insertionIsFeasible = False
        taskSkillLevelIsTooHigh = False
        taskCannotBeReachedOnTime = False
        insertionStepIndex = None
        bestTravelingDurationDetour = None
        bestLate = None
        bestInsertionIndex = None
        bestEarliestStartTimeOfEnteringTask = None

        # Check skill levels
        if self.employee.skillLevel < task.skillLevel:
            taskSkillLevelIsTooHigh = True

        # Go through all possible insertions
        else:
            insertionStepIndex = 1
            while insertionStepIndex <= len(self.steps) - 1:

                if insertionStepIndex in tabuIndices:

                    # Go to next step
                    insertionStepIndex += 1

                else:

                    # Compute earliest start time of entering task if inserted after stepBeforeInsertion
                    stepBeforeInsertion = self.steps[insertionStepIndex - 1]
                    travelingDurationFromStepBeforeInsertion = self.instance.computeTravelingDuration(stepBeforeInsertion.activity, task)
                    earliestStartTimeOfEnteringTask = max(task.startTime,
                        stepBeforeInsertion.startTime - stepBeforeInsertion.BTS + stepBeforeInsertion.activity.duration + travelingDurationFromStepBeforeInsertion)

                    # If it is possible to end realizing the task before its end time
                    if earliestStartTimeOfEnteringTask + task.duration <= task.endTime:

                        # Compute earliest start time of step after insertion
                        stepAfterInsertion = self.steps[insertionStepIndex]
                        travelingDurationToStepAfterInsertion = self.instance.computeTravelingDuration(task, stepAfterInsertion.activity)
                        earliestStartTimeOfStepAfterInsertion = max(stepAfterInsertion.activity.startTime,
                            earliestStartTimeOfEnteringTask + task.duration + travelingDurationToStepAfterInsertion)

                        # If it is possible to end realizing the stepAfterInsertion before its latest start time
                        if earliestStartTimeOfStepAfterInsertion <= stepAfterInsertion.startTime + stepAfterInsertion.FTS:

                            # Save insertion if best relatively to traveling duration detour
                            insertionIsFeasible = True
                            travelingDurationDetour = travelingDurationFromStepBeforeInsertion + travelingDurationToStepAfterInsertion -\
                                self.instance.computeTravelingDuration(stepBeforeInsertion.activity, stepAfterInsertion.activity)
                            if bestTravelingDurationDetour == None or travelingDurationDetour < bestTravelingDurationDetour:
                                bestTravelingDurationDetour = travelingDurationDetour
                                bestInsertionIndex = insertionStepIndex
                                bestEarliestStartTimeOfEnteringTask = earliestStartTimeOfEnteringTask

                        # If it is not possible to end realizing the stepAfterInsertion before its latest start time
                        # and no feasible insertion is yet known
                        elif not(insertionIsFeasible):

                            # Save insertion if best relatively to late
                            late = earliestStartTimeOfStepAfterInsertion - (stepAfterInsertion.startTime + stepAfterInsertion.FTS)
                            if bestLate == None or late < bestLate:
                                bestLate = late
                                bestInsertionIndex = insertionStepIndex
                                bestEarliestStartTimeOfEnteringTask = earliestStartTimeOfEnteringTask

                        # Go to next step
                        insertionStepIndex += 1

                    # If it is not possible to end realizing the task before its end time
                    else:

                        # If no other insertion has been studied
                        if bestInsertionIndex == None:
                            bestInsertionIndex = 0
                            bestEarliestStartTimeOfEnteringTask = earliestStartTimeOfEnteringTask
                            bestLate = earliestStartTimeOfEnteringTask + task.duration - task.endTime
                            taskCannotBeReachedOnTime = True

                        # Stop the while loop
                        insertionStepIndex = len(self.steps)

        insertionResult = dict()
        insertionResult['feasible'] = insertionIsFeasible
        insertionResult['stepIndex'] = bestInsertionIndex
        insertionResult['startTime'] = bestEarliestStartTimeOfEnteringTask
        insertionResult['travelingDurationVariation'] = bestTravelingDurationDetour
        insertionResult['late'] = bestLate
        insertionResult['taskSkillLevelTooHigh'] = taskSkillLevelIsTooHigh
        insertionResult['taskTooFar'] = taskCannotBeReachedOnTime
        return insertionResult


    def findCriticalStepIndexBackwardFrom(self, stepIndex):
        step = self.steps[stepIndex]
        while step.BTS < step.startTime - step.activity.startTime:
            stepIndex -= 1
            step = self.steps[stepIndex]
        return stepIndex


    def findCriticalStepIndexForwardFrom(self, stepIndex):
        step = self.steps[stepIndex]
        while step.FTS < step.activity.endTime - (step.startTime + step.activity.duration):
            stepIndex += 1
            step = self.steps[stepIndex]
        return stepIndex



    #-------------------------#
    # Local change - Feasible #
    #-------------------------#


    # Assumption: sequence of times is supposed to be correct
    def _popStep(self, stepIndex, tightenTimes = True, updateKPIs = True):

        assert self.steps[0].arrivalTime == self.steps[0].startTime and self.steps[0].startTime == self.steps[0].endTime, "Departure times are not equal"
        assert self.steps[-1].arrivalTime == self.steps[-1].startTime and self.steps[-1].startTime == self.steps[-1].endTime, "Return times are not equal"

        # Pop step
        removedStep = self.steps.pop(stepIndex)
        # Rk: now that the step has been popped out, stepIndex corresponds to the step after the removal

        # Get steps around the removed step
        stepBeforeRemoval = self.steps[stepIndex - 1]
        stepBeforeRemovalFormerEndTime = stepBeforeRemoval.endTime
        stepAfterRemoval = self.steps[stepIndex]
        stepAfterRemovalFormerArrivalTime = stepAfterRemoval.arrivalTime

        # Compute traveling duration
        travelingDurationBeforeAfter = self.instance.computeTravelingDuration(stepBeforeRemoval.activity, stepAfterRemoval.activity)


        # If step before removal is departure, then update it
        if stepIndex == 1:
            stepAfterRemoval.arrivalTime = stepAfterRemoval.startTime
            stepBeforeRemoval.endTime = stepAfterRemoval.arrivalTime - travelingDurationBeforeAfter
            stepBeforeRemoval.startTime = stepBeforeRemoval.endTime
            stepBeforeRemoval.arrivalTime = stepBeforeRemoval.startTime
            stepBeforeRemoval.BTS += stepBeforeRemoval.startTime - stepBeforeRemovalFormerEndTime
            assert stepBeforeRemoval.startTime >= stepBeforeRemovalFormerEndTime, \
                "After removal, departure time is found to be earlier than before"

        # Else, update arrival time of step after removal
        else:
            stepAfterRemoval.arrivalTime = stepBeforeRemoval.endTime + travelingDurationBeforeAfter
            assert stepAfterRemoval.arrivalTime <= stepAfterRemovalFormerArrivalTime, \
                "After removal, arrival time of step-after-removal is found to be later than before"

            # If step after removal is return, then update return times to be all equal
            if stepIndex == len(self.steps) - 1:
                stepAfterRemoval.FTS += stepAfterRemoval.startTime - stepAfterRemoval.arrivalTime
                stepAfterRemoval.startTime = stepAfterRemoval.arrivalTime
                stepAfterRemoval.endTime = stepAfterRemoval.startTime
                assert stepAfterRemoval.arrivalTime <= stepAfterRemovalFormerArrivalTime, \
                    "After removal, return time is found to be later than before"

        if updateKPIs:

            # Update tasks realization
            self.KPIs['nbRealizedTasks'] -= 1
            self.KPIs['totalWorkingDuration'] -= removedStep.activity.duration

            # Update traveling duration
            travelingDurationVariation = travelingDurationBeforeAfter
            travelingDurationVariation -= (removedStep.arrivalTime - stepBeforeRemovalFormerEndTime) # travelingDurationBefore
            travelingDurationVariation -= (stepAfterRemovalFormerArrivalTime - removedStep.endTime) # travelingDurationAfter
            self.KPIs['totalTravelingDuration'] += travelingDurationVariation
            assert removedStep.arrivalTime - stepBeforeRemovalFormerEndTime == \
                self.instance.computeTravelingDuration(stepBeforeRemoval.activity, removedStep.activity), \
                "Times before removal were incorrect, traveling duration was not respected"
            assert stepAfterRemovalFormerArrivalTime - removedStep.endTime == \
                self.instance.computeTravelingDuration(removedStep.activity, stepAfterRemoval.activity), \
                "Times after removal were incorrect, traveling duration was not respected"
            assert travelingDurationVariation <= 0, "After removal, variation of traveling duration is found to be positive"

            # Update idle time
            idleTimeVariation = stepAfterRemovalFormerArrivalTime - stepAfterRemoval.arrivalTime
            idleTimeVariation -= (removedStep.startTime - removedStep.arrivalTime)
            self.KPIs['totalIdleTime'] += idleTimeVariation

            # Update traveling distance
            #solution.KPIs['totalTravelingDistance'] += ...

        # Update times slacks if needed
        # BTS of steps from steps[0] (included) to steps[stepIndex - 1] (included) are correct
        # BTS of steps following steps[stepIndex] (included) must be updated
        self.updateBTSForwardFrom(stepIndex)
        # FTS of steps from steps[-1] (included) to steps[stepIndex] (included) are correct
        # FTS of steps preceding steps[stepIndex - 1] (included) must be updated
        self.updateFTSBackwardFrom(stepIndex - 1)
        if tightenTimes:
            self.tightenTimes(updateKPIs)

        return removedStep


    def _removeAllTasks(self, tightenTimes = True, updateKPIs = True):
        stepIndices = self.getStepIndicesOfTasks()
        for stepIndex in reversed(stepIndices):
            self._popStep(stepIndex, tightenTimes = False, updateKPIs = False)
        if updateKPIs:
            self.updateKPIs()
        if tightenTimes:
            self.tightenTimes(updateKPIs)


    # Assumption: sequence of times is supposed to be correct
    def _insertTaskAt(self, task: Task, stepIndex, startTime, tightenTimes = True, updateKPIs = True):

        # Initialize indices of the range of steps which startTime has been changed
        timeChangeFirstIndex = stepIndex
        timeChangeLastIndex = stepIndex

        # Insert step
        insertedStep = StepForLS(activity = task, arrivalTime = startTime, startTime = startTime, endTime = startTime + task.duration)
        self.steps.insert(stepIndex, insertedStep)

        # Get steps around the insertion
        stepBeforeInsertion = self.steps[stepIndex - 1]
        stepAfterInsertion = self.steps[stepIndex + 1]

        # Compute traveling durations
        travelingDurationBeforeAfter = stepAfterInsertion.arrivalTime - stepBeforeInsertion.endTime
        travelingDurationBefore = self.instance.computeTravelingDuration(stepBeforeInsertion.activity, task)
        travelingDurationAfter = self.instance.computeTravelingDuration(task, stepAfterInsertion.activity)
        assert travelingDurationBeforeAfter == \
            self.instance.computeTravelingDuration(stepBeforeInsertion.activity, stepAfterInsertion.activity), \
            "Times before and after insertion were incorrect, traveling duration was not respected"

        # Update times before insertion
        # Rk: insertedStep.arrivalTime is currently set to startTime
        timeVariation = startTime - (stepBeforeInsertion.endTime + travelingDurationBefore)
        timeShiftBackward = 0
        idleTimeAtInsertion = 0
        departureTimeShiftBackward = 0
        if timeVariation < 0:
            timeShiftBackward = -timeVariation
            departureFormerTime = self.steps[0].startTime
            timeChangeFirstIndex = self.shiftTimesBackwardFrom(stepIndex - 1, stepBeforeInsertion.startTime - timeShiftBackward)
            departureTimeShiftBackward = departureFormerTime - self.steps[0].startTime
        else:
            idleTimeAtInsertion = timeVariation
            insertedStep.arrivalTime = startTime - idleTimeAtInsertion

        # Update times after insertion
        formerIdleTimeAfter = stepAfterInsertion.startTime - stepAfterInsertion.arrivalTime
        stepAfterInsertion.arrivalTime = insertedStep.endTime + travelingDurationAfter
        timeVariation = stepAfterInsertion.startTime - stepAfterInsertion.arrivalTime
        timeShiftForward = 0
        idleTimeAfter = 0
        returnTimeShiftForward = 0
        if timeVariation < 0:
            timeShiftForward = -timeVariation
            arrivalFormerTime = self.steps[-1].startTime
            timeChangeLastIndex = self.shiftTimesForwardFrom(stepIndex + 1, stepAfterInsertion.arrivalTime)
            returnTimeShiftForward = self.steps[-1].startTime - arrivalFormerTime
        else:
            idleTimeAfter = timeVariation

        # Updare KPIs if needed
        if updateKPIs:

            # Update tasks realization
            self.KPIs['nbRealizedTasks'] += 1
            self.KPIs['totalWorkingDuration'] += insertedStep.activity.duration

            # Update traveling duration
            travelingDurationVariation = travelingDurationBefore + travelingDurationAfter - travelingDurationBeforeAfter
            self.KPIs['totalTravelingDuration'] += travelingDurationVariation
            assert travelingDurationVariation >= 0, "After insertion, variation of traveling duration is found to be negative"

            # Update idle time
            idleTimeVariation = idleTimeAtInsertion + idleTimeAfter - formerIdleTimeAfter
            if timeShiftBackward > 0:
                idleTimeVariation -= (timeShiftBackward - departureTimeShiftBackward)
            if timeShiftForward > 0:
                idleTimeVariation -= (timeShiftForward - returnTimeShiftForward)
            self.KPIs['totalIdleTime'] += idleTimeVariation

            # Update traveling distance
            #solution.KPIs['totalTravelingDistance'] += ...

        # Update times slacks
        # BTS of steps from steps[0] (included) to steps[stepIndex - 1] (included) are correct
        # BTS of steps following steps[stepIndex] (included) must be updated
        self.updateBTSForwardFrom(stepIndex)
        # FTS of steps from steps[-1] (included) to steps[stepIndex + 1] (included) are correct
        # FTS of steps preceding steps[stepIndex] (included) must be updated
        self.updateFTSBackwardFrom(stepIndex)
        if tightenTimes:
            self.tightenTimes(updateKPIs)

        # Return indices of the range of steps which startTime has been changed
        return timeChangeFirstIndex, timeChangeLastIndex


    # Assumption: sequence of times is supposed to be correct
    def _replaceStepByTask(self, task: Task, stepIndex, startTime, updateKPIs = True):
        print("To do")



    #---------------------------#
    # Local change - Infeasible #
    #---------------------------#


    def _infeasiblyInsertTaskAt(self, task: Task, stepIndex, startTime, startTimeForBackward, startTimeForForward):

        # Initialize indices of the range of steps which startTime has been changed
        timeChangeFirstIndex = stepIndex
        timeChangeLastIndex = stepIndex

        # Insert step
        insertedStep = StepForLS(activity = task, arrivalTime = startTime, startTime = startTime, endTime = startTime + task.duration)
        self.steps.insert(stepIndex, insertedStep)

        # Update times before insertion
        stepBeforeInsertion = self.steps[stepIndex - 1]
        travelingDurationBefore = self.instance.computeTravelingDuration(stepBeforeInsertion.activity, task)
        stepBeforeInsertionStartTime = startTimeForBackward - (travelingDurationBefore + stepBeforeInsertion.activity.duration)
        if stepBeforeInsertionStartTime < stepBeforeInsertion.startTime:
            timeChangeFirstIndex = self.shiftTimesBackwardFrom(stepIndex = stepIndex - 1, startTime = stepBeforeInsertionStartTime)
            insertedStep.arrivalTime = startTimeForBackward
        else:
            insertedStep.arrivalTime = stepBeforeInsertion.endTime + travelingDurationBefore

        # Update times after insertion
        stepAfterInsertion = self.steps[stepIndex + 1]
        travelingDurationAfter = self.instance.computeTravelingDuration(task, stepAfterInsertion.activity)
        stepAfterInsertionArrivalTime = startTimeForForward + task.duration + travelingDurationAfter
        stepAfterInsertion.arrivalTime = stepAfterInsertionArrivalTime
        if stepAfterInsertion.startTime < stepAfterInsertionArrivalTime:
            timeChangeLastIndex = self.shiftTimesForwardFrom(stepIndex = stepIndex + 1, startTime = stepAfterInsertionArrivalTime)

        # Return indices of the range of steps which startTime has been changed
        return timeChangeFirstIndex, timeChangeLastIndex



#######################
# Class SolutionForLS #
#######################


class SolutionForLS(Solution):



    #--------#
    # Basics #
    #--------#


    def __init__(self, instance: Instance, name = None, sequences = None, tasksDescs = None, LBsDescs = None):
        super().__init__(instance, name, sequences, tasksDescs, LBsDescs)


    @classmethod
    def fromSolution(cls, solution: Solution):
        sequences = dict()
        for employeeName, sequence in solution.sequences.items():
            sequences[employeeName] = SequenceForLS.fromSequence(sequence)
        solutionForLS = cls(solution.instance, solution.name, sequences, solution._copyTasksDescs(), solution._copyLBsDescs())
        solutionForLS.KPIs = solution._copyKPIs()
        return solutionForLS


    def copy(self, copyName = None):
        name = self.name if copyName == None else copyName
        solution = SolutionForLS(self.instance, name, self._copySequences(), self._copyTasksDescs(), self._copyLBsDescs())
        solution.KPIs = self._copyKPIs()
        return solution



    #------------------------#
    # Times and times slacks #
    #------------------------#

    # Assumptions:
    # - no lunch breaks;
    # - no tasks unavailabilities.


    def updateTimeSlacks(self):
        for sequence in self.sequences.values():
            sequence.updateTimeSlacks()


    def tightenTimes(self, updateKPIs = True):
        for sequence in self.sequences.values():
            formerSequenceIdleTime = sequence.getKPI('totalIdleTime')
            sequence.tightenTimes(updateKPIs)
            if updateKPIs:
                self.KPIs['totalIdleTime'] += sequence.getKPI('totalIdleTime') - formerSequenceIdleTime



    #--------------#
    # Local change #
    #--------------#


    def _setTaskDescToNonrealized(self, task: Task):
        taskDescription = self.tasksDescriptions[task.name]
        taskDescription['realized'] = False
        del taskDescription['employeeName']
        del taskDescription['startTime']


    def _setTaskDescToRealized(self, task: Task, employee: Employee, startTime):
        taskDescription = self.tasksDescriptions[task.name]
        taskDescription['realized'] = True
        taskDescription['employeeName'] = employee.name
        taskDescription['startTime'] = startTime



    #-------------------------#
    # Local change - Feasible #
    #-------------------------#


    # Assumption: solution.sequences[employeeName][stepIndex] is a task
    def _removeStep(self, employee: Employee, stepIndex, tightenTimes = True, updateKPIs = True):

        assert self.getSequence(employee.name)[stepIndex].activity.isTask(), \
            f"Removed step {self.getSequence(employee.name)[stepIndex].activity} is not a task"

        # Get sequence
        sequence = self.getSequence(employee.name)
        sequenceFormerKPIs = sequence.getKPIs()

        # Pop step
        removedStep = sequence._popStep(stepIndex, tightenTimes, updateKPIs)
        self._setTaskDescToNonrealized(removedStep.activity)

        # Update KPIs if needed
        if updateKPIs:
            for KPIKey, sequenceKPIValue in sequenceFormerKPIs.items():
                self.KPIs[KPIKey] += sequence.getKPI(KPIKey) - sequenceKPIValue

        # Clear removed step
        removedStep.clear()


    # def _removeTask(self, task: Task, updateKPIs = True):
    #     realized, employee = self.taskIsRealizedBy(task)
    #     if realized:
    #         stepIndex = self.getSequence(employee.name).getStepIndexOfActivity(task.name)


    # Assumption stepIndex is between 1 (included) and len(sequence) - 1 (included)
    def _insertTaskAt(self, employee: Employee, task: Task, stepIndex, startTime, tightenTimes = True, updateKPIs = True):
        assert not(self.taskIsRealizedBy(task)[0]), f"{task} must be removed from {self.taskIsRealizedBy(task)[1]}'s planning before being inserted"
        sequence = self.getSequence(employee.name)
        sequenceFormerKPIs = sequence.getKPIs()
        assert stepIndex > 0 and stepIndex < len(sequence), f"Step index {stepIndex} must be between 1 and {len(sequence) - 1} included"
        timeChangeFirstIndex, timeChangeLastIndex = sequence._insertTaskAt(task, stepIndex, startTime, tightenTimes, updateKPIs)
        self._setTaskDescToRealized(task, employee, startTime)
        self._updateTimesInTasksDescriptionsForTasksOfStepsInRange(employee, max(timeChangeFirstIndex, 1), min(timeChangeLastIndex, len(sequence) - 2))
        if updateKPIs:
            for KPIKey, sequenceKPIValue in sequenceFormerKPIs.items():
                self.KPIs[KPIKey] += sequence.getKPI(KPIKey) - sequenceKPIValue


    def _replaceStepByTaskAt(self, employee: Employee, task: Task, stepIndex, startTime, tightenTimes = True, updateKPIs = True):
        assert not(self.taskIsRealizedBy(task)[0]), f"{task} must be removed from {self.taskIsRealizedBy(task)[1]}'s planning before being inserted"
        self._removeStep(employee, stepIndex, tightenTimes = False, updateKPIs = updateKPIs)
        self._insertTaskAt(employee, task, stepIndex, startTime, tightenTimes, updateKPIs)


    def _replaceTaskByAnotherAt(self, leavingTask: Task, enteringTask: Task, startTime, tightenTimes = True, updateKPIs = True):
        realized, employee = self.taskIsRealizedBy(leavingTask)
        assert not(realized), f"{leavingTask} must be realized to be replaced by {enteringTask}"
        stepIndex = self.getSequence(employee.name).getStepIndexOfActivity(leavingTask.name)
        self._replaceStepByTaskAt(employee, enteringTask, stepIndex, startTime, tightenTimes, updateKPIs)


    def _replaceSequence(self, employee: Employee, newSequence: SequenceForLS, updateKPIs = True):
        sequence = self.getSequence(employee.name)
        formerSequenceKPIs = sequence.getKPIs()
        for task in sequence.getTasks():
            self._setTaskDescToNonrealized(task)
        self.sequences[employee.name] = newSequence
        for step in newSequence[1:-1]:
            if step.activity.isTask():
                self._setTaskDescToRealized(step.activity, employee, step.startTime)
        if updateKPIs:
            for KPIKey, sequenceKPIValue in formerSequenceKPIs.items():
                self.KPIs[KPIKey] += newSequence.getKPI(KPIKey) - sequenceKPIValue




    #---------------------------#
    # Local change - Infeasible #
    #---------------------------#


    def _infeasiblyInsertTaskAt(self, employee: Employee, task: Task, stepIndex, startTime, startTimeForBackward, startTimeForForward):
        assert not(self.taskIsRealizedBy(task)[0]), f"{task} must be removed from {self.taskIsRealizedBy(task)[1]}'s planning before being inserted"
        sequence = self.getSequence(employee.name)
        timeChangeFirstIndex, timeChangeLastIndex = sequence._infeasiblyInsertTaskAt(task, stepIndex, startTime, startTimeForBackward, startTimeForForward)
        self._setTaskDescToRealized(task, employee, startTime)
        self._updateTimesInTasksDescriptionsForTasksOfStepsInRange(employee, max(timeChangeFirstIndex, 1), min(timeChangeLastIndex, len(sequence) - 2))
        return timeChangeFirstIndex, timeChangeLastIndex


    def _infeasiblyReplaceStepByTaskAt(self, employee: Employee, task: Task, stepIndex, startTime, startTimeForBackward, startTimeForForward):
        assert not(self.taskIsRealizedBy(task)[0]), f"{task} must be removed from {self.taskIsRealizedBy(task)[1]}'s planning before being inserted"
        self._removeStep(employee, stepIndex, tightenTimes = False, updateKPIs = False)
        return self._infeasiblyInsertTaskAt(employee, task, stepIndex, startTime, startTimeForBackward, startTimeForForward)



    #--------------#
    # Local change #
    #--------------#


    def removeTask(self, task: Task, tightenTimes = True, updateKPIs = True):
        realized, employee = self.taskIsRealizedBy(task)
        if realized:
            stepIndex = self.getSequence(employee.name).getStepIndexOfActivity(task.name)
            self._removeStep(employee, stepIndex, tightenTimes = tightenTimes, updateKPIs = updateKPIs)
        else:
            raise ValueError(f"{task} is not realized in this solution {self}")
        return True


    def replaceTaskByAnother(self, leavingTask: Task, enteringTask: Task,
        startTime = None, startTimeForBackward = None, startTimeForForward = None,
        tightenTimes = True, updateKPIs = True):

        # Get employee realizing leaving task
        # and remove entering task from its employee's planning (if any)
        leavingTaskIsRealized, employee = self.activityIsRealizedBy(leavingTask)
        if leavingTaskIsRealized:
            replacingStepIndex = self.getSequence(employee.name).getStepIndexOfActivity(leavingTask.name)
            enteringTaskIsRealized, otherEmployee = self.taskIsRealizedBy(enteringTask)
            if enteringTaskIsRealized:
                removalStepIndex = self.getSequence(otherEmployee.name).getStepIndexOfActivity(enteringTask.name)
                self._removeStep(otherEmployee, removalStepIndex, tightenTimes, updateKPIs)
        else:
            raise ValueError(f"{leavingTask} is not realized in this solution {self}")

        # Find start time (if needed)
        if startTimeForBackward == None:

            if startTime == None:
                print("Not yet coded!")
                return False

            # Replace
            else:
                self._replaceStepByTaskAt(employee, enteringTask, replacingStepIndex, startTime, tightenTimes, updateKPIs)
                return True

        # Replace
        else:
            timeChangeFirstIndex, timeChangeLastIndex = self._infeasiblyReplaceStepByTaskAt(employee, enteringTask, replacingStepIndex, startTime, startTimeForBackward, startTimeForForward)
            return False, timeChangeFirstIndex, timeChangeLastIndex


    def insertTaskAfterActivity(self, task: Task, activity: Activity,
        startTime = None, startTimeForBackward = None, startTimeForForward = None,
        tightenTimes = True, updateKPIs = True):

        assert not(activity.isReturn()), f"{task.name} cannot be inserted after {activity}"

        # Get employee realizing activity
        # and remove (entering) task from its employee's planning (if any)
        activityIsRealized, employee = self.activityIsRealizedBy(activity)
        insertionStepIndex = -1
        if activityIsRealized:
            insertionStepIndex = self.getSequence(employee.name).getStepIndexOfActivity(activity.name) + 1
            taskIsRealized, otherEmployee = self.taskIsRealizedBy(task)
            if taskIsRealized:
                removalStepIndex = self.getSequence(otherEmployee.name).getStepIndexOfActivity(task.name)
                self._removeStep(otherEmployee, removalStepIndex, tightenTimes, updateKPIs)
        else:
            raise ValueError(f"{activity} is not realized in this solution {self}")

        # Find start time (if needed)
        if startTimeForBackward == None:

            if startTime == None:
                print("Not yet coded!")
                return False

            # Insert
            else:
                self._insertTaskAt(employee, task, insertionStepIndex, startTime, tightenTimes, updateKPIs)
                return True

        # Insert
        else:
            timeChangeFirstIndex, timeChangeLastIndex = self._infeasiblyInsertTaskAt(employee, task, insertionStepIndex, startTime, startTimeForBackward, startTimeForForward)
            return False, timeChangeFirstIndex, timeChangeLastIndex


    def insertTaskAtAllCosts(self, employee: Employee, task: Task, tightenTimes = True, updateKPIs = True):

        # Remove (entering) task from its employee's planning (if any)
        enteringTaskIsRealized, otherEmployee = self.taskIsRealizedBy(task)
        if enteringTaskIsRealized:
            removalStepIndex = self.getSequence(otherEmployee.name).getStepIndexOfActivity(task.name)
            self._removeStep(otherEmployee, removalStepIndex, tightenTimes, updateKPIs)

        # Create and run model for sequence optimization
        formerSequenceTasks = self.getSequence(employee.name).getTasks()
        selectedTasks = formerSequenceTasks + [task]
        prescribedTasks = [task]
        model = IPModelForSequence(self.instance, employee, selectedTasks, prescribedTasks)
        model.optimize(mute = True)
        #model.optimize(mute = False)
        if not(model.hasSolution()):
            raise Exception(f"Inserting {prescribedTasks} in {employee}'s planning is infeasible")
        newSequence = SequenceForLS.fromSequence(model.getSolutionAsSequence())
        newSequence.updateTimeSlacks()
        if updateKPIs:
            newSequence.updateKPIs()
        if tightenTimes:
            newSequence.tightenTimes(tightenTimes)

        # Replace sequence
        removedTasks = set(formerSequenceTasks).difference(newSequence.getTasks())
        self._replaceSequence(employee, newSequence, updateKPIs)

        return True, removedTasks



    #------------#
    # Looking up #
    #------------#


    # def findBestInsertionInEmployeePlanning(self, employee: Employee, task: Task, tabuIndices = []):
    #     return self.getSequence(employee.name).findBestInsertion(task, tabuIndices)


    def findBestInsertionIfAlone(self, employee: Employee, task: Task):
        sequence = self.getSequence(employee.name).copy()
        sequence._removeAllTasks(tightenTimes = False, updateKPIs = False)
        insertionResult = sequence.findBestInsertion(task)
        solution = self.copy()
        solution._replaceSequence(employee, sequence)
        return insertionResult, solution


    def findCriticalStepIndexForwardFrom(self, employee: Employee, task: Task):
        stepIndex = self.getSequence(employee.name).getStepIndexOfActivity(task.name)
        return self.getSequence(employee.name).findCriticalStepIndexForwardFrom(stepIndex)


    def findBestInsertion(self, task: Task):
        insertionResult = dict()
        insertionResult['feasible'] = False
        insertionResult['employee'] = None
        insertionResult['stepIndex'] = None
        insertionResult['startTime'] = None
        insertionResult['travelingDurationVariation'] = None
        insertionResult['late'] = None
        insertionResult['taskSkillLevelTooHigh'] = True
        insertionResult['taskTooFar'] = True
        for employee in self.instance.getEmployees():
            employeeInsertionResult = self.getSequence(employee.name).findBestInsertion(task)
            if employeeInsertionResult['feasible']:
                insertionResult['feasible'] = True
                insertionResult['taskSkillLevelTooHigh'] = False
                if insertionResult['taskTooFar']:
                    insertionResult['taskTooFar'] = False
                    insertionResult['late'] = None
                if insertionResult['travelingDurationVariation'] == None or \
                    employeeInsertionResult['travelingDurationVariation'] < insertionResult['travelingDurationVariation']:
                    insertionResult['employee'] = employee
                    insertionResult['stepIndex'] = employeeInsertionResult['stepIndex']
                    insertionResult['startTime'] = employeeInsertionResult['startTime']
                    insertionResult['travelingDurationVariation'] = employeeInsertionResult['travelingDurationVariation']
            else:
                if not(employeeInsertionResult['taskSkillLevelTooHigh']):
                    insertionResult['taskSkillLevelTooHigh'] = False
                    if employeeInsertionResult['taskTooFar']:
                        if insertionResult['taskTooFar']:
                            if insertionResult['late'] == None or employeeInsertionResult['late'] < insertionResult['late']:
                                insertionResult['employee'] = employee
                                insertionResult['stepIndex'] = employeeInsertionResult['stepIndex']
                                insertionResult['startTime'] = employeeInsertionResult['startTime']
                                insertionResult['travelingDurationVariation'] = employeeInsertionResult['travelingDurationVariation']
                                insertionResult['late'] = employeeInsertionResult['late']
                    else:
                        if insertionResult['taskTooFar']:
                            insertionResult['taskTooFar'] = False
                            insertionResult['late'] = None
                        if insertionResult['late'] == None or employeeInsertionResult['late'] < insertionResult['late']:
                            insertionResult['employee'] = employee
                            insertionResult['stepIndex'] = employeeInsertionResult['stepIndex']
                            insertionResult['startTime'] = employeeInsertionResult['startTime']
                            insertionResult['travelingDurationVariation'] = employeeInsertionResult['travelingDurationVariation']
                            insertionResult['late'] = employeeInsertionResult['late']

        return insertionResult



    #------------#
    # Deprecated #
    #------------#


    # Assumption: stepIndex > 0 and BTS[stepIndex - 1] is computed
    def propagateBTSForwardFrom(self, employeeName, stepIndex):
        print("Deprecated: Solution.propagateBTSForwardFrom is deprecated, use Solution.updateBTSForwardFrom")
        self.sequences[employeeName].updateBTSForwardFrom(stepIndex)


    # Assumption: stepIndex < -1 and FTS[stepIndex + 1] is computed
    def propagateFTSBackwardFrom(self, employeeName, stepIndex):
        print("Deprecated: Solution.propagateFTSBackwardFrom is deprecated, use Solution.updateFTSForwardFrom")
        self.sequences[employeeName].updateFTSBackwardFrom(stepIndex)


    def computeTimeSlacks(self):
        print("Deprecated: Solution.computeTimeSlacks is deprecated, use Solution.updateTimeSlacks")
        # for employeeName, sequence in self.sequences.items():
        #     sequence.updateTimeSlacks(self.instance.getEmployee(employeeName))
        for sequence in self.sequences.values():
            sequence.updateTimeSlacks()
