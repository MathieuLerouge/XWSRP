## RK: Skill level constraints could be handled in the definition of the variables U

###########
# Modules #
###########

# Basic modules
import gurobipy as grb
from gurobipy import GRB

# Project modules
from Definition.solution import *
from Optimization.IPModel.IP_model_data import *
from Tools.global_variables import *



#################
# Class IPModel #
#################


class IPModel:

    data = None
    type = None
    GRBModel = None
    minimization = True
    travelingDurationCoefficientInObjective = None
    workingDurationCoefficientInObjective = None
    nbRealizedTasksCoefficientInObjective = None
    decisionVariablesX = None
    decisionVariablesT = None
    decisionVariablesL = None
    decisionVariablesU = None
    decisionVariablesV = None
    storedSolutionToggle = None
    solution = None

    def __init__(self, instance, type):
        self.data = IPModelData(instance = instance, modelType = type)
        self.type = type
        self.GRBModel = grb.Model(instance.name + "byV" + str(type))
        self.addDecisionVariables()
        self.addObjectiveFunction()
        self.addConstraints()
        self.storedSolutionToggle = False



    ######################
    # Decision variables #
    ######################


    def addDecisionVariables(self):

        # Add X decision variables (specific to model of type 2)
        if self.type == 2:
            self.decisionVariablesX = self.GRBModel.addVars(
                self.data.getTasksIndices(), vtype = GRB.BINARY, name = "X")

        # Add T decision variables
        self.decisionVariablesT = self.GRBModel.addVars(
            self.data.getTasksIndices(), vtype = GRB.INTEGER, name = "T")

        # Add L decision variables (specific to model of type 2)
        if self.type == 2:
            self.decisionVariablesL = self.GRBModel.addVars(
                self.data.getEmployeesIndices(), vtype = GRB.INTEGER, name = "L")

        # Add U decision variables
        if self.type == 1:
            self.decisionVariablesU = self.GRBModel.addVars(
                [(i, j, k)
                    for i in self.data.getEmployeesIndices()
                    for j in self.data.getEmployeeActivitiesIndices(
                        employeeIndex = i,
                        includingStart = True,
                        includingEnd = False
                    )
                    for k in self.data.getEmployeeActivitiesIndices(
                        employeeIndex = i,
                        includingStart = False,
                        includingEnd = True
                    ) if k != j
                ],
                vtype = GRB.BINARY, name = "U")
        elif self.type == 2:
            self.decisionVariablesU = self.GRBModel.addVars(
                [(i, j, k, n)
                    for i in self.data.getEmployeesIndices()
                    for j in self.data.getEmployeeActivitiesIndices(
                        employeeIndex = i,
                        includingStart = True,
                        includingEnd = False
                    )
                    for k in self.data.getEmployeeActivitiesIndices(
                        employeeIndex = i,
                        includingStart = False,
                        includingEnd = True
                    ) if k != j
                    for n in self.data.getEmployeeTasksAvailabilityTWIndices(
                        employeeIndex = i,
                        activityIndex = j
                    )
                ],
                vtype = GRB.BINARY, name = "U")

        # Add V decision variables (specific to model of type 2)
        if self.type == 2:
            self.decisionVariablesV = self.GRBModel.addVars(
                [(i, j, k)
                    for i in self.data.getEmployeesIndices()
                    for j in self.data.getEmployeeActivitiesIndices(
                        employeeIndex = i,
                        includingStart = True,
                        includingEnd = False
                    )
                    for k in self.data.getEmployeeActivitiesIndices(
                        employeeIndex = i,
                        includingStart = False,
                        includingEnd = True
                    ) if k != j
                ],
                vtype = GRB.BINARY, name = "V")

        self.GRBModel.update()



    ######################
    # Objective function #
    ######################


    def setObjectiveFunctionParameters(self, minimization = True,
        travelingDurationCoefficient = None,
        workingDurationCoefficient = None,
        nbRealizedTasksCoefficient = None):

        self.minimization = minimization
        self.travelingDurationCoefficientInObjective = travelingDurationCoefficient
        self.workingDurationCoefficientInObjective = workingDurationCoefficient
        self.nbRealizedTasksCoefficientInObjective = nbRealizedTasksCoefficient
        self.addObjectiveFunction()

    def addObjectiveFunction(self):

        objectiveExpression = grb.LinExpr()

        # Traveling duration
        if self.travelingDurationCoefficientInObjective != None:
            travelingDuration = grb.LinExpr()
            travelingDuration.add(
                grb.quicksum(
                    [self.decisionVariablesU[indices]*\
                        self.data.getTravelingDuration(
                            employeeIndex = indices[0],
                            activityIndex1 = indices[1],
                            activityIndex2 = indices[2]
                        )
                        for indices in self.decisionVariablesU.keys()
                    ]
                )
            )
            objectiveExpression += self.travelingDurationCoefficientInObjective*travelingDuration

        # Working duration
        if self.workingDurationCoefficientInObjective != None and self.type != 1:
            workingDuration = grb.LinExpr()
            workingDuration.add(
                grb.quicksum(
                    [self.decisionVariablesX[j]*self.data.getTask(j).duration
                        for j in self.data.getTasksIndices()
                    ]
                )
            )
            objectiveExpression += self.workingDurationCoefficientInObjective*workingDuration

        # Number of realized tasks
        if self.nbRealizedTasksCoefficientInObjective != None and self.type != 1:
            nbRealizedTasks = grb.LinExpr()
            nbRealizedTasks.add(
                grb.quicksum(
                    [self.decisionVariablesX[j]
                        for j in self.data.getTasksIndices()
                    ]
                )
            )
            objectiveExpression += self.nbRealizedTasksCoefficientInObjective*nbRealizedTasks

        sense = None
        if self.minimization:
            sense = GRB.MINIMIZE
        else:
            sense = GRB.MAXIMIZE
        self.GRBModel.setObjective(objectiveExpression, sense = sense)
        self.GRBModel.update()


    ###############
    # Constraints #
    ###############


    def addConstraints(self):
        self.addCoveringConstraints()
        self.addFlowConstraints()
        self.addTimeWindowConstraints()
        self.addTimeSequenceConstraints()
        self.addSkillLevelConstraints()



    ########################
    # Covering constraints #
    ########################


    def addCoveringConstraints(self):

        # Case of models of type 1
        if self.type == 1:
            for j in self.data.getTasksIndices():
                self.GRBModel.addLConstr(
                    grb.quicksum(
                        [self.decisionVariablesU[(i, j, k)]
                            for i in self.data.getEmployeesIndices()
                            for k in self.data.getEmployeeActivitiesIndices(
                                employeeIndex = i,
                                includingStart = False,
                                includingEnd = True
                            ) if k != j
                        ]
                    ),
                    sense = GRB.EQUAL, rhs = 1,
                    name = f"TaskCoveringConstraint[{j}]"
                )

        # Case of models of type 2
        elif self.type == 2:

            # Task covering
            for j in self.data.getTasksIndices():
                self.GRBModel.addLConstr(
                    grb.quicksum(
                        [self.decisionVariablesU[(i, j, k, n)]
                            for i in self.data.getEmployeesIndices()
                            for k in self.data.getEmployeeActivitiesIndices(
                                employeeIndex = i,
                                includingStart = False,
                                includingEnd = True
                            ) if k != j
                            for n in self.data.getEmployeeTasksAvailabilityTWIndices(
                                employeeIndex = i,
                                activityIndex = j
                            )
                        ]
                    ) - self.decisionVariablesX[j],
                    sense = GRB.EQUAL, rhs = 0,
                    name = f"TaskCoveringConstraint[{j}]"
                )

            # Unavailability covering
            for i in self.data.getEmployeesIndices():
                for j in self.data.getEmployeeUnavailabilitiesIndices(i):
                    self.GRBModel.addLConstr(
                        grb.quicksum(
                            [self.decisionVariablesU[(i, j, k, n)]
                                for k in self.data.getEmployeeActivitiesIndices(
                                    employeeIndex = i,
                                    includingStart = False,
                                    includingEnd = True
                                ) if k != j
                                for n in self.data.getEmployeeTasksAvailabilityTWIndices(
                                    employeeIndex = i,
                                    activityIndex = j
                                )
                            ]
                        ),
                        sense = GRB.EQUAL, rhs = 1,
                        name = f"UnavailabilityCoveringConstraint[{i},{j}]"
                    )

            # Lunch break covering
            for i in self.data.getEmployeesIndices():
                self.GRBModel.addLConstr(
                    grb.quicksum(
                        [self.decisionVariablesV[(i, j, k)]
                            for j in self.data.getEmployeeActivitiesIndices(
                                employeeIndex = i,
                                includingStart = True,
                                includingEnd = False
                            )
                            for k in self.data.getEmployeeActivitiesIndices(
                                employeeIndex = i,
                                includingStart = False,
                                includingEnd = True
                            ) if k != j
                        ]
                    ),
                    sense = GRB.EQUAL, rhs = 1,
                    name = f"LunchBreakCoveringConstraint[{i}]"
                )

            # Lunch break sequence implying task sequence
            for i in self.data.getEmployeesIndices():
                for j in self.data.getEmployeeActivitiesIndices(
                    employeeIndex = i,
                    includingStart = True,
                    includingEnd = False):
                    for k in self.data.getEmployeeActivitiesIndices(
                        employeeIndex = i,
                        includingStart = False,
                        includingEnd = True):
                        if k != j:
                            self.GRBModel.addLConstr(
                                self.decisionVariablesV[(i, j, k)] -
                                grb.quicksum(
                                    [self.decisionVariablesU[(i, j, k, n)]
                                        for n in self.data.getEmployeeTasksAvailabilityTWIndices(
                                            employeeIndex = i,
                                            activityIndex = j
                                        )
                                    ]
                                ),
                                sense = GRB.LESS_EQUAL, rhs = 0,
                                name = f"TaskCoveringImplicationConstraint[{i},{j},{k}]"
                            )

        self.GRBModel.update()



    ####################
    # Flow constraints #
    ####################


    # RK: this method could be faster by implementing two cases depending on the model's type
    def addFlowConstraints(self):

        for i in self.data.getEmployeesIndices():

            # Starting flow
            self.GRBModel.addLConstr(
                grb.quicksum(
                    [self.decisionVariablesU[indices]
                        for indices in self.decisionVariablesU.keys()
                        if indices[0] == i and indices[1] == self.data.startIndex
                    ]
                ),
                sense = GRB.EQUAL, rhs = 1,
                name = f"StartFlowConstraint[{i}]"
            )

            # Tasks flow
            for k in self.data.getEmployeeActivitiesIndices(
                employeeIndex = i,
                includingStart = False,
                includingEnd = False,
                includingUnavailabilities = True):
                self.GRBModel.addLConstr(
                    grb.quicksum(
                        [self.decisionVariablesU[indices]
                            for indices in self.decisionVariablesU.keys()
                            if indices[0] == i and indices[2] == k
                        ]
                    ) -
                    grb.quicksum(
                        [self.decisionVariablesU[indices]
                            for indices in self.decisionVariablesU.keys()
                            if indices[0] == i and indices[1] == k
                        ]
                    ),
                    sense = GRB.EQUAL, rhs = 0,
                    name = f"flowConstraint[{i},{k}]"
                )

            # Ending flow
            self.GRBModel.addLConstr(
                grb.quicksum(
                    [self.decisionVariablesU[indices]
                        for indices in self.decisionVariablesU.keys()
                        if indices[0] == i and indices[2] == self.data.endIndex
                    ]
                ),
                sense = GRB.EQUAL, rhs = 1,
                name = f"EndFlowConstraint[{i}]"
            )

        self.GRBModel.update()



    ###########################
    # Time window constraints #
    ###########################


    def addTimeWindowConstraints(self):

        # Case of models of type 1
        if self.type == 1:

            # Bounds on tasks' realization times
            for j in self.data.getTasksIndices():

                # Lower bound on task's realization time
                self.GRBModel.addLConstr(
                    self.decisionVariablesT[j],
                    sense = GRB.GREATER_EQUAL, rhs = self.data.getTask(j).startTime,
                    name = f"TaskTWLBContraint[{j}]"
                )

                # Upper bound on task's realization time
                self.GRBModel.addLConstr(
                    self.decisionVariablesT[j] + self.data.getTask(j).duration,
                    sense = GRB.LESS_EQUAL, rhs = self.data.getTask(j).endTime,
                    name = f"TaskTWUBContraint[{j}]"
                )

        # Case of models of type 2
        elif self.type == 2:

            # Bounds on tasks' realization times
            for j in self.data.getTasksIndices():

                # Lower bound on task's realization time
                self.GRBModel.addLConstr(
                    self.decisionVariablesT[j] -
                    grb.quicksum(
                        [self.decisionVariablesU[(i, j, k, n)]*\
                            self.data.getTask(j).availabilityTimeWindows[n].lowerBound
                            for i in self.data.getEmployeesIndices()
                            for k in self.data.getEmployeeActivitiesIndices(
                                employeeIndex = i,
                                includingStart = False,
                                includingEnd = True
                            ) if k != j
                            for n in self.data.getEmployeeTasksAvailabilityTWIndices(
                                employeeIndex = i,
                                activityIndex = j
                            )
                        ]
                    ),
                    sense = GRB.GREATER_EQUAL, rhs = 0,
                    name = f"TaskTWLBContraint[{j}]"
                )

                # Upper bound on task's realization time
                self.GRBModel.addLConstr(
                    self.decisionVariablesT[j] +
                    self.decisionVariablesX[j]*self.data.getTask(j).duration -
                    grb.quicksum(
                        [self.decisionVariablesU[(i, j, k, n)]*\
                            self.data.getTask(j).availabilityTimeWindows[n].upperBound
                            for i in self.data.getEmployeesIndices()
                            for k in self.data.getEmployeeActivitiesIndices(
                                employeeIndex = i,
                                includingStart = False,
                                includingEnd = True
                            ) if k != j
                            for n in self.data.getEmployeeTasksAvailabilityTWIndices(
                                employeeIndex = i,
                                activityIndex = j
                            )
                        ]
                    ),
                    sense = GRB.LESS_EQUAL, rhs = 0,
                    name = f"TaskTWUBContraint[{j}]"
                )

            # Bounds on lunch breaks' realization times
            for i in self.data.getEmployeesIndices():

                # Lower bound on lunch break's realization time
                self.GRBModel.addLConstr(
                    self.decisionVariablesL[i],
                    sense = GRB.GREATER_EQUAL,
                    rhs = self.data.instance.lunchBreakStartTime,
                    name = f"LunchBreakTWLBContraint[{i}]"
                )

                # Upper bound on lunch break's realization time
                self.GRBModel.addLConstr(
                    self.decisionVariablesL[i],
                    sense = GRB.LESS_EQUAL,
                    rhs = self.data.instance.lunchBreakEndTime -\
                    self.data.instance.lunchBreakDuration,
                    name = f"LunchBreakTWUBContraint[{i}]"
                )

        self.GRBModel.update()



    #############################
    # Time sequence constraints #
    #############################


    def addTimeSequenceConstraints(self):

        # Case of models of type 1
        if self.type == 1:

            # Start-to-first-task time sequence
            for k in self.data.getTasksIndices():
                self.GRBModel.addLConstr(
                    grb.quicksum([
                        self.decisionVariablesU[(i, self.data.startIndex, k)]*(
                            self.data.getEmployee(i).startTime +
                            self.data.getTravelingDuration(
                                employeeIndex = i,
                                activityIndex1 = self.data.startIndex,
                                activityIndex2 = k
                            )
                        )
                        for i in self.data.getEmployeesIndices()
                    ]) - self.decisionVariablesT[k],
                    sense = GRB.LESS_EQUAL, rhs = 0,
                    name = f"StartToFirstTaskTimeSequenceConstraint[{k}]"
                )

            # Between-two-tasks time sequence
            for j in self.data.getTasksIndices():
                for k in self.data.getTasksIndices():
                    if k != j:
                        self.GRBModel.addLConstr(
                            self.decisionVariablesT[j] - self.decisionVariablesT[k] +
                            grb.quicksum([
                                self.decisionVariablesU[(i, j, k)]*(
                                    self.data.getTask(j).duration +
                                    self.data.getTravelingDuration(
                                        employeeIndex = i,
                                        activityIndex1 = j,
                                        activityIndex2 = k
                                    ) + self.data.getTask(j).endTime
                                )
                                for i in self.data.getEmployeesIndices()
                            ]) - self.data.getTask(j).endTime,
                            sense = GRB.LESS_EQUAL, rhs = 0,
                            name = f"TaskToTaskTimeSequenceConstraint[{j},{k}]"
                        )

            # Last-task-to-end time sequence
            for j in self.data.getTasksIndices():
                self.GRBModel.addLConstr(
                    self.decisionVariablesT[j] +
                    grb.quicksum([
                        self.decisionVariablesU[(i, j, self.data.endIndex)]*(
                            self.data.getTask(j).duration +
                            self.data.getTravelingDuration(
                                employeeIndex = i,
                                activityIndex1 = j,
                                activityIndex2 = self.data.endIndex
                            ) -
                            self.data.getEmployee(i).endTime +
                            self.data.getTask(j).endTime
                        )
                        for i in self.data.getEmployeesIndices()
                    ]),
                    sense = GRB.LESS_EQUAL, rhs = self.data.getTask(j).endTime,
                    name = f"LastTaskToEndTimeSequenceConstraint[{j}]"
                )

        # Case of models of type 2
        elif self.type == 2:

            # Start-to-first-task time sequence
            for k in self.data.getTasksIndices():
                self.GRBModel.addLConstr(
                    grb.quicksum([
                        self.decisionVariablesU[(i, self.data.startIndex, k, n)]*(
                            self.data.getEmployee(i).startTime +
                            self.data.getTravelingDuration(
                                employeeIndex = i,
                                activityIndex1 = self.data.startIndex,
                                activityIndex2 = k
                            )
                        ) + self.decisionVariablesV[(i, self.data.startIndex, k)]*\
                            self.data.instance.lunchBreakDuration
                        for i in self.data.getEmployeesIndices()
                        for n in self.data.getEmployeeTasksAvailabilityTWIndices(i, self.data.startIndex)
                    ]) - self.decisionVariablesT[k],
                    sense = GRB.LESS_EQUAL, rhs = 0,
                    name = f"StartToFirstTaskTimeSequenceConstraint[{k}]"
                )

            # Start-to-first-task-if-unavailability time sequence
            for i in self.data.getEmployeesIndices():
                for k in self.data.getEmployeeUnavailabilitiesIndices(i):
                    self.GRBModel.addLConstr(
                        grb.quicksum([
                            self.decisionVariablesU[(i, self.data.startIndex, k, n)]*(
                                #self.data.getEmployee(i).startTime +
                                self.data.getTravelingDuration(
                                    employeeIndex = i,
                                    activityIndex1 = self.data.startIndex,
                                    activityIndex2 = k
                                )
                            ) + self.decisionVariablesV[(i, self.data.startIndex, k)]*\
                                self.data.instance.lunchBreakDuration
                            for n in self.data.getEmployeeTasksAvailabilityTWIndices(i, self.data.startIndex)
                        ]) - self.data.getEmployeeActivity(i, k).startTime,
                        sense = GRB.LESS_EQUAL, rhs = 0,
                        name = f"StartToFirstTaskIfUnavailabilityTimeSequenceConstraint[{i},{k}]"
                    )

            # Between-two-tasks time sequence
            for j in self.data.getTasksIndices():
                for k in self.data.getTasksIndices():
                    if k != j:
                        self.GRBModel.addLConstr(
                            self.decisionVariablesT[j] +
                            grb.quicksum([
                                grb.quicksum([
                                    self.decisionVariablesU[(i, j, k, n)]
                                    for n in self.data.getEmployeeTasksAvailabilityTWIndices(i, j)
                                ])*(
                                    self.data.getTask(j).duration +
                                    self.data.getTravelingDuration(
                                        employeeIndex = i,
                                        activityIndex1 = j,
                                        activityIndex2 = k
                                    ) +
                                    self.data.getTask(j).endTime
                                ) +
                                self.decisionVariablesV[(i, j, k)]*\
                                    self.data.instance.lunchBreakDuration
                                for i in self.data.getEmployeesIndices()
                            ]) - self.decisionVariablesT[k],
                            sense = GRB.LESS_EQUAL, rhs = self.data.getTask(j).endTime,
                            name = f"TaskToTaskTimeSequenceConstraint[{j},{k}]"
                        )

            # Task-to-unavailability time sequence
            for i in self.data.getEmployeesIndices():
                for j in self.data.getTasksIndices():
                    for k in self.data.getEmployeeUnavailabilitiesIndices(i):
                        self.GRBModel.addLConstr(
                            self.decisionVariablesT[j] +
                            grb.quicksum([
                                    self.decisionVariablesU[(i, j, k, n)]
                                    for n in self.data.getEmployeeTasksAvailabilityTWIndices(i, j)
                            ])*(
                                self.data.getTask(j).duration +
                                self.data.getTravelingDuration(
                                    employeeIndex = i,
                                    activityIndex1 = j,
                                    activityIndex2 = k
                                ) +
                                self.data.getTask(j).endTime
                            ) +
                            self.decisionVariablesV[(i, j, k)]*\
                                self.data.instance.lunchBreakDuration,
                            sense = GRB.LESS_EQUAL,
                            rhs = self.data.getEmployeeUnavailability(i, k).startTime + self.data.getTask(j).endTime,
                            name = f"TaskToUnavailabilityTimeSequenceConstraint[{i},{j},{k}]"
                        )

            # Unavailability-to-task time sequence
            for i in self.data.getEmployeesIndices():
                for j in self.data.getEmployeeUnavailabilitiesIndices(i):
                    for k in self.data.getTasksIndices():
                        self.GRBModel.addLConstr(
                            grb.quicksum([
                                    self.decisionVariablesU[(i, j, k, n)]
                                    for n in self.data.getEmployeeTasksAvailabilityTWIndices(i, j)
                            ])*(
                                self.data.getEmployeeUnavailability(i, j).endTime +
                                self.data.getTravelingDuration(
                                    employeeIndex = i,
                                    activityIndex1 = j,
                                    activityIndex2 = k
                                )
                            ) +
                            self.decisionVariablesV[(i, j, k)]*\
                                self.data.instance.lunchBreakDuration -
                            self.decisionVariablesT[k],
                            sense = GRB.LESS_EQUAL, rhs = 0,
                            name = f"UnavailabilityToTaskTimeSequenceConstraint[{i},{j},{k}]"
                        )

            # Unavailability-to-unavailability time sequence
            for i in self.data.getEmployeesIndices():
                for j in self.data.getEmployeeUnavailabilitiesIndices(i):
                    for k in self.data.getEmployeeUnavailabilitiesIndices(i):
                        if j != k:
                            self.GRBModel.addLConstr(
                                grb.quicksum([
                                        self.decisionVariablesU[(i, j, k, n)]
                                        for n in self.data.getEmployeeTasksAvailabilityTWIndices(i, j)
                                ])*(
                                    self.data.getEmployeeUnavailability(i, j).endTime +
                                    self.data.getTravelingDuration(
                                        employeeIndex = i,
                                        activityIndex1 = j,
                                        activityIndex2 = k
                                    )
                                ) +
                                self.decisionVariablesV[(i, j, k)]*\
                                    self.data.instance.lunchBreakDuration -
                                self.data.getEmployeeUnavailability(i, k).startTime,
                                sense = GRB.LESS_EQUAL, rhs = 0,
                                name = f"UnavailabilityToUnavailabilityTimeSequenceConstraint[{i},{j},{k}]"
                            )

            # Last-task-to-end time sequence
            for j in self.data.getTasksIndices():
                self.GRBModel.addLConstr(
                    self.decisionVariablesT[j] +
                    grb.quicksum([
                        grb.quicksum([
                            self.decisionVariablesU[(i, j, self.data.endIndex, n)]
                            for n in self.data.getEmployeeTasksAvailabilityTWIndices(i, j)
                        ])*(
                            self.data.getTask(j).duration +
                            self.data.getTravelingDuration(
                                employeeIndex = i,
                                activityIndex1 = j,
                                activityIndex2 = self.data.endIndex
                            ) +
                            self.data.getTask(j).endTime -
                            self.data.getEmployee(i).endTime
                        ) +
                        self.decisionVariablesV[(i, j, self.data.endIndex)]*\
                            self.data.instance.lunchBreakDuration
                        for i in self.data.getEmployeesIndices()
                    ]),
                    sense = GRB.LESS_EQUAL, rhs = self.data.getTask(j).endTime,
                    name = f"TaskToEndTimeSequenceConstraint[{j}]"
                )

            # # Last-task-if-unavailability-to-end time sequence
            # # Assumption: not needed otherwise it means the instance is unfeasible

            # Task-before-lunch time sequence
            for i in self.data.getEmployeesIndices():
                for j in self.data.getTasksIndices():
                    for k in self.data.getEmployeeActivitiesIndices(
                        employeeIndex = i,
                        includingStart = False,
                        includingEnd = True):
                        if k != j:
                            self.GRBModel.addLConstr(
                                self.decisionVariablesT[j] +
                                self.data.getTask(j).duration -
                                self.decisionVariablesL[i] +
                                self.decisionVariablesV[(i, j, k)]*\
                                    self.data.getTask(j).endTime,
                                sense = GRB.LESS_EQUAL, rhs = self.data.getTask(j).endTime,
                                name = f"TaskBeforeLunchTimeSequenceConstraint[{i},{j},{k}]"
                            )

            # Unavailability-before-lunch time sequence
            for i in self.data.getEmployeesIndices():
                for j in self.data.getEmployeeUnavailabilitiesIndices(i):
                    for k in self.data.getEmployeeActivitiesIndices(
                        employeeIndex = i,
                        includingStart = False,
                        includingEnd = True):
                        if j != k:
                            self.GRBModel.addLConstr(
                                self.decisionVariablesV[(i, j, k)]*\
                                    self.data.getEmployeeUnavailability(i, j).endTime -
                                self.decisionVariablesL[i],
                                sense = GRB.LESS_EQUAL, rhs = 0,
                                name = f"UnavailabilityBeforeLunchTimeSequenceConstraint[{i},{j},{k}]"
                            )

            # Task-after-lunch time sequence
            for i in self.data.getEmployeesIndices():
                for j in self.data.getEmployeeActivitiesIndices(
                    employeeIndex = i,
                    includingStart = True,
                    includingEnd = False):
                    for k in self.data.getTasksIndices():
                        if j != k:
                            self.GRBModel.addLConstr(
                                self.decisionVariablesL[i] +
                                self.data.instance.lunchBreakDuration -
                                self.decisionVariablesT[k] +
                                self.decisionVariablesV[(i, j, k)]*\
                                    self.data.instance.lunchBreakEndTime,
                                sense = GRB.LESS_EQUAL, rhs = self.data.instance.lunchBreakEndTime,
                                name = f"TaskAfterLunchTimeSequenceConstraint[{i},{j},{k}]"
                            )

            # Unavailability-after-lunch time sequence
            for i in self.data.getEmployeesIndices():
                for j in self.data.getEmployeeActivitiesIndices(
                    employeeIndex = i,
                    includingStart = True,
                    includingEnd = False):
                    for k in self.data.getEmployeeUnavailabilitiesIndices(i):
                        if j != k:
                            self.GRBModel.addLConstr(
                                self.decisionVariablesL[i] +
                                self.data.instance.lunchBreakDuration -
                                self.data.getEmployeeUnavailability(i, k).startTime +
                                self.decisionVariablesV[(i, j, k)]*\
                                    self.data.instance.lunchBreakEndTime,
                                sense = GRB.LESS_EQUAL, rhs = self.data.instance.lunchBreakEndTime,
                                name = f"UnavailabilityAfterLunchTimeSequenceConstraint[{i},{j},{k}]"
                           )

        self.GRBModel.update()



    ###########################
    # Skill level constraints #
    ###########################


    def addSkillLevelConstraints(self):
        for j in self.data.getTasksIndices():
            self.GRBModel.addLConstr(
                grb.quicksum(
                    [self.decisionVariablesU[indices]*(
                        self.data.getEmployee(indices[0]).skillLevel -
                        self.data.getTask(j).skillLevel
                    )
                        for indices in self.decisionVariablesU.keys()
                        if indices[1] == j
                    ]
                ),
                sense = GRB.GREATER_EQUAL, rhs = 0,
                name = f"SkillLevelConstraint[{j}]"
            )




    ################
    # Optimization #
    ################


    def setSolvingTimeLimit(self, solvingTimeLimitInSeconds = None):
        if solvingTimeLimitInSeconds != None:
            self.GRBModel.Params.timeLimit = solvingTimeLimitInSeconds


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
        elif self.GRBModel.Status == GRB.TIME_LIMIT:
            print("IP model solving was stopped as it reached given time limit")
            print("")
            self.storedSolutionToggle = True
        else:
            self.storedSolutionToggle = True
        if self.storedSolutionToggle:
            self.extractSolution()


    def extractSolution(self):

        if not(self.storedSolutionToggle):
            print("There is no solution stored")

        else:
            solvingMethodId = None
            if self.type == 1:
                solvingMethodId = IPModelType1Id
            elif self.type == 2:
                solvingMethodId = IPModelType2Id
            solution = Solution(instance = self.data.instance)
            solution.setOptimizationData(
                methodId = solvingMethodId,
                parameters = [
                    "min" if self.minimization else "max",
                    self.travelingDurationCoefficientInObjective,
                    self.workingDurationCoefficientInObjective,
                    self.nbRealizedTasksCoefficientInObjective
                ],
                runTime = self.getSolvingRunTime(),
                optimalityGap = self.getOptimalityGap(),
                objectiveValue = self.getObjectiveValue()
            )

            # Results about tasks
            for j in self.data.getTasksIndices():
                taskDescription = solution.tasksDescriptions[self.data.getTask(j).name]
                if self.type == 1:
                    taskDescription["realized"] = True
                elif self.type == 2:
                    taskDescription["realized"] = (self.decisionVariablesX[j].x > 0.99)
                if taskDescription["realized"]:
                    taskDescription["startTime"] = int(self.decisionVariablesT[j].x)
            for i in self.data.getEmployeesIndices():
                for j in self.data.getTasksIndices():
                    for k in self.data.getEmployeeActivitiesIndices(
                        employeeIndex = i, includingStart = False, includingEnd = True):
                        if j != k:
                            if self.type == 1:
                                if self.decisionVariablesU[(i, j, k)].x > 0.99:
                                    taskDescription = solution.tasksDescriptions[self.data.getTask(j).name]
                                    taskDescription["employeeName"] = self.data.getEmployee(i).name
                            elif self.type == 2:
                                for n in self.data.getEmployeeTasksAvailabilityTWIndices(i, j):
                                    if self.decisionVariablesU[(i, j, k, n)].x > 0.99:
                                        taskDescription = solution.tasksDescriptions[self.data.getTask(j).name]
                                        taskDescription["employeeName"] = self.data.getEmployee(i).name

            # Results about employees sequences
            # for i in self.data.getEmployeesIndices():
            #     employeeSequence = []
            #     j = self.data.startIndex
            #     while j != self.data.endIndex:
            #         for k in self.data.getEmployeeActivitiesIndices(
            #             employeeIndex = i,
            #             includingStart = False, includingEnd = True):
            #             if k != j:
            #                 stepDescription = dict()
            #                 if self.type == 1:
            #                     if self.decisionVariablesU[(i, j, k)].x > 0.99:
            #                         stepDescription["name"] = self.data.getEmployeeActivity(i, j).name
            #                 elif self.type == 2:
            #                     for n in self.data.getEmployeeTasksAvailabilityTWIndices(i, j):
            #                         if self.decisionVariablesU[(i, j, k, n)].x > 0.99:
            #                             stepDescription["name"] = self.data.getEmployeeActivity(i, j).name
            #                 if "name" in stepDescription.keys():
            #                     stepDescription["arrivalTime"] = None
            #                     if j in self.data.getTasksIndices():
            #                         task = self.data.getTask(j)
            #                         taskDescription = solution.tasksDescriptions[task.name]
            #                         taskDescription["employeeName"] = self.data.getEmployee(i).name
            #                         stepDescription["startTime"] = taskDescription["startTime"]
            #                         stepDescription["endTime"] = stepDescription["startTime"] + task.duration
            #                     elif j != self.data.startIndex:
            #                         activity = self.data.getEmployeeActivity(i, j)
            #                         stepDescription["startTime"] = activity.startTime
            #                         stepDescription["endTime"] = stepDescription["startTime"] + activity.duration
            #                     else:
            #                         stepDescription["startTime"] = None
            #                         stepDescription["endTime"] = None
            #                     stepDescription["travelingDurationToNextStep"] = np.round(
            #                         self.data.getTravelingDuration(
            #                             employeeIndex = i,
            #                             activityIndex1 = j,
            #                             activityIndex2 = k
            #                         ), 4
            #                     )
            #                     employeeSequence.append(stepDescription)
            #                     j = k
            #                     break
            #     stepDescription = dict()
            #     stepDescription["name"] = self.data.getEmployeeActivity(i, j).name
            #     stepDescription["arrivalTime"] = None
            #     stepDescription["startTime"] = None
            #     stepDescription["endTime"] = None
            #     stepDescription["travelingDurationToNextStep"] = 0
            #     employeeSequence.append(stepDescription)
            #     solution.employeesSequences[self.data.getEmployee(i).name] = employeeSequence

            # Results about employees lunch breaks
            # if self.type == 2:
            #     for i in self.data.getEmployeesIndices():
            #         lunchBreakDescription = solution.employeesLunchBreaksDescriptions[self.data.getEmployee(i).name]
            #         lunchBreakDescription["startTime"] = int(self.decisionVariablesL[i].x)
            #     for (i, j, k), decisionVariableV in self.decisionVariablesV.items():
            #         if decisionVariableV.x > 0.99:
            #             lunchBreakDescription = solution.employeesLunchBreaksDescriptions[self.data.getEmployee(i).name]
            #             lunchBreakDescription["taskBefore"] = self.data.getEmployeeActivity(i, j).name
            #             lunchBreakDescription["taskAfter"] = self.data.getEmployeeActivity(i, k).name

            self.solution = solution



    ############
    # Solution #
    ############


    def getSolution(self):
        if not(self.storedSolutionToggle):
            print("There is no solution stored")
            return None
        else:
            return self.solution


    def getOptimalityGap(self):
        if not(self.storedSolutionToggle):
            print("There is no solution stored")
            return None
        else:
            return np.round(self.GRBModel.MIPGap, 5)


    def getSolvingRunTime(self):
        if not(self.storedSolutionToggle):
            print("There is no solution stored")
            return None
        else:
            return np.round(self.GRBModel.Runtime, 3)


    def getObjectiveValue(self):
        if not(self.storedSolutionToggle):
            print("There is no solution stored")
            return None
        else:
            return np.round(self.GRBModel.objVal, 3)
