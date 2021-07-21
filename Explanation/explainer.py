###########
# Modules #
###########


# Basic modules
import re


# Project modules
from Optimization.solution_for_LS import *
from Optimization.local_change import *
from Tools.global_variables import *



#####################
# Class Explanation #
#####################


class Explanation:

    text = None
    newSolution = None
    feasible = False
    infeasibility = None
    criticalBounds = None

    def __init__(self, text, newSolution = None, feasible = False, infeasibility = None, criticalBounds = None):
        self.text = text
        self.newSolution = newSolution
        self.feasible = feasible
        self.infeasibility = infeasibility
        self.criticalBounds = criticalBounds

    def hasANewSolution(self):
        return self.newSolution != None

    def newSolutionIsFeasible(self):
        return self.hasANewSolution and self.feasible



###################
# Class Explainer #
###################


class Explainer:


    def __init__(self, solution = None):
        self.currentSolution = solution.copy()
        self.currentSolution.name += "_0"
        self.solutionsHistory = dict()
        self.solutionsHistory[self.currentSolution.name] = self.currentSolution
        self.templatesKeys = ["RealizingInsteadOf", "RealizingJustAfter", "RealizingInAddition", "RealizingAtAnotherTime", \
            "NotRealized", "RealizingAtAllCosts"] #, "Tightening"
        self.templates = dict()
        self.addTemplate("RealizingInsteadOf", "Why employee {0} does not realize task {1} instead of the task {2}?") # AOTRSO
        self.addTemplate("RealizingJustAfter", "Why employee {0} does not realize task {1} just after the activity {2}?") # AOTRSO
        self.addTemplate("RealizingInAddition", "Why employee {0} does not realize task {1} in addition to his/her tasks?") # AOTRSO
        self.addTemplate("RealizingAtAnotherTime", "Why employee {0} does not realize task {1} at another time in his/her planning?") # AOTRSO
        self.addTemplate("NotRealized", "Why task {1} is not realized in addition to the other tasks?") # AOTRSO
        self.addTemplate("RealizingAtAllCosts", "What if employee {0} realizes task {1}?")
        # self.addTemplate("Realizing", "Why employee {0} does realize task {1}?")
        # self.addTemplate("NotRealized", "Why task {1} is not realized?")
        #self.addTemplate("Tightening", "Can you tighten the plannings please?")



    #--------------------#
    # Template questions #
    #--------------------#


    def addTemplate(self, templateKey, template):
        self.templates[templateKey] = (template, template.count('{'))

    def getTemplatesTexts(self):
        return [self.templates[key][0] for key in self.templatesKeys]

    def getTemplateText(self, index = None, key = None):
        if index != None:
            return self.templates[self.templatesKeys[index]][0]
        elif key != None:
            return self.templates[key][0]
        else:
            print("There is something wrong with the template text")

    def getTemplateNbFields(self, index = None, key = None):
        if index != None:
            return self.templates[self.templatesKeys[index]][1]
        elif key != None:
            return self.templates[key][1]
        else:
            print("There is something wrong with the template nb of fields")



    #------------------#
    # Solution history #
    #------------------#


    def setCurrentSolution(self, solutionName):
        self.currentSolution = self.solutionsHistory[solutionName]


    def saveNewSolutionInHistory(self, newSolution):
        nbSolutions = len(self.solutionsHistory)
        newSolution.name = newSolution.name.replace("_New", f"_{nbSolutions}")
        self.solutionsHistory[newSolution.name] = newSolution



    #------------------------#
    # Comparison computation #
    #------------------------#


    def compareSolutions(self, solution1, solution2):
        KPIs1 = solution1.getKPIs()
        KPIs2 = solution2.getKPIs()
        KPIsDescs = dict()
        KPIsDescs['nbRealizedTasks'] = {'sense': 'max', 'fullName': "number of realized tasks", 'unit': ""}
        KPIsDescs['totalWorkingDuration'] = {'sense': 'max', 'fullName': "total working duration", 'unit': "min"}
        KPIsDescs['totalTravelingDuration'] = {'sense': 'min', 'fullName': "total traveling duration", 'unit': "min"}
        KPIsDescs['totalIdleTime'] = {'sense': 'min', 'fullName': "total idle time", 'unit': "min"}
        text = f"Choosing {solution2.name} instead of {solution1.name} implies that:" + lineBreakSymbol
        for key, desc in KPIsDescs.items():
            sense = 1 if KPIsDescs[key]['sense'] == 'max' else -1
            feedback = ""
            if (KPIs2[key] - KPIs1[key])*sense > 0:
                feedback = "(+)"
            elif (KPIs2[key] - KPIs1[key])*sense == 0:
                feedback = "(=)"
            else:
                feedback = "(-)"
            variation = KPIs2[key] - KPIs1[key]
            trend = ""
            if variation > 0:
                trend = "increases"
            elif variation < 0:
                trend = "decreases"
            if trend == "":
                text += f"{feedback} the {KPIsDescs[key]['fullName']} stays the same;"
            else:
                text += f"{feedback} the {KPIsDescs[key]['fullName']} {trend} by {abs(variation)}{KPIsDescs[key]['unit']};"
            text += lineBreakSymbol
        text = text[: -len(lineBreakSymbol) - 1] + "."
        return text



    #-----------------------------------#
    # Explanation computation - General #
    #-----------------------------------#


    def computeExplanationByIndex(self, templateIndex, fieldsValues):
        return self.computeExplanationByKey(self.templatesKeys[templateIndex], fieldsValues)


    def computeExplanationByKey(self, templateKey, fieldsValues):
        if templateKey == "RealizingInsteadOf":
            employeeName = fieldsValues[0]
            enteringTaskName = fieldsValues[1]
            leavingTaskName = fieldsValues[2]
            explanation = self.computeExplanationAboutRealizingInsteadOf(employeeName, enteringTaskName, leavingTaskName)
        elif templateKey == "RealizingJustAfter":
            employeeName = fieldsValues[0]
            taskName = fieldsValues[1]
            beforeInsertionActivityName = fieldsValues[2]
            explanation = self.answerQuestionAboutInsertingAfter(employeeName, taskName, beforeInsertionActivityName)
        elif templateKey == "RealizingInAddition":
            employeeName = fieldsValues[0]
            enteringTaskName = fieldsValues[1]
            explanation = self.answerQuestionAboutRealizingInAddition(employeeName, enteringTaskName)
        elif templateKey == "RealizingAtAnotherTime":
            employeeName = fieldsValues[0]
            taskName = fieldsValues[1]
            explanation = self.answerQuestionAboutRealizingAtAnotherTime(employeeName, taskName)
        elif templateKey == "NotRealized":
            taskName = fieldsValues[1]
            explanation = self.answerQuestionAboutWhyTaskIsNotRealized(taskName)
        elif templateKey == "RealizingAtAllCosts":
            employeeName = fieldsValues[0]
            enteringTaskName = fieldsValues[1]
            explanation = self.answerQuestionAboutRealizingAtAllCosts(employeeName, enteringTaskName)
        elif templateKey == "Tightening":
            explanation = self.answerQuestionAboutTightening()
        else:
            explanation = Explanation("Not yet coded but thank you for your interest ;)")
        return explanation



    #----------------------------------------------------#
    # Explanation computation - Realizing - One employee #
    #----------------------------------------------------#


    def _commentInsertionBetweenTwoSteps(self, employee: Employee, insertedTask: Task, stepBeforeIndex, stepAfterIndex, nonCurrentSolution = None):

        # Define useful variables
        solution = self.currentSolution if nonCurrentSolution == None else nonCurrentSolution
        sequence = solution.getSequence(employee.name)
        stepBefore = sequence[stepBeforeIndex]
        stepAfter = sequence[stepAfterIndex]

        # Initialize returned variables
        insertionIsFeasible = True
        earliestStartTimeOfInsertedTask = None
        text = ""

        # ... Check start-to-inserted-task feasibility
        earliestStartTimeOfInsertedTask = max(insertedTask.startTime,
            stepBefore.startTime - stepBefore.BTS + stepBefore.activity.duration + \
            self.currentSolution.instance.computeTravelingDuration(stepBefore.activity, insertedTask))
        if earliestStartTimeOfInsertedTask + insertedTask.duration > insertedTask.endTime:
            insertionIsFeasible = False
            if stepBeforeIndex == 0:
                text += f"By realizing {insertedTask.name} after leaving {stepBefore.activity.name} at the earliest possible, "
            elif stepBeforeIndex == 1:
                text += f"By realizing {stepBefore.activity.name} and {insertedTask.name} at the earliest possible, "
            else:
                text += f"By realizing all the activities before {insertedTask.name} at the earliest possible, "
            text += f"{employee.name} can end {insertedTask.name} at {convert_nb_minutes_to_time_string(earliestStartTimeOfInsertedTask + insertedTask.duration)} at the earliest, "
            text += f"while {insertedTask.name} must be ended by {convert_nb_minutes_to_time_string(insertedTask.endTime)}. "

        # ... Check entering-task-to-end feasibility
        else:
            earliestStartTimeOfStepAfter = max(stepAfter.activity.startTime,
                earliestStartTimeOfInsertedTask + insertedTask.duration + self.currentSolution.instance.computeTravelingDuration(insertedTask, stepAfter.activity))
            if earliestStartTimeOfStepAfter > stepAfter.startTime + stepAfter.FTS:
                insertionIsFeasible = False
                text += f"By realizing all the activities before {stepAfter.activity.name} at the earliest possible, "
                if stepAfterIndex == len(sequence) - 1:
                    text += f"{employee.name} can be at {stepAfter.activity.name} at {convert_nb_minutes_to_time_string(earliestStartTimeOfStepAfter)} at the earliest, "
                    text += f"while he/she must be there by {convert_nb_minutes_to_time_string(stepAfter.activity.endTime)}."
                elif stepAfter.activity.isUnavailability():
                    text += f"{employee.name} can start {stepAfter.activity.name} at {convert_nb_minutes_to_time_string(earliestStartTimeOfStepAfter)} at the earliest, "
                    text += f"while he/she must start it at {convert_nb_minutes_to_time_string(sequence[stepAfterIndex].activity.startTime)}."
                else:
                    text += f"{employee.name} can start {stepAfter.activity.name} at {convert_nb_minutes_to_time_string(earliestStartTimeOfStepAfter)} at the earliest, "
                    text += f"while {stepAfter.activity.name} must be started at {convert_nb_minutes_to_time_string(stepAfter.startTime + stepAfter.FTS)} at the latest "
                    text += f"in order to allow him/her "
                    criticalStepIndex = sequence.findCriticalStepIndexForwardFrom(stepAfterIndex)
                    criticalStep = sequence[criticalStepIndex]
                    if criticalStepIndex == stepAfterIndex:
                        text += f"to end it before {convert_nb_minutes_to_time_string(stepAfter.activity.endTime)}."
                    elif criticalStepIndex < len(sequence) - 1:
                        if criticalStep.activity.isUnavailability():
                            text += f"to start {criticalStep.activity.name} at {convert_nb_minutes_to_time_string(criticalStep.activity.startTime)}."
                        else:
                            text += f"to end {criticalStep.activity.name} before {convert_nb_minutes_to_time_string(criticalStep.activity.endTime)}."
                    else:
                        text += f"to be at {sequence[-1].activity.name} by {convert_nb_minutes_to_time_string(sequence[-1].activity.endTime)}."

        return insertionIsFeasible, earliestStartTimeOfInsertedTask, text


    # Assumption: fields are corrects
    def computeExplanationAboutRealizingInsteadOf(self, employeeName, enteringTaskName, leavingTaskName):

        # Define variables
        employee = self.currentSolution.instance.getEmployee(employeeName)
        sequence = self.currentSolution.getSequence(employee.name)
        enteringTask = self.currentSolution.instance.getTask(enteringTaskName)
        leavingTask = self.currentSolution.instance.getTask(leavingTaskName)
        leavingTaskIndex = sequence.getStepIndexOfActivity(leavingTaskName)

        # Get steps before and after replacement
        stepBeforeReplacement = sequence[leavingTaskIndex - 1]
        stepIndexAfterReplacement = leavingTaskIndex + 1
        stepAfterReplacement = sequence[leavingTaskIndex + 1]

        # Check skill level
        text = ""
        if employee.skillLevel < enteringTask.skillLevel:
            text = f"{employee.name} does not have enough skills to do {enteringTaskName}," + lineBreakSymbol
            text += f"therefore {employee.name} can not do {enteringTaskName} instead of {leavingTaskName}."
            return Explanation(text)

        # Observe insertion between steps before and after replacement
        sequenceIsFeasible, earliestStartTimeOfEnteringTask, insertionText = self._commentInsertionBetweenTwoSteps(employee,
            insertedTask = enteringTask, stepBeforeIndex = leavingTaskIndex - 1, stepAfterIndex = leavingTaskIndex + 1)

        # Check sequence
        if not(sequenceIsFeasible):
            infeasibleSolution = self.currentSolution.copy(re.sub(r"_.+", "_Infeasible", self.currentSolution.name))
            startTimeForBackward = earliestStartTimeOfEnteringTask
            startTimeForForward = stepAfterReplacement.startTime + stepAfterReplacement.FTS - \
                (self.currentSolution.instance.computeTravelingDuration(enteringTask, stepAfterReplacement.activity) + enteringTask.duration)
            startTime = startTimeForBackward
            _, timeChangeFirstIndex, timeChangeLastIndex = infeasibleSolution.replaceTaskByAnother(leavingTask, enteringTask,
                startTime, startTimeForBackward, startTimeForForward, tightenTimes = False, updateKPIs = False)
            text = f"Let assume that {enteringTask.name} is put in {employee.name}'s planning instead of {leavingTask.name}." + lineBreakSymbol
            text += insertionText + lineBreakSymbol
            text += f"Therefore {employee.name} can not do {enteringTask.name} instead of {leavingTask.name}."
            infeasibility = {'employeeName': employeeName, 'taskName': enteringTaskName}
            # TEMP
            criticalBounds = None
            if not('must be ended by' in insertionText):
                criticalLBIndex = infeasibleSolution.getSequence(employee.name).findCriticalStepIndexBackwardFrom(leavingTaskIndex - 1)
                criticalUBIndex = infeasibleSolution.getSequence(employee.name).findCriticalStepIndexForwardFrom(leavingTaskIndex + 1)
                criticalBounds = {employeeName: {infeasibleSolution.getSequence(employee.name)[criticalLBIndex].activity.name: "LB",
                    infeasibleSolution.getSequence(employee.name)[criticalUBIndex].activity.name: "UB"}}
            return Explanation(text, infeasibleSolution, feasible = False, infeasibility = infeasibility, criticalBounds = criticalBounds)

        # Compute new solution
        text = f"{employee.name} can actually do {enteringTaskName} instead of {leavingTaskName}." + lineBreakSymbol
        newSolution = self.currentSolution.copy(re.sub(r"_.+", "_New", self.currentSolution.name))
        newSolution.replaceTaskByAnother(leavingTask, enteringTask, startTime = earliestStartTimeOfEnteringTask, tightenTimes = True, updateKPIs = True)
        newSolution.updateKPIs()
        comparisonText = self.compareSolutions(self.currentSolution, newSolution)
        text += comparisonText.replace(self.currentSolution.name, "the former solution").replace(newSolution.name, "the new solution")
        return Explanation(text, newSolution, feasible = True)


    def answerQuestionAboutInsertingAfter(self, employeeName, enteringTaskName, beforeInsertionActivityName):

        # Get employee, sequence and entering task
        employee = self.currentSolution.instance.getEmployee(employeeName)
        sequence = self.currentSolution.getSequence(employee.name)
        enteringTask = self.currentSolution.instance.getTask(enteringTaskName)

        # Get steps before and after insertion
        beforeInsertionActivity = self.currentSolution.instance.getActivity(beforeInsertionActivityName, employeeName)
        beforeInsertionActivityIndex = sequence.getStepIndexOfActivity(beforeInsertionActivity.name)
        stepBeforeInsertion = sequence[beforeInsertionActivityIndex]
        stepAfterInsertion = sequence[beforeInsertionActivityIndex + 1]

        # Check skill level
        text = ""
        if employee.skillLevel < enteringTask.skillLevel:
            text = f"{employee.name} does not have enough skills to do {enteringTaskName}," + lineBreakSymbol
            text += f"therefore {employee.name} can not do {enteringTaskName} after {beforeInsertionActivityName}."
            return Explanation(text)

        # Observe insertion between steps before and after insertion
        sequenceIsFeasible, earliestStartTimeOfEnteringTask, insertionText = self._commentInsertionBetweenTwoSteps(employee,
            insertedTask = enteringTask, stepBeforeIndex = beforeInsertionActivityIndex, stepAfterIndex = beforeInsertionActivityIndex + 1)

        # Check sequence
        if not(sequenceIsFeasible):
            infeasibleSolution = self.currentSolution.copy(re.sub(r"_.+", "_Infeasible", self.currentSolution.name))
            startTimeForBackward = earliestStartTimeOfEnteringTask
            startTimeForForward = stepAfterInsertion.startTime + stepAfterInsertion.FTS - \
                (self.currentSolution.instance.computeTravelingDuration(enteringTask, stepAfterInsertion.activity) + enteringTask.duration)
            startTime = startTimeForBackward
            _, timeChangeFirstIndex, timeChangeLastIndex = infeasibleSolution.insertTaskAfterActivity(enteringTask, beforeInsertionActivity,
                startTime, startTimeForBackward, startTimeForForward, tightenTimes = False, updateKPIs = False)
            text = f"Let assume that {enteringTask.name} is put in {employee.name}'s planning just after {stepBeforeInsertion.activity.name}." + lineBreakSymbol
            text += insertionText + lineBreakSymbol
            text += f"Therefore {employee.name} can not do {enteringTask.name} just after {stepBeforeInsertion.activity.name}"
            infeasibility = {'employeeName': employeeName, 'taskName': enteringTaskName}
            # TEMP
            criticalBounds = None
            if not("must be ended by" in insertionText):
                criticalLBIndex = infeasibleSolution.getSequence(employee.name).findCriticalStepIndexBackwardFrom(beforeInsertionActivityIndex)
                criticalUBIndex = infeasibleSolution.getSequence(employee.name).findCriticalStepIndexForwardFrom(beforeInsertionActivityIndex + 2)
                criticalBounds = {employeeName: {infeasibleSolution.getSequence(employee.name)[criticalLBIndex].activity.name: "LB",
                    infeasibleSolution.getSequence(employee.name)[criticalUBIndex].activity.name: "UB"}}
            return Explanation(text, infeasibleSolution, feasible = False, infeasibility = infeasibility, criticalBounds = criticalBounds)

        # Compute new solution
        else:
            text = f"{employee.name} can actually do {enteringTaskName} just after {beforeInsertionActivityName}." + lineBreakSymbol
            newSolution = self.currentSolution.copy(re.sub(r"_.+", "_New", self.currentSolution.name))
            newSolution.insertTaskAfterActivity(enteringTask, beforeInsertionActivity, startTime = earliestStartTimeOfEnteringTask, tightenTimes = True, updateKPIs = True)
            newSolution.updateKPIs()
            comparisonText = self.compareSolutions(self.currentSolution, newSolution)
            text += comparisonText.replace(self.currentSolution.name, "the former solution").replace(newSolution.name, "the new solution")
            return Explanation(text, newSolution, feasible = True)


    def answerQuestionAboutRealizingInAddition(self, employeeName, enteringTaskName):

        # Define variables
        employee = self.currentSolution.instance.getEmployee(employeeName)
        sequence = self.currentSolution.getSequence(employee.name)
        enteringTask = self.currentSolution.instance.getTask(enteringTaskName)

        # Check skill level
        if employee.skillLevel < enteringTask.skillLevel:
            text = f"{employee.name} does not have enough skills to do {enteringTask.name}," + lineBreakSymbol
            text += f"therefore {employee.name} can not do {enteringTask.name} in addition to the tasks of his/her planning."
            return Explanation(text)

        # Find best insertion
        insertionResult = sequence.findBestInsertion(enteringTask)
        insertionIsFeasible = insertionResult['feasible']
        insertionIndex = insertionResult['stepIndex']
        earliestStartTimeOfEnteringTask = insertionResult['startTime']
        taskCannotBeReachedOnTime = insertionResult['taskTooFar']
        # insertionIsFeasible, insertionIndex, earliestStartTimeOfEnteringTask, taskCannotBeReachedOnTime = self.currentSolution.find_BestInsertionInEmployeePlanning(employee, enteringTask)

        # If insertion is infeasible
        if not(insertionIsFeasible):

            # Observe insertion between steps before and after insertion
            stepBeforeInsertion = sequence[insertionIndex - 1]
            stepAfterInsertion = sequence[insertionIndex]
            _, earliestStartTimeOfEnteringTask, insertionText = self._commentInsertionBetweenTwoSteps(employee,
                insertedTask = enteringTask, stepBeforeIndex = insertionIndex - 1, stepAfterIndex = insertionIndex)
            text = ""

            # Define explanation text when infeasibility is simply due to going to the task
            if taskCannotBeReachedOnTime:
                text = f"Let assume that {enteringTask.name} is inserted in {employee.name}'s between {stepBeforeInsertion.activity.name} and {stepAfterInsertion.activity.name}." + lineBreakSymbol
                text += insertionText + lineBreakSymbol
                text += f"Inserting {enteringTask.name} later in {employee.name}'s planning can only lead to a later ending time." + lineBreakSymbol
                text += f"Therefore {employee.name} can not do {enteringTask.name} in addition to the tasks of his/her planning."

            # Define explanation text when infeasibility is simply due to going to the task Infeasibility of any insertion
            else:
                earliestStartTimeOfStepAfterInsertion = max(stepAfterInsertion.activity.startTime,
                    earliestStartTimeOfEnteringTask + enteringTask.duration + self.currentSolution.instance.computeTravelingDuration(enteringTask, stepAfterInsertion.activity))
                text = f"All insertions of {enteringTask.name} in {employee.name}'s planning have been tested and none of them are feasible." + lineBreakSymbol
                text += f"For instance, one of the nearest solutions to feasibility is obtained by inserting {enteringTask.name} "
                text += f"in {employee.name}'s planning between {stepBeforeInsertion.activity.name} and {stepAfterInsertion.activity.name}. " + lineBreakSymbol
                text += f"Let assume that {enteringTask.name} is inserted this way. "
                text += insertionText + " "
                text += f"Therefore {employee.name} can not do {enteringTask.name} between {stepBeforeInsertion.activity.name} and {stepAfterInsertion.activity.name}." + lineBreakSymbol
                text += f"More generally, {employee.name} can not do {enteringTask.name} in addition to the tasks of his/her planning."

            infeasibleSolution = self.currentSolution.copy(re.sub(r"_.+", "_Infeasible", self.currentSolution.name))
            startTimeForBackward = earliestStartTimeOfEnteringTask
            startTimeForForward = stepAfterInsertion.startTime + stepAfterInsertion.FTS - \
                (self.currentSolution.instance.computeTravelingDuration(enteringTask, stepAfterInsertion.activity) + enteringTask.duration)
            startTime = startTimeForBackward
            _, timeChangeFirstIndex, timeChangeLastIndex = infeasibleSolution.insertTaskAfterActivity(enteringTask, stepBeforeInsertion.activity,
                startTime, startTimeForBackward, startTimeForForward, tightenTimes = False, updateKPIs = False)
            infeasibility = {'employeeName': employeeName, 'taskName': enteringTaskName}
            # TEMP
            criticalBounds = None
            if not("must be ended by" in insertionText):
                criticalLBIndex = infeasibleSolution.getSequence(employee.name).findCriticalStepIndexBackwardFrom(insertionIndex - 1)
                criticalUBIndex = infeasibleSolution.getSequence(employee.name).findCriticalStepIndexForwardFrom(insertionIndex + 1)
                criticalBounds = {employeeName: {infeasibleSolution.getSequence(employee.name)[criticalLBIndex].activity.name: "LB",
                    infeasibleSolution.getSequence(employee.name)[criticalUBIndex].activity.name: "UB"}}
            criticalBounds = {employeeName: {infeasibleSolution.getSequence(employee.name)[criticalLBIndex].activity.name: "LB",
                infeasibleSolution.getSequence(employee.name)[criticalUBIndex].activity.name: "UB"}}
            return Explanation(text, infeasibleSolution, feasible = False, infeasibility = infeasibility, criticalBounds = criticalBounds)

        # Compute new solution
        else:
            stepBeforeInsertion = sequence[insertionIndex - 1]
            text = f"{employee.name} can actually do {enteringTaskName} in addition to the tasks of his/her planning by inserting it after {stepBeforeInsertion.activity.name}." + lineBreakSymbol
            newSolution = self.currentSolution.copy(re.sub(r"_.+", "_New", self.currentSolution.name))
            newSolution.insertTaskAfterActivity(enteringTask, stepBeforeInsertion.activity, startTime = earliestStartTimeOfEnteringTask, tightenTimes = True, updateKPIs = True)
            newSolution.updateKPIs()
            comparisonText = self.compareSolutions(self.currentSolution, newSolution)
            text += comparisonText.replace(self.currentSolution.name, "the former solution").replace(newSolution.name, "the new solution")
            return Explanation(text, newSolution, feasible = True)


    def answerQuestionAboutRealizingAtAnotherTime(self, employeeName, taskName):

        # Define variables
        employee = self.currentSolution.instance.getEmployee(employeeName)
        sequence = self.currentSolution.getSequence(employee.name)
        task = self.currentSolution.instance.getTask(taskName)
        stepIndex = sequence.getStepIndexOfActivity(task.name)

        # Create new solution
        newSolution = self.currentSolution.copy(re.sub(r"_.+", "_New", self.currentSolution.name))
        newSolution.removeTask(task, tightenTimes = False, updateKPIs = True)
        newSequence = newSolution.getSequence(employee.name)

        # Find best insertion with tabu index
        insertionResult = newSequence.findBestInsertion(task, tabuIndices = [stepIndex])
        insertionIsFeasible = insertionResult['feasible']
        insertionIndex = insertionResult['stepIndex']
        earliestStartTimeOfEnteringTask = insertionResult['startTime']

        # If insertion is infeasible
        if not(insertionIsFeasible):

            # Observe insertion between steps before and after insertion
            stepBeforeInsertion = newSequence[insertionIndex - 1]
            stepAfterInsertion = newSequence[insertionIndex]
            _, newEarliestStartTimeOfEnteringTask, insertionText = self._commentInsertionBetweenTwoSteps(employee,
                insertedTask = task, stepBeforeIndex = insertionIndex - 1, stepAfterIndex = insertionIndex, nonCurrentSolution = newSolution)
            text = ""
            assert newEarliestStartTimeOfEnteringTask == earliestStartTimeOfEnteringTask, "Hmmm weird!"

            # Define explanation text when infeasibility is simply due to going to the task infeasibility of any insertion other than the tabu one
            earliestStartTimeOfStepAfterInsertion = max(stepAfterInsertion.activity.startTime,
                earliestStartTimeOfEnteringTask + task.duration + self.currentSolution.instance.computeTravelingDuration(task, stepAfterInsertion.activity))
            text = f"All insertions of {task.name} in {employee.name}'s planning have been tested and none of them are feasible." + lineBreakSymbol
            text += f"For instance, one of the nearest solutions to feasibility is obtained by inserting {task.name} "
            text += f"in {employee.name}'s planning between {stepBeforeInsertion.activity.name} and {stepAfterInsertion.activity.name}. " + lineBreakSymbol
            text += f"Let assume that {task.name} is inserted this way. "
            text += insertionText + " "
            text += f"Therefore {employee.name} can not do {task.name} between {stepBeforeInsertion.activity.name} and {stepAfterInsertion.activity.name}." + lineBreakSymbol
            text += f"More generally, {employee.name} can not do {task.name} at another time in his/her planning."

            startTimeForBackward = earliestStartTimeOfEnteringTask
            startTimeForForward = stepAfterInsertion.startTime + stepAfterInsertion.FTS - self.currentSolution.instance.computeTravelingDuration(task, stepAfterInsertion.activity) - task.duration
            startTime = startTimeForBackward
            newSolution.insertTaskAfterActivity(task, stepBeforeInsertion.activity, startTime, startTimeForBackward, startTimeForForward, tightenTimes = False, updateKPIs = False)
            infeasibility = {'employeeName': employeeName, 'taskName': task.name}
            return Explanation(text, newSolution, feasible = False, infeasibility = infeasibility)

        # Compute new solution
        else:
            stepBeforeInsertion = newSolution.getSequence(employee.name)[insertionIndex - 1]
            text = f"{employee.name} can actually do {task.name} at another time in his/her planning by like after {stepBeforeInsertion.activity.name}." + lineBreakSymbol
            newSolution.insertTaskAfterActivity(task, stepBeforeInsertion.activity, startTime = earliestStartTimeOfEnteringTask, tightenTimes = True, updateKPIs = True)
            newSolution.updateKPIs()
            comparisonText = self.compareSolutions(self.currentSolution, newSolution)
            text += comparisonText.replace(self.currentSolution.name, "the former solution").replace(newSolution.name, "the new solution")
            return Explanation(text, newSolution, feasible = True)


    def answerQuestionAboutRealizingAtAllCosts(self, employeeName, enteringTaskName):

        # Define variables
        employee = self.currentSolution.instance.getEmployee(employeeName)
        sequence = self.currentSolution.getSequence(employee.name)
        enteringTask = self.currentSolution.instance.getTask(enteringTaskName)

        # Check skill level
        if employee.skillLevel < enteringTask.skillLevel:
            text = f"{employee.name} can not do {enteringTaskName} because he/she does not have enough skills to do it."
            return Explanation(text)

        # If task even alone cannot be affected to employee
        insertionResult, solution = self.currentSolution.findBestInsertionIfAlone(employee, enteringTask)
        insertionIsFeasible = insertionResult['feasible']
        insertionIndex = insertionResult['stepIndex']
        earliestStartTimeOfEnteringTask = insertionResult['startTime']
        taskCannotBeReachedOnTime = insertionResult['taskTooFar']
        #insertionIsFeasible, insertionIndex, earliestStartTimeOfEnteringTask, taskCannotBeReachedOnTime, solution = self.currentSolution.find_BestInsertionIfAlone(employee, enteringTask)
        if not(insertionIsFeasible):

            stepBeforeInsertion = sequence[insertionIndex - 1]
            stepAfterInsertion = sequence[insertionIndex]
            text = f"{employee.name} can not do {enteringTaskName}."
            text += f"Indeed, let assume that {enteringTaskName} is the only task to be in {employee.name}'s planning "
            text += f"and it is inserted between {stepBeforeInsertion.activity.name} and {stepAfterInsertion.activity.name}." + lineBreakSymbol

            # Define explanation text when infeasibility is simply due to going to the task
            if taskCannotBeReachedOnTime:
                text += f"{employee.name} can end {enteringTaskName} at {convert_nb_minutes_to_time_string(earliestStartTimeOfEnteringTask + enteringTask.duration)} at the earliest, "
                text += f"while {enteringTaskName} must be ended at {convert_nb_minutes_to_time_string(enteringTask.endTime)}."

            # Define explanation text when infeasibility is simply due to going to the task Infeasibility of any insertion
            else:
                earliestStartTimeOfStepAfterInsertion = max(stepAfterInsertion.activity.startTime,
                    earliestStartTimeOfEnteringTask + enteringTask.duration + self.currentSolution.instance.computeTravelingDuration(enteringTask, stepAfterInsertion.activity))
                text += f"{employee.name} can start {stepAfterInsertion.activity.name} at {convert_nb_minutes_to_time_string(earliestStartTimeOfStepAfterInsertion)} at the earliest, "
                text += f"while {stepAfterInsertion.activity.name} must be started at {convert_nb_minutes_to_time_string(stepAfterInsertion.startTime + stepAfterInsertion.FTS)} at the latest "
                text += f"to allow {employee.name} to realize {stepAfterInsertion.activity.name} and the following activities." + lineBreakSymbol

            #text += f"Therefore {employee.name} can not do {enteringTaskName} in his/her planning."

            infeasibleSolution = solution
            infeasibleSolution.name = re.sub(r"_.+", "_Infeasible", self.currentSolution.name)
            startTimeForBackward = earliestStartTimeOfEnteringTask
            startTimeForForward = stepAfterInsertion.startTime + stepAfterInsertion.FTS - \
                (self.currentSolution.instance.computeTravelingDuration(enteringTask, stepAfterInsertion.activity) + enteringTask.duration)
            startTime = startTimeForBackward
            infeasibleSolution.insertTaskAfterActivity(enteringTask, stepBeforeInsertion.activity, startTime, startTimeForBackward, startTimeForForward, tightenTimes = False, updateKPIs = False)
            infeasibility = {'employeeName': employeeName, 'taskName': enteringTaskName}
            return Explanation(text, infeasibleSolution, feasible = False, infeasibility = infeasibility)

        # If task alone can be affected to employee
        else:

            newSolution = self.currentSolution.copy(re.sub(r"_.+", "_New", self.currentSolution.name))
            _, removedTasks = newSolution.insertTaskAtAllCosts(employee, enteringTask, tightenTimes = True, updateKPIs = True)
            text = ""
            if len(removedTasks) == 0:
                text += f"It is possible to insert {enteringTaskName} in {employee.name}'s planning while keeping all other tasks realized."
            else:
                text += f"If {enteringTaskName} is inserted in {employee.name}'s planning, "
                text += f"then one or several tasks must be removed." + lineBreakSymbol
                text += f"The solution maximizing the total working duration is obtained by removing the task{'s' if len(removedTasks) > 1 else ''}: "
                for task in removedTasks:
                    text += f"{task.name}, "
                text = text[:-2]
                text += "."
            return Explanation(text, newSolution, feasible = True)


    def answerQuestionAboutTightening(self):
        newSolution = self.currentSolution.copy(re.sub(r"_.+", "_New", self.currentSolution.name))
        newSolution.tightenTimes()
        text = "All plannings are now tightened."
        return Explanation(text, newSolution, feasible = True)



    #-----------------------------------------------------#
    # Explanation computation - Realizing - All employees #
    #-----------------------------------------------------#


    def answerQuestionAboutWhyTaskIsNotRealized(self, taskName):

        # Define variables
        task = self.currentSolution.instance.getTask(taskName)

        # Find best insertion of the task
        insertionResult = self.currentSolution.findBestInsertion(task)

        #
        if not(insertionResult['feasible']):

            if insertionResult['taskSkillLevelTooHigh']:
                return Explanation("Not yet coded but thank you for your interest ;)")

            elif insertionResult['taskTooFar']:
                return Explanation("Not yet coded but thank you for your interest ;)")

            else:

                # Define variables
                employee = insertionResult['employee']
                sequence = self.currentSolution.getSequence(employee.name)
                insertionIndex = insertionResult['stepIndex']
                earliestStartTimeOfEnteringTask = insertionResult['startTime']

                # Observe insertion between steps before and after insertion in best employee's planning
                stepBeforeInsertion = sequence[insertionIndex - 1]
                stepAfterInsertion = sequence[insertionIndex]
                _, newEarliestStartTimeOfEnteringTask, insertionText = self._commentInsertionBetweenTwoSteps(employee,
                    insertedTask = task, stepBeforeIndex = insertionIndex - 1, stepAfterIndex = insertionIndex)
                text = ""
                assert newEarliestStartTimeOfEnteringTask == earliestStartTimeOfEnteringTask, "Hmmm weird!"

                # Define explanation text when infeasibility is simply due to going to the task infeasibility of any insertion other than the tabu one
                earliestStartTimeOfStepAfterInsertion = max(stepAfterInsertion.activity.startTime,
                    earliestStartTimeOfEnteringTask + task.duration + self.currentSolution.instance.computeTravelingDuration(task, stepAfterInsertion.activity))
                text = f"All insertions of {task.name} in all employees' plannings have been tested and none of them are feasible." + lineBreakSymbol
                text += f"For instance, one of the nearest solutions to feasibility is obtained by inserting {task.name} "
                text += f"in {employee.name}'s planning between {stepBeforeInsertion.activity.name} and {stepAfterInsertion.activity.name}. " + lineBreakSymbol
                text += f"Let assume that {task.name} is inserted this way. "
                text += insertionText + " "
                text += f"Therefore {employee.name} can not do {task.name} between {stepBeforeInsertion.activity.name} and {stepAfterInsertion.activity.name}." + lineBreakSymbol
                text += f"And more generally, no employee can do {task.name} in his/her planning."

                infeasibleSolution = self.currentSolution.copy(re.sub(r"_.+", "_Infeasible", self.currentSolution.name))
                startTimeForBackward = earliestStartTimeOfEnteringTask
                startTimeForForward = stepAfterInsertion.startTime + stepAfterInsertion.FTS - self.currentSolution.instance.computeTravelingDuration(task, stepAfterInsertion.activity) - task.duration
                startTime = startTimeForBackward
                infeasibleSolution.insertTaskAfterActivity(task, stepBeforeInsertion.activity, startTime, startTimeForBackward, startTimeForForward, tightenTimes = False, updateKPIs = False)
                infeasibility = {'employeeName': employee.name, 'taskName': task.name}
                return Explanation(text, infeasibleSolution, feasible = False, infeasibility = infeasibility)

        # Compute new solution
        else:
            employee = insertionResult['employee']
            sequence = self.currentSolution.getSequence(employee.name)
            insertionIndex = insertionResult['stepIndex']
            earliestStartTimeOfEnteringTask = insertionResult['startTime']
            stepBeforeInsertion = sequence[insertionIndex - 1]
            text = f"{task.name} can be realized by {employee.name} in addition to the tasks of his/her planning by inserting it after {stepBeforeInsertion.activity.name}."
            newSolution = self.currentSolution.copy(re.sub(r"_.+", "_New", self.currentSolution.name))
            newSolution.insertTaskAfterActivity(task, stepBeforeInsertion.activity, startTime = earliestStartTimeOfEnteringTask, tightenTimes = True, updateKPIs = True)
            return Explanation(text, newSolution, feasible = True)



    #----------------------------------#
    # Explanation computation - Moving #
    #----------------------------------#


    def answerQuestionAboutIntraMovingAfter(self, employeeName, movingTaskName, beforeInsertionActivityName):

        # Define variables
        employee = self.currentSolution.instance.getEmployee(employeeName)
        sequence = self.currentSolution.getSequence(employee.name)
        movingTask = self.currentSolution.instance.getTask(movingTaskName)

        #
        print("To be completed")
        newSolution = self.currentSolution.copy(re.sub(r"_.+", "_New", self.currentSolution.name))
        text = ""

        return Explanation(text, newSolution, feasible = True)



    #--------------------------------#
    # Explanation computation - Swap #
    #--------------------------------#


    def answerQuestionAboutIntraSwapping(self, employeeName, firstTaskName, secondTaskName):

        # Define variables
        employee = self.currentSolution.instance.getEmployee(employeeName)
        sequence = self.currentSolution.getSequence(employee.name)
        firstTask = self.currentSolution.instance.getTask(firstTaskName)
        secondTask = self.currentSolution.instance.getTask(secondTaskName)

        #
        print("To be completed")
        newSolution = self.currentSolution.copy(re.sub(r"_.+", "_New", self.currentSolution.name))
        text = ""

        return Explanation(text, newSolution, feasible = True)
