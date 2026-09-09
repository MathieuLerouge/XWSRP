# Standard library
from typing import Optional

# Third-party libraries
import numpy as np
import pyomo.environ as pyo

# Local libraries
from main_configuration import SOLVER_NAME
from src.optimization.milp.milpmodelindex import MILPModelIndex, LEAVING_HOME_INDEX, COMING_BACK_HOME_INDEX
from src.optimization.milp.solver.outcome import Outcome
from src.optimization.milp.solver.solver import Solver
from src.optimization.solution import SolutionOpti
from src.utils.constants import SOLUTION_SOLVING_METHOD_SYMBOL_BIS

# Global variables
TRAVELING_DURATION_WEIGHT_KEY = 'traveling_duration'
WORKING_DURATION_WEIGHT_KEY = 'working_duration'
NB_PERFORMED_TASKS_WEIGHT_KEY = 'nb_performed_tasks'
SOLVING_METHOD_IP = 'IP'


#############
# MILPModel #
#############

class MILPModel:
    """
    Whole-workforce MILP formulation of the WSRP: assigns tasks to employees and sequences each
    employee's activities, respecting skill, time-window, unavailability and lunch-break constraints.
    """

    def __init__(self, instance):
        """
        Args:
            instance: the instance to build the model for.
        """
        self._name = f"{instance.core_name}{SOLUTION_SOLVING_METHOD_SYMBOL_BIS}{self._solving_method_id}"
        self._data = MILPModelIndex(instance)
        self._weights: dict[str, Optional[int]] = dict()
        if self._data.instance.must_cover_all_tasks:
            self.weight_traveling_duration = 1
            self.weight_working_duration = None
            self.weight_nb_performed_tasks = None
        else:
            self.weight_traveling_duration = 1
            self.weight_working_duration = -10
            self.weight_nb_performed_tasks = None
        self._decision_variables: dict[str, pyo.Var] = dict()
        self._solving_time_limit: Optional[int] = None
        self._solve_outcome: Optional[Outcome] = None
        self._solution: Optional[SolutionOpti] = None
        self._model = pyo.ConcreteModel(name=self._name)
        self._add_decision_variables()
        self._add_objective_function()
        self._add_constraints()

    @property
    def _solving_method_id(self):
        """The solving-method identifier used to build this model's name and its solutions'."""
        return SOLVING_METHOD_IP

    @property
    def name(self):
        """This model's name."""
        return self._name

    ##############
    # Assumption #
    ##############

    @property
    def is_considering_lunch_break(self):
        """Whether this model accounts for a lunch break."""
        return self._data.instance.has_lunch_break

    @property
    def is_considering_tasks_unavailabilities(self):
        """Whether this model accounts for tasks' unavailabilities."""
        return self._data.instance.has_task_unavailabilities

    def display(self):
        """Print the underlying Pyomo model's variables, objective and constraints to the console."""
        self._model.display()

    ######################
    # Decision variables #
    ######################

    @property
    def vars_X(self):
        """The X decision variables: whether each task is performed (only defined when tasks covering is optional)."""
        return self._decision_variables['X']

    @vars_X.setter
    def vars_X(self, X: pyo.Var):
        self._decision_variables['X'] = X

    @property
    def vars_T(self):
        """The T decision variables: each task's performance start time."""
        return self._decision_variables['T']

    @vars_T.setter
    def vars_T(self, T: pyo.Var):
        self._decision_variables['T'] = T

    @property
    def vars_L(self):
        """The L decision variables: each employee's lunch-break start time."""
        return self._decision_variables['L']

    @vars_L.setter
    def vars_L(self, L: pyo.Var):
        self._decision_variables['L'] = L

    @property
    def vars_U(self):
        """The U decision variables: whether each employee/activity/activity/time-window combination is used."""
        return self._decision_variables['U']

    @vars_U.setter
    def vars_U(self, U: pyo.Var):
        self._decision_variables['U'] = U

    @property
    def vars_V(self):
        """The V decision variables: whether each employee/activity/activity combination places the lunch break."""
        return self._decision_variables['V']

    @vars_V.setter
    def vars_V(self, V: pyo.Var):
        self._decision_variables['V'] = V

    def _add_decision_variables(self):
        # Add X decision variables
        if not self._data.instance.must_cover_all_tasks:
            self._model.X = pyo.Var(self._data.tasks_indices, domain=pyo.Binary)
            self.vars_X = self._model.X
        # Add T decision variables
        # NB: NonNegativeIntegers replicates Gurobi's implicit default lower bound of 0 for integer variables
        self._model.T = pyo.Var(self._data.tasks_indices, domain=pyo.NonNegativeIntegers)
        self.vars_T = self._model.T
        # TODO remove decision variables L which are no longer useful
        # Add L decision variables
        if self.is_considering_lunch_break:
            self._model.L = pyo.Var(self._data.employees_indices, domain=pyo.NonNegativeIntegers)
            self.vars_L = self._model.L
        self._model.U = pyo.Var(
            [(i, j, k, n) for i in self._data.employees_indices
             for j in self._data.get_hyp_activities_indices(i, True, False)
             for k in self._data.get_hyp_activities_indices(i, False, True) if k != j
             for n in self._data.get_hyp_activities_TW_indices(i, j)],
            domain=pyo.Binary)
        self.vars_U = self._model.U
        # Add V decision variables
        if self._data.instance.has_lunch_break:
            self._model.V = pyo.Var(
                [(i, j, k) for i in self._data.employees_indices
                 for j in self._data.get_hyp_activities_indices(i, True, False)
                 for k in self._data.get_hyp_activities_indices(i, False, True) if k != j],
                domain=pyo.Binary)
            self.vars_V = self._model.V

    ######################
    # Objective function #
    ######################

    @property
    def weight_traveling_duration(self):
        """The traveling-duration term's weight in the objective function, or 0 if unset."""
        if self._weights[TRAVELING_DURATION_WEIGHT_KEY] is not None:
            return self._weights[TRAVELING_DURATION_WEIGHT_KEY]
        else:
            return 0

    @weight_traveling_duration.setter
    def weight_traveling_duration(self, weight):
        self._weights[TRAVELING_DURATION_WEIGHT_KEY] = weight

    @property
    def weight_working_duration(self):
        """The working-duration term's weight in the objective function, or 0 if unset."""
        if self._weights[WORKING_DURATION_WEIGHT_KEY] is not None:
            return self._weights[WORKING_DURATION_WEIGHT_KEY]
        else:
            return 0

    @weight_working_duration.setter
    def weight_working_duration(self, weight):
        """
        Args:
            weight: the working-duration term's weight, or None to leave it out of the objective.

        Raises:
            ValueError: if weight is not None while the instance assumes all tasks must be covered
                (in which case working duration is constant and cannot be optimized against).
        """
        if self._data.instance.must_cover_all_tasks and weight is not None:
            raise ValueError("The working duration weight must be None "
                             "when it is assumed that all tasks must be covered")
        self._weights[WORKING_DURATION_WEIGHT_KEY] = weight

    @property
    def weight_nb_performed_tasks(self):
        """The number-of-performed-tasks term's weight in the objective function, or 0 if unset."""
        if self._weights[NB_PERFORMED_TASKS_WEIGHT_KEY] is not None:
            return self._weights[NB_PERFORMED_TASKS_WEIGHT_KEY]
        else:
            return 0

    @weight_nb_performed_tasks.setter
    def weight_nb_performed_tasks(self, weight):
        """
        Args:
            weight: the number-of-performed-tasks term's weight, or None to leave it out of the objective.

        Raises:
            ValueError: if weight is not None while the instance assumes all tasks must be covered
                (in which case the number of performed tasks is constant and cannot be optimized against).
        """
        if self._data.instance.must_cover_all_tasks and weight is not None:
            raise ValueError("The number of performed tasks weight must be None "
                             "when it is assumed that all tasks must be covered")
        self._weights[NB_PERFORMED_TASKS_WEIGHT_KEY] = weight

    def _add_objective_function(self):

        objective = 0

        # Traveling duration
        if self.weight_traveling_duration is not None:
            traveling_duration = pyo.quicksum([
                self.vars_U[indices] *
                self._data.get_traveling_duration(
                    employee_index=indices[0], activity_index1=indices[1], activity_index2=indices[2]
                )
                for indices in self.vars_U.keys()
            ])
            objective += self.weight_traveling_duration * traveling_duration

        # Working duration
        if self.weight_working_duration is not None and self.weight_working_duration != 0:
            working_duration = pyo.quicksum([
                self.vars_X[j] * self._data.get_task_by_index(j).duration for j in self._data.tasks_indices
            ])
            objective += self.weight_working_duration * working_duration

        # Number of performed tasks
        if self.weight_nb_performed_tasks is not None and self.weight_working_duration != 0:
            nb_performed_tasks = pyo.quicksum([self.vars_X[j] for j in self._data.tasks_indices])
            objective += self.weight_nb_performed_tasks * nb_performed_tasks

        self._model.objective = pyo.Objective(expr=objective, sense=pyo.minimize)

    ###############
    # Constraints #
    ###############

    def _add_constraints(self):
        self._add_covering_constraints()
        self._add_flow_constraints()
        self._add_time_window_constraints()
        self._add_time_sequence_constraints()
        self._add_skill_level_constraints()

    ######################################
    # Constraints - Covering constraints #
    ######################################

    def _add_covering_constraints(self):
        # Add tasks covering constraints
        if self._data.instance.must_cover_all_tasks:
            for j in self._data.tasks_indices:
                self._model.add_component(
                    f"TaskCoveringConstraint[{j}]",
                    pyo.Constraint(expr=(
                        pyo.quicksum([
                            self.vars_U[(i, j, k, n)]
                            for i in self._data.employees_indices
                            for k in self._data.get_hyp_activities_indices(i, False, True) if k != j
                            for n in self._data.get_hyp_activities_TW_indices(i, j)
                        ]) == 1
                    ))
                )
        else:
            for j in self._data.tasks_indices:
                self._model.add_component(
                    f"TaskCoveringConstraint[{j}]",
                    pyo.Constraint(expr=(
                        pyo.quicksum([
                            self.vars_U[(i, j, k, n)]
                            for i in self._data.employees_indices
                            for k in self._data.get_hyp_activities_indices(i, False, True) if k != j
                            for n in self._data.get_hyp_activities_TW_indices(i, j)
                        ]) - self.vars_X[j] == 0
                    ))
                )
        # Add unavailability covering if any
        for i in self._data.employees_indices:
            for j in self._data.get_employee_unavailabilities_indices(i):
                self._model.add_component(
                    f"UnavailabilityCoveringConstraint[{i},{j}]",
                    pyo.Constraint(expr=(
                        pyo.quicksum([
                            self.vars_U[(i, j, k, n)]
                            for k in self._data.get_hyp_activities_indices(i, False, True) if k != j
                            for n in self._data.get_hyp_activities_TW_indices(i, j)
                        ]) == 1
                    ))
                )
        # Add lunch break covering if any
        if self.is_considering_lunch_break:
            for i in self._data.employees_indices:
                self._model.add_component(
                    f"LunchBreakCoveringConstraint[{i}]",
                    pyo.Constraint(expr=(
                        pyo.quicksum([
                            self.vars_V[(i, j, k)]
                            for j in self._data.get_hyp_activities_indices(i, True, False)
                            for k in self._data.get_hyp_activities_indices(i, False, True) if k != j
                        ]) == 1
                    ))
                )
            for i in self._data.employees_indices:
                for j in self._data.get_hyp_activities_indices(i, True, False):
                    for k in self._data.get_hyp_activities_indices(i, False, True):
                        if k != j:
                            self._model.add_component(
                                f"TaskCoveringImplicationConstraint[{i},{j},{k}]",
                                pyo.Constraint(expr=(
                                    self.vars_V[(i, j, k)] -
                                    pyo.quicksum([
                                        self.vars_U[(i, j, k, n)]
                                        for n in self._data.get_hyp_activities_TW_indices(i, j)
                                    ]) <= 0
                                ))
                            )

    ##################################
    # Constraints - Flow constraints #
    ##################################

    def _add_flow_constraints(self):
        for i in self._data.employees_indices:
            # Add flow constraint at start locations
            self._model.add_component(
                f"StartFlowConstraint[{i}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([
                        self.vars_U[indices] for indices in self.vars_U.keys()
                        if indices[0] == i and indices[1] == LEAVING_HOME_INDEX
                    ]) == 1
                ))
            )
            # Add flow constraints around tasks and unavailabilities if any
            for k in self._data.get_hyp_activities_indices(i, False, False, True):
                self._model.add_component(
                    f"FlowConstraint[{i},{k}]",
                    pyo.Constraint(expr=(
                        pyo.quicksum([
                            self.vars_U[indices] for indices in self.vars_U.keys()
                            if indices[0] == i and indices[2] == k
                        ]) -
                        pyo.quicksum([
                            self.vars_U[indices] for indices in self.vars_U.keys()
                            if indices[0] == i and indices[1] == k
                        ]) == 0
                    ))
                )
            # Add flow constraint at end locations
            self._model.add_component(
                f"EndFlowConstraint[{i}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([
                        self.vars_U[indices] for indices in self.vars_U.keys()
                        if indices[0] == i and indices[2] == COMING_BACK_HOME_INDEX
                    ]) == 1
                ))
            )

    #########################################
    # Constraints - Time window constraints #
    #########################################

    def _add_time_window_constraints(self):

        # Case of models with tasks covering assumption
        if self._data.instance.must_cover_all_tasks:

            # Bounds on tasks' performance times
            for j in self._data.tasks_indices:
                # Lower bound on task's performance time
                self._model.add_component(
                    f"TaskTWLBConstraint[{j}]",
                    pyo.Constraint(expr=(self.vars_T[j] >= self._data.get_task_by_index(j).start_time_lb))
                )

                # Upper bound on task's performance time
                self._model.add_component(
                    f"TaskTWUBConstraint[{j}]",
                    pyo.Constraint(expr=(
                        self.vars_T[j] + self._data.get_task_by_index(j).duration <=
                        self._data.get_task_by_index(j).end_time_ub
                    ))
                )

        # Case of models without tasks covering assumption
        else:

            # Bounds on tasks' performance times
            for j in self._data.tasks_indices:
                # Lower bound on task's performance time
                self._model.add_component(
                    f"TaskTWLBConstraint[{j}]",
                    pyo.Constraint(expr=(
                        self.vars_T[j] -
                        pyo.quicksum([
                            self.vars_U[(i, j, k, n)] * self._data.get_task_by_index(j).time_windows[n].lower_bound
                            for i in self._data.employees_indices
                            for k in self._data.get_hyp_activities_indices(
                                employee_index=i, including_departure=False, including_comeback=True
                            ) if k != j
                            for n in self._data.get_hyp_activities_TW_indices(employee_index=i, activity_index=j)
                        ]) >= 0
                    ))
                )

                # Upper bound on task's performance time
                self._model.add_component(
                    f"TaskTWUBConstraint[{j}]",
                    pyo.Constraint(expr=(
                        self.vars_T[j] + self.vars_X[j] * self._data.get_task_by_index(j).duration -
                        pyo.quicksum([
                            self.vars_U[(i, j, k, n)] * self._data.get_task_by_index(j).time_windows[n].upper_bound
                            for i in self._data.employees_indices
                            for k in self._data.get_hyp_activities_indices(
                                employee_index=i, including_departure=False, including_comeback=True
                            ) if k != j
                            for n in self._data.get_hyp_activities_TW_indices(employee_index=i, activity_index=j)
                        ]) <= 0
                    ))
                )

            # Bounds on performance times of lunch breaks
            if self.is_considering_lunch_break:
                for i in self._data.employees_indices:
                    # Lower bound on lunch break's performance time
                    self._model.add_component(
                        f"LunchBreakTWLBConstraint[{i}]",
                        pyo.Constraint(expr=(self.vars_L[i] >= self._data.instance.lunch_break_time_lb))
                    )
                    # Upper bound on lunch break's performance time
                    self._model.add_component(
                        f"LunchBreakTWUBConstraint[{i}]",
                        pyo.Constraint(expr=(
                            self.vars_L[i] <=
                            self._data.instance.lunch_break_time_ub - self._data.instance.lunch_break_duration
                        ))
                    )

    ###########################################
    # Constraints - Time sequence constraints #
    ###########################################

    def _add_time_sequence_constraints(self):
        # Departure-to-first-task time sequence
        for k in self._data.tasks_indices:
            self._model.add_component(
                f"DepartureToFirstTaskTimeSequenceConstraint[{k}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([
                        self.vars_U[(i, LEAVING_HOME_INDEX, k, n)] * (
                            self._data.get_employee_by_index(i).start_time_lb +
                            self._data.get_traveling_duration(i, LEAVING_HOME_INDEX, k)
                        ) +
                        (0 if not self.is_considering_lunch_break else
                         self.vars_V[(i, LEAVING_HOME_INDEX, k)] * self._data.instance.lunch_break_duration)
                        for i in self._data.employees_indices
                        for n in self._data.get_hyp_activities_TW_indices(i, LEAVING_HOME_INDEX)
                    ]) -
                    self.vars_T[k] <= 0
                ))
            )
        # Departure-to-first-task-if-unavailability time sequence
        for i in self._data.employees_indices:
            for k in self._data.get_employee_unavailabilities_indices(i):
                self._model.add_component(
                    f"DepartureToFirstTaskIfUnavailabilityTimeSequenceConstraint[{i},{k}]",
                    pyo.Constraint(expr=(
                        pyo.quicksum([
                            self.vars_U[(i, LEAVING_HOME_INDEX, k, n)] *
                            self._data.get_traveling_duration(i, LEAVING_HOME_INDEX, k) +
                            (0 if not self.is_considering_lunch_break else
                             self.vars_V[(i, LEAVING_HOME_INDEX, k)] * self._data.instance.lunch_break_duration)
                            for n in self._data.get_hyp_activities_TW_indices(i, LEAVING_HOME_INDEX)
                        ]) -
                        self._data.get_hyp_activity_by_indices(i, k).start_time_lb <= 0
                    ))
                )
        # Between-two-tasks time sequence
        for j in self._data.tasks_indices:
            for k in self._data.tasks_indices:
                if k != j:
                    self._model.add_component(
                        f"TaskToTaskTimeSequenceConstraint[{j},{k}]",
                        pyo.Constraint(expr=(
                            self.vars_T[j] +
                            pyo.quicksum([
                                pyo.quicksum([
                                    self.vars_U[(i, j, k, n)]
                                    for n in self._data.get_hyp_activities_TW_indices(i, j)
                                ]) *
                                (self._data.get_task_by_index(j).duration +
                                 self._data.get_traveling_duration(i, j, k) +
                                 self._data.get_task_by_index(j).end_time_ub) +
                                (0 if not self.is_considering_lunch_break else
                                 self.vars_V[(i, j, k)] * self._data.instance.lunch_break_duration)
                                for i in self._data.employees_indices
                            ]) - self.vars_T[k] <= self._data.get_task_by_index(j).end_time_ub
                        ))
                    )
        # Task-to-unavailability time sequence
        for i in self._data.employees_indices:
            for j in self._data.tasks_indices:
                for k in self._data.get_employee_unavailabilities_indices(i):
                    self._model.add_component(
                        f"TaskToUnavailabilityTimeSequenceConstraint[{i},{j},{k}]",
                        pyo.Constraint(expr=(
                            self.vars_T[j] +
                            pyo.quicksum([
                                self.vars_U[(i, j, k, n)]
                                for n in self._data.get_hyp_activities_TW_indices(i, j)
                            ]) *
                            (self._data.get_task_by_index(j).duration + self._data.get_traveling_duration(i, j, k) +
                             self._data.get_task_by_index(j).end_time_ub) +
                            (0 if not self.is_considering_lunch_break else
                             self.vars_V[(i, j, k)] * self._data.instance.lunch_break_duration) <=
                            (self._data.get_employee_unavailability_by_indices(i, k).start_time_lb +
                             self._data.get_task_by_index(j).end_time_ub)
                        ))
                    )
        # Unavailability-to-task time sequence
        for i in self._data.employees_indices:
            for j in self._data.get_employee_unavailabilities_indices(i):
                for k in self._data.tasks_indices:
                    self._model.add_component(
                        f"UnavailabilityToTaskTimeSequenceConstraint[{i},{j},{k}]",
                        pyo.Constraint(expr=(
                            pyo.quicksum([
                                self.vars_U[(i, j, k, n)]
                                for n in self._data.get_hyp_activities_TW_indices(i, j)
                            ]) *
                            (self._data.get_employee_unavailability_by_indices(i, j).end_time_ub +
                             self._data.get_traveling_duration(i, j, k)) +
                            (0 if not self.is_considering_lunch_break else
                             self.vars_V[(i, j, k)] * self._data.instance.lunch_break_duration) -
                            self.vars_T[k] <= 0
                        ))
                    )
        # Unavailability-to-unavailability time sequence
        for i in self._data.employees_indices:
            for j in self._data.get_employee_unavailabilities_indices(i):
                for k in self._data.get_employee_unavailabilities_indices(i):
                    if j != k:
                        self._model.add_component(
                            f"UnavailabilityToUnavailabilityTimeSequenceConstraint[{i},{j},{k}]",
                            pyo.Constraint(expr=(
                                pyo.quicksum([
                                    self.vars_U[(i, j, k, n)]
                                    for n in self._data.get_hyp_activities_TW_indices(i, j)
                                ]) *
                                (self._data.get_employee_unavailability_by_indices(i, j).end_time_ub +
                                 self._data.get_traveling_duration(i, j, k)) +
                                (0 if not self.is_considering_lunch_break else
                                 self.vars_V[(i, j, k)] * self._data.instance.lunch_break_duration) -
                                self._data.get_employee_unavailability_by_indices(i, k).start_time_lb <= 0
                            ))
                        )
        # Last-task-to-comeback time sequence
        for j in self._data.tasks_indices:
            self._model.add_component(
                f"TaskToComebackTimeSequenceConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] +
                    pyo.quicksum([
                        pyo.quicksum([
                            self.vars_U[(i, j, COMING_BACK_HOME_INDEX, n)]
                            for n in self._data.get_hyp_activities_TW_indices(i, j)
                        ]) *
                        (self._data.get_task_by_index(j).duration +
                         self._data.get_traveling_duration(i, j, COMING_BACK_HOME_INDEX) +
                         self._data.get_task_by_index(j).end_time_ub -
                         self._data.get_employee_by_index(i).end_time_ub) +
                        (0 if not self.is_considering_lunch_break else
                         self.vars_V[(i, j, COMING_BACK_HOME_INDEX)] * self._data.instance.lunch_break_duration)
                        for i in self._data.employees_indices
                    ]) <= self._data.get_task_by_index(j).end_time_ub
                ))
            )
        # # Last-task-if-unavailability-to-comeback time sequence
        # # Assumption: not needed otherwise it means the instance is infeasible
        # Task-before-lunch time sequence
        if self.is_considering_lunch_break:
            for i in self._data.employees_indices:
                for j in self._data.tasks_indices:
                    for k in self._data.get_hyp_activities_indices(i, False, True):
                        if k != j:
                            self._model.add_component(
                                f"TaskBeforeLunchTimeSequenceConstraint[{i},{j},{k}]",
                                pyo.Constraint(expr=(
                                    self.vars_T[j] + self._data.get_task_by_index(j).duration - self.vars_L[i] +
                                    self.vars_V[(i, j, k)] * self._data.get_task_by_index(j).end_time_ub <=
                                    self._data.get_task_by_index(j).end_time_ub
                                ))
                            )
        # Unavailability-before-lunch time sequence
        if self.is_considering_lunch_break:
            for i in self._data.employees_indices:
                for j in self._data.get_employee_unavailabilities_indices(i):
                    for k in self._data.get_hyp_activities_indices(i, False, True):
                        if j != k:
                            self._model.add_component(
                                f"UnavailabilityBeforeLunchTimeSequenceConstraint[{i},{j},{k}]",
                                pyo.Constraint(expr=(
                                    (self.vars_V[(i, j, k)] *
                                     self._data.get_employee_unavailability_by_indices(i, j).end_time_ub -
                                     self.vars_L[i]) <= 0
                                ))
                            )
        # Task-after-lunch time sequence
        if self.is_considering_lunch_break:
            for i in self._data.employees_indices:
                for j in self._data.get_hyp_activities_indices(i, True, False):
                    for k in self._data.tasks_indices:
                        if j != k:
                            self._model.add_component(
                                f"TaskAfterLunchTimeSequenceConstraint[{i},{j},{k}]",
                                pyo.Constraint(expr=(
                                    (self.vars_L[i] + self._data.instance.lunch_break_duration) -
                                    (self.vars_T[k] +
                                     (1 - self.vars_V[(i, j, k)]) * self._data.instance.lunch_break_time_ub) <= 0
                                ))
                            )
        # Unavailability-after-lunch time sequence
        if self.is_considering_lunch_break:
            for i in self._data.employees_indices:
                for j in self._data.get_hyp_activities_indices(
                        employee_index=i, including_departure=True, including_comeback=False):
                    for k in self._data.get_employee_unavailabilities_indices(i):
                        if j != k:
                            self._model.add_component(
                                f"UnavailabilityAfterLunchTimeSequenceConstraint[{i},{j},{k}]",
                                pyo.Constraint(expr=(
                                    self.vars_L[i] + self._data.instance.lunch_break_duration -
                                    self._data.get_employee_unavailability_by_indices(i, k).start_time_lb +
                                    self.vars_V[(i, j, k)] * self._data.instance.lunch_break_time_ub <=
                                    self._data.instance.lunch_break_time_ub
                                ))
                            )

    #########################################
    # Constraints - Skill level constraints #
    #########################################

    def _add_skill_level_constraints(self):
        for j in self._data.tasks_indices:
            self._model.add_component(
                f"SkillLevelConstraint[{j}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([
                        self.vars_U[indices] * (
                            self._data.get_employee_by_index(indices[0]).skill_level -
                            self._data.get_task_by_index(j).skill_level
                        )
                        for indices in self.vars_U.keys() if indices[1] == j
                    ]) >= 0
                ))
            )

    ###########
    # Solving #
    ###########

    @property
    def solving_time_limit(self):
        """Solving time limit in seconds, or None for no limit."""
        return self._solving_time_limit

    @solving_time_limit.setter
    def solving_time_limit(self, solving_time_limit: int):
        """
        Set solving time limit.

        Args:
            solving_time_limit: solving time limit in seconds.
        """
        self._solving_time_limit = solving_time_limit

    def _initialize_solution(self):
        self._solution = SolutionOpti(self._data.instance, solving_method_id=self._solving_method_id)

    def solve(self, mute=True, solver_name: str = SOLVER_NAME) -> Outcome:
        """
        Solve the model with the configured MILP backend.

        Args:
            mute: if True, suppress the solver's own console output.
            solver_name: which MILP backend to use (SOLVER_HIGHS or SOLVER_GUROBI from
                src.optimization.milp.solver.solver), defaults to main_configuration.SOLVER_NAME.

        Returns:
            the Outcome describing the solve, with its solution set if a feasible solution
            (an incumbent) was found.
        """
        solver = Solver(solver_name, mute=mute, time_limit=self._solving_time_limit)
        self._solve_outcome = solver.solve(self._model)
        if self._solve_outcome.is_infeasible:
            print("IP model is infeasible")
            print("")
        elif self._solve_outcome.is_unbounded:
            print("IP model is unbounded")
            print("")
        elif self._solve_outcome.is_time_limit:
            print("IP model solving was stopped as it reached given time limit")
            if self._solve_outcome.has_incumbent:
                print("but a solution was found")
            else:
                print("No solutions were found")
            print("")
        if self._solve_outcome.has_incumbent:
            self._extract_solution()
            self._solve_outcome.solution = self.solution
        return self._solve_outcome

    ###########
    # Results #
    ###########

    def _extract_solution(self):
        # Initialize solution
        self._initialize_solution()
        self.solution.solving_method_parameters = {
            'Traveling duration weight': self.weight_traveling_duration,
            'Working duration weight': self.weight_working_duration,
            'Number of performed tasks weight': self.weight_nb_performed_tasks
        }
        self.solution.solving_time = self.solving_run_time
        self.solution.optimality_gap = self.optimality_gap
        self.solution.objective_value = self.objective_value
        # Results about tasks
        for j in self._data.tasks_indices:
            task = self._data.get_task_by_index(j)
            if self._data.instance.must_cover_all_tasks:
                performed = True
            else:
                performed = pyo.value(self.vars_X[j]) > 0.99
            self.solution.set_task_performance_status(task, performed)
            if performed:
                self.solution.set_task_start_time(task, round(pyo.value(self.vars_T[j])))
        for i in self._data.employees_indices:
            for j in self._data.tasks_indices:
                for k in self._data.get_hyp_activities_indices(i, False, True):
                    if j != k:
                        for n in self._data.get_hyp_activities_TW_indices(i, j):
                            if pyo.value(self.vars_U[(i, j, k, n)]) > 0.99:
                                self.solution.set_task_assignee(self._data.get_task_by_index(j),
                                                                self._data.get_employee_by_index(i))
        # Compute full solution
        self.solution.compute_sequences_based_on_tasks_performances()

    @property
    def solution(self):
        """
        This model's solution.

        Raises:
            AttributeError: if solve() hasn't been called yet, or found no feasible solution.
        """
        if self.has_solution:
            return self._solution
        else:
            raise AttributeError("There is no solution")

    @property
    def has_solution(self):
        """Whether a feasible solution has been found and stored."""
        return self._solution is not None

    @property
    def optimality_gap(self):
        """
        This model's solution's relative optimality gap.

        Raises:
            AttributeError: if solve() hasn't been called yet, or found no feasible solution.
        """
        if self._solve_outcome is not None and self._solve_outcome.has_incumbent:
            return np.round(self._solve_outcome.mip_gap, 5)
        else:
            raise AttributeError("There is no solution stored")

    @property
    def solving_run_time(self):
        """
        This model's solving run time, in seconds.

        Raises:
            AttributeError: if solve() hasn't been called yet, or found no feasible solution.
        """
        if self._solve_outcome is not None and self._solve_outcome.has_incumbent:
            return np.round(self._solve_outcome.run_time, 3)
        else:
            raise AttributeError("There is no solution stored")

    @property
    def objective_value(self):
        """
        This model's solution's objective value.

        Raises:
            AttributeError: if solve() hasn't been called yet, or found no feasible solution.
        """
        if self._solve_outcome is not None and self._solve_outcome.has_incumbent:
            return np.round(self._solve_outcome.objective_value, 3)
        else:
            raise AttributeError("There is no solution stored")
