# Third party libraries
import gurobipy as grb
from gurobipy import GRB
import numpy as np

# Local libraries
from src.optimization.solution import SolutionOpti
from src.optimization.IP.WSRPdata import WSRPIPModelData, LEAVING_HOME_INDEX, COMING_BACK_HOME_INDEX
from src.utils.constants import SOLUTION_SOLVING_METHOD_SYMBOL_BIS

# Global variables
TRAVELING_DURATION_WEIGHT_KEY = 'traveling_duration'
WORKING_DURATION_WEIGHT_KEY = 'working_duration'
NB_REALIZED_TASKS_WEIGHT_KEY = 'nb_realized_tasks'
SOLVING_METHOD_IP = 'IP'


#####################
# Class WSRPIPModel #
#####################

class WSRPIPModel:

    def __init__(self, instance):
        self._name = f"{instance.core_name}{SOLUTION_SOLVING_METHOD_SYMBOL_BIS}{self._solving_method_id}"
        self._data = WSRPIPModelData(instance)
        self._assumptions = dict()
        self._assumptions['cover_all_tasks'] = False
        self._weights = dict()
        self._weights[TRAVELING_DURATION_WEIGHT_KEY] = 1
        self._weights[WORKING_DURATION_WEIGHT_KEY] = -10
        self._weights[NB_REALIZED_TASKS_WEIGHT_KEY] = None
        self._model = None
        self._decision_variables = dict()
        self._successful_IP_solving = False
        self._solution = None

    @property
    def name(self):
        return self._name

    ##############
    # Assumption #
    ##############

    @property
    def is_making_all_tasks_covered(self):
        return self._assumptions['cover_all_tasks']

    @is_making_all_tasks_covered.setter
    def is_making_all_tasks_covered(self, boolean: bool):
        self._assumptions['cover_all_tasks'] = boolean
        if boolean:
            self.weight_traveling_duration = 1
            self.weight_working_duration = None
            self.weight_nb_realized_tasks = None
        else:
            self.weight_traveling_duration = 1
            self.weight_working_duration = -10
            self.weight_nb_realized_tasks = None

    @property
    def is_considering_lunch_break(self):
        return self._data.instance.has_lunch_break

    @property
    def is_considering_tasks_unavailabilities(self):
        return self._data.instance.has_task_unavailabilities

    ##########
    # Update #
    ##########

    def update(self):
        self._model = grb.Model(self._name)
        self._add_decision_variables()
        self._add_objective_function()
        self._add_constraints()

    def display(self):
        self._model.display()

    ######################
    # Decision variables #
    ######################

    @property
    def vars_X(self):
        return self._decision_variables['X']

    @vars_X.setter
    def vars_X(self, X: grb.MVar):
        self._decision_variables['X'] = X

    @property
    def vars_T(self):
        return self._decision_variables['T']

    @vars_T.setter
    def vars_T(self, T: grb.MVar):
        self._decision_variables['T'] = T

    @property
    def vars_L(self):
        return self._decision_variables['L']

    @vars_L.setter
    def vars_L(self, L: grb.MVar):
        self._decision_variables['L'] = L

    @property
    def vars_U(self):
        return self._decision_variables['U']

    @vars_U.setter
    def vars_U(self, U: grb.MVar):
        self._decision_variables['U'] = U

    @property
    def vars_V(self):
        return self._decision_variables['V']

    @vars_V.setter
    def vars_V(self, V: grb.MVar):
        self._decision_variables['V'] = V

    def _add_decision_variables(self):
        # Add X decision variables
        if not self.is_making_all_tasks_covered:
            self.vars_X = self._model.addVars(self._data.tasks_indices, vtype=GRB.BINARY, name="X")
        # Add T decision variables
        self.vars_T = self._model.addVars(self._data.tasks_indices, vtype=GRB.INTEGER, name="T")
        # TODO remove decision variables L which are no longer useful
        # Add L decision variables
        if self.is_considering_lunch_break:
            self.vars_L = self._model.addVars(self._data.employees_indices, vtype=GRB.INTEGER, name="L")
        self.vars_U = self._model.addVars(
            [(i, j, k, n) for i in self._data.employees_indices
             for j in self._data.get_hyp_activities_indices(i, True, False)
             for k in self._data.get_hyp_activities_indices(i, False, True) if k != j
             for n in self._data.get_hyp_activities_TW_indices(i, j)],
            vtype=GRB.BINARY, name="U")
        # Add V decision variables
        if self._data.instance.has_lunch_break:
            self.vars_V = self._model.addVars(
                [(i, j, k) for i in self._data.employees_indices
                 for j in self._data.get_hyp_activities_indices(i, True, False)
                 for k in self._data.get_hyp_activities_indices(i, False, True) if k != j],
                vtype=GRB.BINARY, name="V")
        self._model.update()

    ######################
    # Objective function #
    ######################

    @property
    def weight_traveling_duration(self):
        if self._weights[TRAVELING_DURATION_WEIGHT_KEY] is not None:
            return self._weights[TRAVELING_DURATION_WEIGHT_KEY]
        else:
            return 0

    @weight_traveling_duration.setter
    def weight_traveling_duration(self, weight):
        self._weights[TRAVELING_DURATION_WEIGHT_KEY] = weight

    @property
    def weight_working_duration(self):
        if self._weights[WORKING_DURATION_WEIGHT_KEY] is not None:
            return self._weights[WORKING_DURATION_WEIGHT_KEY]
        else:
            return 0

    @weight_working_duration.setter
    def weight_working_duration(self, weight):
        if self.is_making_all_tasks_covered and weight is not None:
            raise ValueError("The working duration weight must be None "
                             "when it is assumed that all tasks must be covered")
        self._weights[WORKING_DURATION_WEIGHT_KEY] = weight

    @property
    def weight_nb_realized_tasks(self):
        if self._weights[NB_REALIZED_TASKS_WEIGHT_KEY] is not None:
            return self._weights[NB_REALIZED_TASKS_WEIGHT_KEY]
        else:
            return 0

    @weight_nb_realized_tasks.setter
    def weight_nb_realized_tasks(self, weight):
        if self.is_making_all_tasks_covered and weight is not None:
            raise ValueError("The number of realized tasks weight must be None "
                             "when it is assumed that all tasks must be covered")
        self._weights[NB_REALIZED_TASKS_WEIGHT_KEY] = weight

    def _add_objective_function(self):

        objective = grb.LinExpr()

        # Traveling duration
        if self.weight_traveling_duration is not None:
            traveling_duration = grb.LinExpr()
            traveling_duration.add(
                grb.quicksum(
                    [self.vars_U[indices] * self._data.get_traveling_duration(
                        employee_index=indices[0], activity_index1=indices[1], activity_index2=indices[2]
                    )
                     for indices in self.vars_U.keys()
                     ]
                )
            )
            objective += self.weight_traveling_duration * traveling_duration

        # Working duration
        if self.weight_working_duration is not None and self.weight_working_duration != 0:
            working_duration = grb.LinExpr()
            working_duration.add(
                grb.quicksum([self.vars_X[j] * self._data.get_task_by_index(j).duration
                              for j in self._data.tasks_indices])
            )
            objective += self.weight_working_duration * working_duration

        # Number of realized tasks
        if self.weight_nb_realized_tasks is not None and self.weight_working_duration != 0:
            nb_realized_tasks = grb.LinExpr()
            nb_realized_tasks.add(grb.quicksum([self.vars_X[j] for j in self._data.tasks_indices]))
            objective += self.weight_nb_realized_tasks * nb_realized_tasks

        self._model.setObjective(objective, sense=GRB.MINIMIZE)
        self._model.update()

    ###############
    # Constraints #
    ###############

    def _add_constraints(self):
        self._add_covering_constraints()
        self._add_flow_constraints()
        self._add_time_window_constraints()
        self._add_time_sequence_constraints()
        self._add_skill_level_constraints()

    ##########################
    # - Covering constraints #
    ##########################

    def _add_covering_constraints(self):
        # Add tasks covering constraints
        if self.is_making_all_tasks_covered:
            for j in self._data.tasks_indices:
                self._model.addLConstr(
                    grb.quicksum([self.vars_U[(i, j, k, n)]
                                  for i in self._data.employees_indices
                                  for k in self._data.get_hyp_activities_indices(i, False, True) if k != j
                                  for n in self._data.get_hyp_activities_TW_indices(i, j)]),
                    sense=GRB.EQUAL, rhs=1,
                    name=f"TaskCoveringConstraint[{j}]"
                )
        else:
            for j in self._data.tasks_indices:
                self._model.addLConstr(
                    grb.quicksum([self.vars_U[(i, j, k, n)]
                                  for i in self._data.employees_indices
                                  for k in self._data.get_hyp_activities_indices(i, False, True) if k != j
                                  for n in self._data.get_hyp_activities_TW_indices(i, j)]) - self.vars_X[j],
                    sense=GRB.EQUAL, rhs=0,
                    name=f"TaskCoveringConstraint[{j}]"
                )
        # Add unavailability covering if any
        for i in self._data.employees_indices:
            for j in self._data.get_employee_unavailabilities_indices(i):
                self._model.addLConstr(
                    grb.quicksum([self.vars_U[(i, j, k, n)]
                                  for k in self._data.get_hyp_activities_indices(i, False, True) if k != j
                                  for n in self._data.get_hyp_activities_TW_indices(i, j)]),
                    sense=GRB.EQUAL, rhs=1,
                    name=f"UnavailabilityCoveringConstraint[{i},{j}]"
                )
        # Add lunch break covering if any
        if self.is_considering_lunch_break:
            for i in self._data.employees_indices:
                self._model.addLConstr(
                    grb.quicksum([self.vars_V[(i, j, k)]
                                  for j in self._data.get_hyp_activities_indices(i, True, False)
                                  for k in self._data.get_hyp_activities_indices(i, False, True) if k != j]),
                    sense=GRB.EQUAL, rhs=1,
                    name=f"LunchBreakCoveringConstraint[{i}]"
                )
            for i in self._data.employees_indices:
                for j in self._data.get_hyp_activities_indices(i, True, False):
                    for k in self._data.get_hyp_activities_indices(i, False, True):
                        if k != j:
                            self._model.addLConstr(
                                self.vars_V[(i, j, k)] -
                                grb.quicksum([self.vars_U[(i, j, k, n)]
                                              for n in self._data.get_hyp_activities_TW_indices(i, j)]),
                                sense=GRB.LESS_EQUAL, rhs=0,
                                name=f"TaskCoveringImplicationConstraint[{i},{j},{k}]"
                            )
        self._model.update()

    #
    ######################
    # - Flow constraints #
    ######################

    def _add_flow_constraints(self):
        for i in self._data.employees_indices:
            # Add flow constraint at start locations
            self._model.addLConstr(
                grb.quicksum([self.vars_U[indices] for indices in self.vars_U.keys()
                              if indices[0] == i and indices[1] == LEAVING_HOME_INDEX]),
                sense=GRB.EQUAL, rhs=1,
                name=f"StartFlowConstraint[{i}]"
            )
            # Add flow constraints around tasks and unavailabilities if any
            for k in self._data.get_hyp_activities_indices(i, False, False, True):
                self._model.addLConstr(
                    grb.quicksum([self.vars_U[indices] for indices in self.vars_U.keys()
                                  if indices[0] == i and indices[2] == k]) -
                    grb.quicksum([self.vars_U[indices] for indices in self.vars_U.keys()
                                  if indices[0] == i and indices[1] == k]),
                    sense=GRB.EQUAL, rhs=0,
                    name=f"flowConstraint[{i},{k}]"
                )
            # Add flow constraint at end locations
            self._model.addLConstr(
                grb.quicksum([self.vars_U[indices] for indices in self.vars_U.keys()
                              if indices[0] == i and indices[2] == COMING_BACK_HOME_INDEX]),
                sense=GRB.EQUAL, rhs=1,
                name=f"EndFlowConstraint[{i}]"
            )
        self._model.update()

    #############################
    # - Time window constraints #
    #############################

    def _add_time_window_constraints(self):

        # Case of models with tasks covering assumption
        if self.is_making_all_tasks_covered:

            # Bounds on tasks' performance times
            for j in self._data.tasks_indices:
                # Lower bound on task's performance time
                self._model.addLConstr(
                    self.vars_T[j],
                    sense=GRB.GREATER_EQUAL, rhs=self._data.get_task_by_index(j).start_time_lb,
                    name=f"TaskTWLBConstraint[{j}]"
                )

                # Upper bound on task's performance time
                self._model.addLConstr(
                    self.vars_T[j] + self._data.get_task_by_index(j).duration,
                    sense=GRB.LESS_EQUAL, rhs=self._data.get_task_by_index(j).end_time_ub,
                    name=f"TaskTWUBConstraint[{j}]"
                )

        # Case of models without tasks covering assumption
        else:

            # Bounds on tasks' performance times
            for j in self._data.tasks_indices:
                # Lower bound on task's performance time
                self._model.addLConstr(
                    self.vars_T[j] -
                    grb.quicksum(
                        [self.vars_U[(i, j, k, n)] * self._data.get_task_by_index(j).TWs[n].lower_bound
                         for i in self._data.employees_indices
                         for k in self._data.get_hyp_activities_indices(
                            employee_index=i, including_departure=False, including_comeback=True
                        ) if k != j
                         for n in self._data.get_hyp_activities_TW_indices(
                            employee_index=i, activity_index=j
                        )
                         ]
                    ),
                    sense=GRB.GREATER_EQUAL, rhs=0,
                    name=f"TaskTWLBConstraint[{j}]"
                )

                # Upper bound on task's performance time
                self._model.addLConstr(
                    self.vars_T[j] + self.vars_X[j] * self._data.get_task_by_index(j).duration -
                    grb.quicksum(
                        [self.vars_U[(i, j, k, n)] * self._data.get_task_by_index(j).TWs[n].upper_bound
                         for i in self._data.employees_indices
                         for k in self._data.get_hyp_activities_indices(
                            employee_index=i, including_departure=False, including_comeback=True
                        ) if k != j
                         for n in self._data.get_hyp_activities_TW_indices(
                            employee_index=i, activity_index=j
                        )
                         ]
                    ),
                    sense=GRB.LESS_EQUAL, rhs=0,
                    name=f"TaskTWUBConstraint[{j}]"
                )

            # Bounds on performance times of lunch breaks
            if self.is_considering_lunch_break:
                for i in self._data.employees_indices:
                    # Lower bound on lunch break's performance time
                    self._model.addLConstr(
                        self.vars_L[i], sense=GRB.GREATER_EQUAL, rhs=self._data.instance.lunch_break_time_LB,
                        name=f"LunchBreakTWLBConstraint[{i}]"
                    )
                    # Upper bound on lunch break's performance time
                    self._model.addLConstr(
                        self.vars_L[i], sense=GRB.LESS_EQUAL,
                        rhs=self._data.instance.lunch_break_time_UB - self._data.instance.lunch_break_duration,
                        name=f"LunchBreakTWUBConstraint[{i}]"
                    )

        self._model.update()

    ###############################
    # - Time sequence constraints #
    ###############################

    def _add_time_sequence_constraints(self):
        # Departure-to-first-task time sequence
        for k in self._data.tasks_indices:
            self._model.addLConstr(
                grb.quicksum([self.vars_U[(i, LEAVING_HOME_INDEX, k, n)] * (
                                self._data.get_employee_by_index(i).start_time_lb +
                                self._data.get_traveling_duration(i, LEAVING_HOME_INDEX, k)) +
                              (0 if not self.is_considering_lunch_break else
                               self.vars_V[(i, LEAVING_HOME_INDEX, k)] * self._data.instance.lunch_break_duration)
                              for i in self._data.employees_indices
                              for n in self._data.get_hyp_activities_TW_indices(i, LEAVING_HOME_INDEX)]) -
                self.vars_T[k],
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"DepartureToFirstTaskTimeSequenceConstraint[{k}]"
            )
        # Departure-to-first-task-if-unavailability time sequence
        for i in self._data.employees_indices:
            for k in self._data.get_employee_unavailabilities_indices(i):
                self._model.addLConstr(
                    grb.quicksum([self.vars_U[(i, LEAVING_HOME_INDEX, k, n)] * (
                                    self._data.get_traveling_duration(i, LEAVING_HOME_INDEX, k)) +
                                  (0 if not self.is_considering_lunch_break else
                                   self.vars_V[(i, LEAVING_HOME_INDEX, k)] * self._data.instance.lunch_break_duration)
                                  for n in self._data.get_hyp_activities_TW_indices(i, LEAVING_HOME_INDEX)]) -
                    self._data.get_hyp_activity_by_indices(i, k).start_time_lb,
                    sense=GRB.LESS_EQUAL, rhs=0,
                    name=f"DepartureToFirstTaskIfUnavailabilityTimeSequenceConstraint[{i},{k}]"
                )
        # Between-two-tasks time sequence
        for j in self._data.tasks_indices:
            for k in self._data.tasks_indices:
                if k != j:
                    self._model.addLConstr(
                        self.vars_T[j] +
                        grb.quicksum([
                            grb.quicksum([self.vars_U[(i, j, k, n)] 
                                          for n in self._data.get_hyp_activities_TW_indices(i, j)]) * 
                            (self._data.get_task_by_index(j).duration + self._data.get_traveling_duration(i, j, k) +
                             self._data.get_task_by_index(j).end_time_ub) +
                            (0 if not self.is_considering_lunch_break else
                             self.vars_V[(i, j, k)] * self._data.instance.lunch_break_duration)
                            for i in self._data.employees_indices
                        ]) - self.vars_T[k],
                        sense=GRB.LESS_EQUAL, rhs=self._data.get_task_by_index(j).end_time_ub,
                        name=f"TaskToTaskTimeSequenceConstraint[{j},{k}]"
                    )
        # Task-to-unavailability time sequence
        for i in self._data.employees_indices:
            for j in self._data.tasks_indices:
                for k in self._data.get_employee_unavailabilities_indices(i):
                    self._model.addLConstr(
                        self.vars_T[j] +
                        grb.quicksum([self.vars_U[(i, j, k, n)]
                                      for n in self._data.get_hyp_activities_TW_indices(i, j)]) *
                        (self._data.get_task_by_index(j).duration + self._data.get_traveling_duration(i, j, k) +
                         self._data.get_task_by_index(j).end_time_ub) +
                        (0 if not self.is_considering_lunch_break else
                         self.vars_V[(i, j, k)] * self._data.instance.lunch_break_duration),
                        sense=GRB.LESS_EQUAL,
                        rhs=(self._data.get_employee_unavailability_by_indices(i, k).start_time_lb +
                             self._data.get_task_by_index(j).end_time_ub),
                        name=f"TaskToUnavailabilityTimeSequenceConstraint[{i},{j},{k}]"
                    )
        # Unavailability-to-task time sequence
        for i in self._data.employees_indices:
            for j in self._data.get_employee_unavailabilities_indices(i):
                for k in self._data.tasks_indices:
                    self._model.addLConstr(
                        grb.quicksum([self.vars_U[(i, j, k, n)]
                                      for n in self._data.get_hyp_activities_TW_indices(i, j)]) *
                        (self._data.get_employee_unavailability_by_indices(i, j).end_time_ub +
                         self._data.get_traveling_duration(i, j, k)) +
                        (0 if not self.is_considering_lunch_break else
                         self.vars_V[(i, j, k)] * self._data.instance.lunch_break_duration) -
                        self.vars_T[k],
                        sense=GRB.LESS_EQUAL, rhs=0,
                        name=f"UnavailabilityToTaskTimeSequenceConstraint[{i},{j},{k}]"
                    )
        # Unavailability-to-unavailability time sequence
        for i in self._data.employees_indices:
            for j in self._data.get_employee_unavailabilities_indices(i):
                for k in self._data.get_employee_unavailabilities_indices(i):
                    if j != k:
                        self._model.addLConstr(
                            grb.quicksum([self.vars_U[(i, j, k, n)]
                                          for n in self._data.get_hyp_activities_TW_indices(i, j)]) *
                            (self._data.get_employee_unavailability_by_indices(i, j).end_time_ub +
                             self._data.get_traveling_duration(i, j, k)) +
                            (0 if not self.is_considering_lunch_break else
                             self.vars_V[(i, j, k)] * self._data.instance.lunch_break_duration) -
                            self._data.get_employee_unavailability_by_indices(i, k).start_time_lb,
                            sense=GRB.LESS_EQUAL, rhs=0,
                            name=f"UnavailabilityToUnavailabilityTimeSequenceConstraint[{i},{j},{k}]"
                        )
        # Last-task-to-comeback time sequence
        for j in self._data.tasks_indices:
            self._model.addLConstr(
                self.vars_T[j] +
                grb.quicksum([
                    grb.quicksum([self.vars_U[(i, j, COMING_BACK_HOME_INDEX, n)]
                                  for n in self._data.get_hyp_activities_TW_indices(i, j)]) *
                    (self._data.get_task_by_index(j).duration +
                     self._data.get_traveling_duration(i, j, COMING_BACK_HOME_INDEX) +
                     self._data.get_task_by_index(j).end_time_ub - self._data.get_employee_by_index(i).end_time_ub) +
                    (0 if not self.is_considering_lunch_break else
                     self.vars_V[(i, j, COMING_BACK_HOME_INDEX)] * self._data.instance.lunch_break_duration)
                    for i in self._data.employees_indices
                ]),
                sense=GRB.LESS_EQUAL, rhs=self._data.get_task_by_index(j).end_time_ub,
                name=f"TaskToComebackTimeSequenceConstraint[{j}]"
            )
        # # Last-task-if-unavailability-to-comeback time sequence
        # # Assumption: not needed otherwise it means the instance is infeasible
        # Task-before-lunch time sequence
        if self.is_considering_lunch_break:
            for i in self._data.employees_indices:
                for j in self._data.tasks_indices:
                    for k in self._data.get_hyp_activities_indices(i, False, True):
                        if k != j:
                            self._model.addLConstr(
                                self.vars_T[j] + self._data.get_task_by_index(j).duration - self.vars_L[i] +
                                self.vars_V[(i, j, k)] * self._data.get_task_by_index(j).end_time_ub,
                                sense=GRB.LESS_EQUAL, rhs=self._data.get_task_by_index(j).end_time_ub,
                                name=f"TaskBeforeLunchTimeSequenceConstraint[{i},{j},{k}]"
                            )
        # Unavailability-before-lunch time sequence
        if self.is_considering_lunch_break:
            for i in self._data.employees_indices:
                for j in self._data.get_employee_unavailabilities_indices(i):
                    for k in self._data.get_hyp_activities_indices(i, False, True):
                        if j != k:
                            self._model.addLConstr(
                                (self.vars_V[(i, j, k)] *
                                 self._data.get_employee_unavailability_by_indices(i, j).end_time_ub - self.vars_L[i]),
                                sense=GRB.LESS_EQUAL, rhs=0,
                                name=f"UnavailabilityBeforeLunchTimeSequenceConstraint[{i},{j},{k}]"
                            )
        # Task-after-lunch time sequence
        if self.is_considering_lunch_break:
            for i in self._data.employees_indices:
                for j in self._data.get_hyp_activities_indices(i, True, False):
                    for k in self._data.tasks_indices:
                        if j != k:
                            self._model.addLConstr(
                                (self.vars_L[i] + self._data.instance.lunch_break_duration) -
                                (self.vars_T[k] +
                                 (1 - self.vars_V[(i, j, k)]) * self._data.instance.lunch_break_time_UB),
                                sense=GRB.LESS_EQUAL, rhs=0,
                                name=f"TaskAfterLunchTimeSequenceConstraint[{i},{j},{k}]"
                            )
        # Unavailability-after-lunch time sequence
        if self.is_considering_lunch_break:
            for i in self._data.employees_indices:
                for j in self._data.get_hyp_activities_indices(
                        employee_index=i, including_departure=True, including_comeback=False):
                    for k in self._data.get_employee_unavailabilities_indices(i):
                        if j != k:
                            self._model.addLConstr(
                                self.vars_L[i] + self._data.instance.lunch_break_duration -
                                self._data.get_employee_unavailability_by_indices(i, k).start_time_lb +
                                self.vars_V[(i, j, k)] * self._data.instance.lunch_break_time_UB,
                                sense=GRB.LESS_EQUAL, rhs=self._data.instance.lunch_break_time_UB,
                                name=f"UnavailabilityAfterLunchTimeSequenceConstraint[{i},{j},{k}]"
                            )
        self._model.update()

    #############################
    # - Skill level constraints #
    #############################

    def _add_skill_level_constraints(self):
        for j in self._data.tasks_indices:
            self._model.addLConstr(
                grb.quicksum([self.vars_U[indices] * (self._data.get_employee_by_index(indices[0]).skill_level -
                                                      self._data.get_task_by_index(j).skill_level)
                              for indices in self.vars_U.keys() if indices[1] == j]),
                sense=GRB.GREATER_EQUAL, rhs=0,
                name=f"SkillLevelConstraint[{j}]"
            )

    ########################
    # Optimization process #
    ########################

    @property
    def solving_time_limit(self):
        """Solving time limit

        :returns: solving time limit in seconds (int)
        """
        return self._model.Params.timeLimit

    @solving_time_limit.setter
    def solving_time_limit(self, solving_time_limit: int):
        """Set solving time limit

        :param solving_time_limit: solving time limit in seconds (int)
        """
        self._model.Params.timeLimit = solving_time_limit

    def optimize(self, mute=True):
        if mute:
            self._model.params.outputflag = 0
        self._model.optimize()
        if self._model.Status == GRB.INFEASIBLE:
            print("IP model is infeasible")
            print("")
        elif self._model.Status == GRB.UNBOUNDED:
            print("IP model is unbounded")
            print("")
        elif self._model.Status == GRB.TIME_LIMIT:
            print("IP model solving was stopped as it reached given time limit")
            if self._model.SolCount > 0:
                print(f"but {self._model.SolCount} solutions were found")
                self._successful_IP_solving = True
            else:
                print(f"No solutions were found")
            print("")
        else:
            self._successful_IP_solving = True
        if self._successful_IP_solving:
            self._extract_solution()

    ##################
    # Solving method #
    ##################

    @property
    def _solving_method_id(self):
        return SOLVING_METHOD_IP

    @property
    def optimality_gap(self):
        if self._successful_IP_solving:
            return np.round(self._model.MIPGap, 5)
        else:
            raise AttributeError("There is no solution stored")

    @property
    def solving_run_time(self):
        if self._successful_IP_solving:
            return np.round(self._model.Runtime, 3)
        else:
            raise AttributeError("There is no solution stored")

    @property
    def objective_value(self):
        if self._successful_IP_solving:
            return np.round(self._model.objVal, 3)
        else:
            raise AttributeError("There is no solution stored")

    ############
    # Solution #
    ############

    def _initialize_solution(self):
        self._solution = SolutionOpti(self._data.instance, solving_method_id=self._solving_method_id)

    def _extract_solution(self):
        # Initialize solution
        self._initialize_solution()
        self.solution.solving_method_parameters = {
            'Traveling duration weight': self.weight_traveling_duration,
            'Working duration weight': self.weight_working_duration,
            'Number of realized tasks weight': self.weight_nb_realized_tasks
        }
        self.solution.solving_time = self.solving_run_time
        self.solution.optimality_gap = self.optimality_gap
        self.solution.objective_value = self.objective_value
        # Results about tasks
        for j in self._data.tasks_indices:
            task = self._data.get_task_by_index(j)
            if self.is_making_all_tasks_covered:
                performed = True
            else:
                performed = self.vars_X[j].x > 0.99
            self.solution.set_task_performance_status(task, performed)
            if performed:
                self.solution.set_task_start_time(task, int(self.vars_T[j].x))
        for i in self._data.employees_indices:
            for j in self._data.tasks_indices:
                for k in self._data.get_hyp_activities_indices(i, False, True):
                    if j != k:
                        for n in self._data.get_hyp_activities_TW_indices(i, j):
                            if self.vars_U[(i, j, k, n)].x > 0.99:
                                self.solution.set_task_assignee(self._data.get_task_by_index(j),
                                                                self._data.get_employee_by_index(i))
        # Compute full solution
        self.solution.compute_sequences_based_on_tasks_performances()

    @property
    def solution(self):
        if self.has_solution:
            return self._solution
        else:
            raise AttributeError("There is no solution")

    @property
    def has_solution(self):
        return self._solution is not None
