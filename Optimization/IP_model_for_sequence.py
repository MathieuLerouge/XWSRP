###########
# Modules #
###########


# Basic modules
import gurobipy as grb
from gurobipy import GRB


# Project modules
from Definition.employee import *
from Definition.instance import *
from Definition.solution import *



################################
# Class IPModelForSequenceData #
################################


class IPModelForSequenceData:


    instance = None
    employee = None
    selectedTasksDict = None
    selectedTasks = None
    prescribedTasks = None
    activities = None


    def __init__(self, instance: Instance, employee: Employee, selectedTasks, prescribedTasks):

        self.instance = instance
        self.employee = employee
        self.selectedTasksDict = dict([(task.name, task) for task in selectedTasks])
        self.selectedTasks = selectedTasks
        self.prescribedTasks = prescribedTasks

        self.activities = dict()
        self.activities['DPT'] = Home(employee, start = True)
        for task in selectedTasks:
            self.activities[task.name] = task
        for unavailability in employee.getUnavailabilities():
            self.activities[unavailability.name] = unavailability
        self.activities['RTN'] = Home(employee, start = False)


    def getEmployee(self):
        return self.employee


    def getTask(self, taskKey):
        return self.selectedTasksDict[taskKey]


    def getUnavailability(self, unavailabilityKey):
        return self.employee.getUnavailability(unavailabilityKey)


    def getActivitiesKeys(self, includingDeparture = True, includingReturn = True, includingUnavailabilities = True):
        activitiesKeys = list(self.activities.keys())
        if not(includingDeparture):
            activitiesKeys.remove('DPT')
        if not(includingReturn):
            activitiesKeys.remove('RTN')
        if not(includingUnavailabilities):
            for unavailability in self.employee.getUnavailabilities():
                activitiesKeys.remove(unavailability.name)
        return activitiesKeys


    def getTasksKeys(self, includingPrescribedTasks = True, includingNonPrescribedTasks = True):
        if includingPrescribedTasks:
            if includingNonPrescribedTasks:
                return [task.name for task in self.selectedTasks]
            else:
                return [task.name for task in self.prescribedTasks]
        else:
            if includingNonPrescribedTasks:
                return [task.name for task in self.selectedTasks if not(task in self.prescribedTasks)]
            else:
                return []


    def getPrescribedTasksKeys(self):
        return [task.name for task in self.prescribedTasks]


    def getUnavailabilitiesKeys(self):
        return [unavailability.name for unavailability in self.employee.getUnavailabilities()]


    def getTravelingDuration(self, activityKey1, activityKey2):
        return self.instance.computeTravelingDuration(self.activities[activityKey1], self.activities[activityKey2])





############################
# Class IPModelForSequence #
############################


class IPModelForSequence:


    GRBModel = None
    decisionVariablesT = None
    decisionVariablesU = None
    solutionSequence = None


    def __init__(self, instance: Instance, employee: Employee, selectedTasks, prescribedTasks = []):
        self.data = IPModelForSequenceData(instance, employee, selectedTasks, prescribedTasks)
        self.GRBModel = grb.Model()
        self._addDecisionVariables()
        self._addObjectiveFunction()
        self._addConstraints()



    #--------------------#
    # Decision variables #
    #--------------------#


    def _addDecisionVariables(self):

        # Add T decision variables
        self.decisionVariablesT = self.GRBModel.addVars(self.data.getTasksKeys(), vtype = GRB.INTEGER, name = "T")

        # Add U decision variables
        self.decisionVariablesU = self.GRBModel.addVars(
            [(j, k) for j in self.data.getActivitiesKeys(includingDeparture = True, includingReturn = False)
                for k in self.data.getActivitiesKeys(includingDeparture = False,includingReturn = True) if k != j],
            vtype = GRB.BINARY, name = "U")



    #--------------------#
    # Objective function #
    #--------------------#


    def _addObjectiveFunction(self):

        # Define total working duration expresion
        workingDurationExpression = grb.LinExpr()
        workingDurationExpression.add(
            grb.quicksum(
                [self.decisionVariablesU[j, k]*self.data.getTask(j).duration
                    for j in self.data.getTasksKeys()
                    for k in self.data.getActivitiesKeys(includingDeparture = False) if k != j
                ]
            )
        )

        # Define total traveling duration expresion
        travelingDurationExpression = grb.LinExpr()
        travelingDurationExpression.add(
            grb.quicksum(
                [self.decisionVariablesU[indices]*self.data.getTravelingDuration(activityKey1 = indices[0], activityKey2 = indices[1])
                    for indices in self.decisionVariablesU.keys()])
        )

        # Set objective function expression as a weight sum of sub objective functions
        # self.travelingDurationCoefficient = 1
        # self.workingDurationCoefficient = 10
        # OFExpression = grb.LinExpr()
        # OFExpression += self.workingDurationCoefficient*workingDurationExpression
        # OFExpression += -self.travelingDurationCoefficient*travelingDurationExpression
        # self.GRBModel.setObjective(OFExpression, sense = GRB.MINIMIZE)

        # Set objective function expression as a multi-objective function
        self.GRBModel.ModelSense = GRB.MINIMIZE
        self.GRBModel.setObjectiveN(-workingDurationExpression, 0, 1)
        self.GRBModel.setObjectiveN(travelingDurationExpression, 1, 0)

        self.GRBModel.update()



    #-------------#
    # Constraints #
    #-------------#


    def _addConstraints(self):
        self._addCoveringConstraints()
        self._addFlowConstraints()
        self._addTimeWindowConstraints()
        self._addTimeSequenceConstraints()
        # No skill constraints


    #------------------------#
    # Constraints - Covering #
    #------------------------#


    def _addCoveringConstraints(self):

        # Add constraint about non-prescribed tasks covering
        for j in self.data.getTasksKeys(includingPrescribedTasks = False):
            self.GRBModel.addLConstr(
                grb.quicksum([self.decisionVariablesU[(j, k)] for k in self.data.getActivitiesKeys(includingDeparture = False, includingReturn = True) if k != j]),
                sense = GRB.LESS_EQUAL, rhs = 1,
                name = f"NonPrescribedTaskCoveringConstraint[{j}]"
            )

        # Add constraint about prescribed tasks covering
        for j in self.data.getPrescribedTasksKeys():
            self.GRBModel.addLConstr(
                grb.quicksum([self.decisionVariablesU[(j, k)] for k in self.data.getActivitiesKeys(includingDeparture = False, includingReturn = True) if k != j]),
                sense = GRB.EQUAL, rhs = 1,
                name = f"PrescribedTaskCoveringConstraint[{j}]"
            )

        # Add constraint about unavailabilitues covering
        for j in self.data.getUnavailabilitiesKeys():
            self.GRBModel.addLConstr(
                grb.quicksum([self.decisionVariablesU[(j, k)] for k in self.data.getActivitiesKeys(includingDeparture = False, includingReturn = True) if k != j]),
                sense = GRB.EQUAL, rhs = 1,
                name = f"UnavailabilityCoveringConstraint[{j}]"
            )

        self.GRBModel.update()



    #--------------------#
    # Constraints - Flow #
    #--------------------#


    def _addFlowConstraints(self):

        # Add flow constraint about departure
        self.GRBModel.addLConstr(
            grb.quicksum([self.decisionVariablesU[('DPT', k)] for k in self.data.getActivitiesKeys(includingDeparture = False, includingReturn = True)]),
            sense = GRB.EQUAL, rhs = 1,
            name = f"DepartureConstraint"
        )

        # Add flow constraint about return
        self.GRBModel.addLConstr(
            grb.quicksum([self.decisionVariablesU[(j, 'RTN')] for j in self.data.getActivitiesKeys(includingDeparture = True, includingReturn = False)]),
            sense = GRB.EQUAL, rhs = 1,
            name = f"ReturnConstraint"
        )

        # Add flow constraint at other activitiesKeys
        for k in self.data.getActivitiesKeys(includingDeparture = False, includingReturn = False):
            self.GRBModel.addLConstr(
                grb.quicksum([self.decisionVariablesU[(j, k)] for j in self.data.getActivitiesKeys(includingDeparture = True, includingReturn = False) if j != k]) -
                grb.quicksum([self.decisionVariablesU[(k, j)] for j in self.data.getActivitiesKeys(includingDeparture = False, includingReturn = True) if j != k]),
                sense = GRB.EQUAL, rhs = 0,
                name = f"FlowConstraint[{k}]"
            )

        self.GRBModel.update()


    #---------------------------#
    # Constraints - Time window #
    #---------------------------#


    def _addTimeWindowConstraints(self):

        # Add time windows lower bound constraint
        for j in self.data.getTasksKeys():
            self.GRBModel.addLConstr(
                self.decisionVariablesT[j] - self.data.getTask(j).startTime*\
                grb.quicksum([self.decisionVariablesU[(j, k)] for k in self.data.getActivitiesKeys(includingDeparture = False, includingReturn = True) if k != j]),
                sense = GRB.GREATER_EQUAL, rhs = 0,
                name = f"TimeWindowLBConstraint[{j}]"
            )

        # Add time windows upper bound constraint
        for j in self.data.getTasksKeys():
            self.GRBModel.addLConstr(
                self.decisionVariablesT[j] - (self.data.getTask(j).endTime - self.data.getTask(j).duration)*\
                grb.quicksum([self.decisionVariablesU[(j, k)] for k in self.data.getActivitiesKeys(includingDeparture = False, includingReturn = True) if k != j]),
                sense = GRB.LESS_EQUAL, rhs = 0,
                name = f"TimeWindowUBConstraint[{j}]"
            )

        self.GRBModel.update()



    #-----------------------------#
    # Constraints - Time sequence #
    #-----------------------------#


    def _addTimeSequenceConstraints(self):

        # Add departure-to-first-task time sequence constraint
        for k in self.data.getTasksKeys():
            self.GRBModel.addLConstr(
                self.decisionVariablesT[k] - \
                (self.data.getEmployee().startTime + self.data.getTravelingDuration('DPT', k))*self.decisionVariablesU[('DPT', k)],
                sense = GRB.GREATER_EQUAL, rhs = 0,
                name = f"SequenceDepartureToTaskConstraint[{k}]"
            )

        # Add last-task-to-return time sequence constraint
        for j in self.data.getTasksKeys():
            self.GRBModel.addLConstr(
                self.decisionVariablesT[j] + self.data.getTask(j).duration -
                (self.data.getEmployee().endTime - self.data.getTravelingDuration(j, 'RTN'))*self.decisionVariablesU[(j, 'RTN')] -
                (1 - self.decisionVariablesU[(j, 'RTN')])*self.data.getTask(j).endTime,
                sense = GRB.LESS_EQUAL, rhs = 0,
                name = f"SequenceTaskToReturnConstraint[{j}]"
            )

        # Add task-to-task time sequence constraint
        for j in self.data.getTasksKeys():
            for k in self.data.getTasksKeys():
                if k != j:
                    self.GRBModel.addLConstr(
                        self.decisionVariablesT[j] + self.data.getTask(j).duration +
                        self.data.getTravelingDuration(j, k)*self.decisionVariablesU[(j, k)] -
                        self.decisionVariablesT[k] - (1 - self.decisionVariablesU[(j, k)])*self.data.getTask(j).endTime,
                        sense = GRB.LESS_EQUAL, rhs = 0,
                        name = f"SequenceTaskToTaskConstraint[{j, k}]"
                    )

        # Add task-to-unavailability time sequence constraint
        for j in self.data.getTasksKeys():
            for k in self.data.getUnavailabilitiesKeys():
                self.GRBModel.addLConstr(
                    self.decisionVariablesT[j] + self.data.getTask(j).duration +
                    self.data.getTravelingDuration(j, k)*self.decisionVariablesU[(j, k)] -
                    self.data.getUnavailability(k).startTime - (1 - self.decisionVariablesU[(j, k)])*self.data.getTask(j).endTime,
                    sense = GRB.LESS_EQUAL, rhs = 0,
                    name = f"SequenceTaskToUnavailabilityConstraint[{j, k}]"
                )

        # Add unavailability-to-task time sequence constraint
        for j in self.data.getUnavailabilitiesKeys():
            for k in self.data.getTasksKeys():
                self.GRBModel.addLConstr(
                    self.data.getUnavailability(j).endTime + self.data.getTravelingDuration(j, k)*self.decisionVariablesU[(j, k)] -
                    self.decisionVariablesT[k] - (1 - self.decisionVariablesU[(j, k)])*self.data.getUnavailability(j).endTime,
                    sense = GRB.LESS_EQUAL, rhs = 0,
                    name = f"SequenceUnavailabilityToTaskConstraint[{j, k}]"
                )

        # Add unavailability-to-unavailability time sequence constraint
        for j in self.data.getUnavailabilitiesKeys():
            for k in self.data.getUnavailabilitiesKeys():
                if j != k:
                    self.GRBModel.addLConstr(
                        self.decisionVariablesU[(j, k)],
                        sense = GRB.LEQUAL,
                        rhs = int(self.data.getUnavailability(j).endTime + self.data.getTravelingDuration(j, k) <= self.data.getUnavailability(k).startTime),
                        name = f"SequenceUnavailabilityToUnavailabilityConstraint[{j, k}]"
                    )

        self.GRBModel.update()



    #--------------#
    # Optimization #
    #--------------#


    def optimize(self, mute = True):
        if mute:
            self.GRBModel.params.outputflag = 0
        self.GRBModel.optimize()
        if self.GRBModel.Status == GRB.INFEASIBLE:
            print("IP model is infeasible")
            print("")
        elif self.GRBModel.Status == GRB.UNBOUNDED:
            print("IP model is unbounded")
            print("")
        else:
            if self.GRBModel.Status == GRB.TIME_LIMIT:
                print("IP model solving was stopped as it reached given time limit")
                print("")
            self._extractSequenceSolution()


    def hasSolution(self):
        return not(self.GRBModel.Status in [GRB.INFEASIBLE, GRB.UNBOUNDED])


    def _extractSequenceSolution(self):

        # Create a list of steps and start times and order it y time
        startTimesAndSteps = []
        startTimesAndSteps.append((
            self.data.employee.startTime,
            Step(activity = Home(employee = self.data.employee, start = True), startTime = self.data.employee.startTime)
        ))
        startTimesAndSteps.append((
            self.data.employee.endTime,
            Step(activity = Home(employee = self.data.employee, start = False), startTime = self.data.employee.endTime)
        ))
        for j in self.data.getTasksKeys():
            if int(np.sum([self.decisionVariablesU[j, k].x for k in self.data.getActivitiesKeys(includingDeparture = False, includingReturn = True) if k != j])) == 1:
                task = self.data.getTask(j)
                startTime = int(self.decisionVariablesT[j].x)
                startTimesAndSteps.append((
                    startTime,
                    Step(activity = task, startTime = startTime)
                ))
        for j in self.data.getUnavailabilitiesKeys():
            unavailability = self.data.getUnavailability(j)
            startTimesAndSteps.append((
                unavailability.startTime,
                Step(activity = unavailability, startTime = unavailability.startTime)
            ))
        startTimesAndSteps.sort()

        # Create and store sequence
        steps = [step for _, step in startTimesAndSteps]
        sequence = Sequence(self.data.instance, self.data.employee, steps)
        sequence.updateTimesGivenStartTimes()
        self.solutionSequence = sequence



    #----------#
    # Solution #
    #----------#


    def getSolutionAsSequence(self):
        if self.hasSolution():
            return self.solutionSequence
        else:
            raise Exception("There is no solution sequence stored")
