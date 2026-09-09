# Standard library
from typing import Optional

# Third-party libraries
import numpy as np
import pyomo.environ as pyo

# Local libraries
from src.explaining.modeling.instance import EditableInstance
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.modeling.sequence import EditableSequence
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.step import Step
from src.modeling.task import Task
from src.optimization.heuristics.sequence import SequenceForHeuristics
from src.optimization.milp.solver.solver import Solver
from src.optimization.milp.subproblems.sequencemodel import SequenceModel, LEAVING_HOME_KEY, \
    COMING_BACK_HOME_KEY, create_activity_key

# Global variables
MAX_NB_ALTERATIONS = 2


###################################################
# IPModelForTransformationWithInstanceAlterations #
###################################################

class IPModelForTransformationWithInstanceAlterations(SequenceModel):
    """
    Base IP model to compute explanation content for answering counterfactual question about any transformation
    """

    def __init__(self, sequence: SequenceForHeuristics, pivot_task: Task,
                 instance_parameter_alteration_bounds: InstanceChanges = None,
                 solving_time_limit: int = None):
        """
        Return an IP model for transforming a sequence while allowing instance parameter alterations

        :param sequence: the sequence to optimize (SequenceForHeuristics)
        :param pivot_task: the task which plays a key role in the sequence optimization (Task)
        :param instance_parameter_alteration_bounds: the bounds of instance parameter alterations (InstanceChanges)
        :param solving_time_limit: the solving time limit in seconds (int)
        """
        self._pivot_task = pivot_task
        self._sequence = sequence
        self._instance_parameter_alteration_bounds = instance_parameter_alteration_bounds
        super().__init__(sequence.instance, sequence.employee, self._compute_candidate_tasks())
        if solving_time_limit is not None:
            self.solving_time_limit = solving_time_limit

    def _compute_candidate_tasks(self):
        """
        Return the list of candidate tasks i.e. the tasks that can be part of the employee's sequence
        NB: depending on the transformation, this method may need to be overridden

        :return: the list of candidate tasks (List[Task])
        """
        return self._sequence.get_contained_tasks() + [self._pivot_task]

    #########################################
    # Getters and setters - Candidate tasks #
    #########################################

    def _get_candidate_tasks_keys(self, including_pivot_task: bool = True):
        """
        Return the list of candidate tasks keys i.e. the keys of the tasks that can be part of the employee's sequence

        :return: the list of candidate tasks keys (List[str])
        """
        if including_pivot_task:
            return [task.name for task in self.candidate_tasks]
        else:
            return [task.name for task in self.candidate_tasks if task != self._pivot_task]

    ####################################
    # Getters and setters - Pivot task #
    ####################################

    @property
    def _pivot_task_key(self):
        """
        Return the key of the pivot task

        :return: the key of the pivot task (str)
        """
        return self._pivot_task.name

    @property
    def pivot_task_time_gap(self):
        """
        Return the time gap between backward and forward start times of the pivot task

        :return: the time gap between backward and forward start times of the pivot task (int)
        """
        if self.has_solution_sequence:
            return round(pyo.value(self.var_T_backward) - pyo.value(self.var_T_forward))
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def pivot_task_start_time(self):
        """
        Return the start time of the pivot task

        :return: the start time of the pivot task (int)
        """
        if self.has_solution_sequence:
            return round(pyo.value(self.var_T_backward))
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def pivot_task_start_time_for_backward(self):
        """
        Return the start time of the pivot task which respects time constraints in backward direction

        :return: the backward start time of the pivot task (int)
        """
        if self.has_solution_sequence:
            return pyo.value(self.var_T_backward)
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def pivot_task_start_time_for_forward(self):
        """
        Return the start time of the pivot task which respects time constraints in forward direction

        :return: the forward start time of the pivot task (int)
        """
        if self.has_solution_sequence:
            return pyo.value(self.var_T_forward)
        else:
            raise AttributeError("There is no solution sequence stored")

    ##############################################
    # Getters and setters - Optimization results #
    ##############################################

    @property
    def support_instance_alterations(self):
        """
        Return the parameter alterations of the support instance

        :return: the parameter alterations of the support instance (InstanceChanges)
        """
        if self.has_solution_sequence:
            return self._support_instance_alterations
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def support_instance(self):
        """
        Return the support instance

        :return: the support instance (EditableInstance)
        """
        if self.has_solution_sequence:
            return self._support_instance
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def support_sequence(self):
        """
        Return the support sequence

        :return: the support sequence (SequenceForHeuristics)
        """
        return SequenceForHeuristics.from_Sequence(self.solution_sequence)

    @property
    def is_support_sequence_feasible(self):
        """
        Return whether the support sequence is feasible or not

        :return: a boolean indicating whether the support sequence is feasible or not (bool)
        """
        return self.pivot_task_time_gap == 0

    ############################
    # Decision variables - All #
    ############################

    def _add_decision_variables(self):
        """
        Add all the decision variables to the model

        :return: None
        """
        self._add_decision_variables_T()
        self._add_decision_variables_split_T()
        self._add_decision_variables_U()
        self._add_decision_variables_X()
        self._add_decision_variables_Delta()

    #############################
    # Decision variables - Time #
    #############################

    def _add_decision_variables_T(self):
        """
        Add the decision variables "T" to the model.
        These variables represent the start times of the tasks.

        :return: None
        """
        self._model.T = pyo.Var(
            self._get_candidate_tasks_keys(including_pivot_task=False), domain=pyo.NonNegativeIntegers
        )
        self.vars_T = self._model.T

    def _add_decision_variables_split_T(self):
        """
        Add the backward and forward start times decision variables to the model.
        These variables represent the start times of the pivot task.
        The backward start time is the start time of the pivot task
        which respects time constraints in backward direction.
        The forward start time is the start time of the pivot task
        which respects time constraints in forward direction.

        :return:
        """
        self._model.Tb = pyo.Var(domain=pyo.NonNegativeIntegers)
        self._model.Ta = pyo.Var(domain=pyo.NonNegativeIntegers)
        self.var_T_backward = self._model.Tb
        self.var_T_forward = self._model.Ta

    ################################
    # Decision variables - Spatial #
    ################################

    # Decision variables (U) are unchanged

    ##############################################
    # Decision variables - Alteration activation #
    ##############################################

    def _add_decision_variables_X_employee(self):
        """
        Add the decision variables "X" to the model for the employee alterations.
        These variables enable the activations of the instance parameter alterations related to employees.

        :return: None
        """
        bounds = self._instance_parameter_alteration_bounds
        employee = self.employee
        if bounds is None:
            self._model.X_LB_e = pyo.Var(domain=pyo.Binary)
            self.var_X_LB_e = self._model.X_LB_e
            self._model.X_UB_e = pyo.Var(domain=pyo.Binary)
            self.var_X_UB_e = self._model.X_UB_e
        else:
            self.var_X_LB_e = None
            self.var_X_UB_e = None
            if bounds.is_affecting_employee(employee):
                new_start_time_lb = bounds.get_employee_start_time_lb(employee)
                if new_start_time_lb is not None and new_start_time_lb < employee.start_time_lb:
                    self._model.X_LB_e = pyo.Var(domain=pyo.Binary)
                    self.var_X_LB_e = self._model.X_LB_e
                new_end_time_ub = bounds.get_employee_end_time_ub(employee)
                if new_end_time_ub is not None and new_end_time_ub > employee.end_time_ub:
                    self._model.X_UB_e = pyo.Var(domain=pyo.Binary)
                    self.var_X_UB_e = self._model.X_UB_e

    def _add_decision_variables_X_tasks(self):
        """
        Add the decision variables "X" to the model for the task alterations.
        These variables enable the activations of the instance parameter alterations related to tasks.

        :return: None
        """
        bounds = self._instance_parameter_alteration_bounds
        if bounds is None:
            self._model.X_LB_t = pyo.Var(self._get_candidate_tasks_keys(), domain=pyo.Binary)
            self.vars_X_LB_t = self._model.X_LB_t
            self._model.X_UB_t = pyo.Var(self._get_candidate_tasks_keys(), domain=pyo.Binary)
            self.vars_X_UB_t = self._model.X_UB_t
            self._model.X_dt_t = pyo.Var(self._get_candidate_tasks_keys(), domain=pyo.Binary)
            self.vars_X_dt_t = self._model.X_dt_t
        else:
            self.vars_X_LB_t = dict([(task_key, None) for task_key in self._get_candidate_tasks_keys()])
            self.vars_X_UB_t = dict([(task_key, None) for task_key in self._get_candidate_tasks_keys()])
            self.vars_X_dt_t = dict([(task_key, None) for task_key in self._get_candidate_tasks_keys()])
            for task in self.candidate_tasks():
                if bounds.is_affecting_task(task):
                    task_key = create_activity_key(task)
                    new_start_time_lb = bounds.get_task_start_time_lb(task)
                    if new_start_time_lb is not None and new_start_time_lb < task.start_time_lb:
                        self._model.add_component(f"X_LB_t[{task_key}]", pyo.Var(domain=pyo.Binary))
                        self.vars_X_LB_t[task_key] = self._model.component(f"X_LB_t[{task_key}]")
                    new_end_time_ub = bounds.get_task_end_time_ub(task)
                    if new_end_time_ub is not None and new_end_time_ub > task.end_time_ub:
                        self._model.add_component(f"X_UB_t[{task_key}]", pyo.Var(domain=pyo.Binary))
                        self.vars_X_UB_t[task_key] = self._model.component(f"X_UB_t[{task_key}]")
                    new_duration = bounds.get_task_duration(task)
                    if new_duration is not None and new_duration < task.duration:
                        self._model.add_component(f"X_dt_t[{task_key}]", pyo.Var(domain=pyo.Binary))
                        self.vars_X_dt_t[task_key] = self._model.component(f"X_dt_t[{task_key}]")

    def _add_decision_variables_X(self):
        """
        Add the decision variables "X" to the model.
        These variables enable the activation of the parameter alterations.

        :return: None
        """
        self._add_decision_variables_X_employee()
        self._add_decision_variables_X_tasks()

    #########################################
    # Decision variables - Alteration bound #
    #########################################

    def _add_decision_variables_Delta_employee(self):
        """
        Add the decision variables "Delta" to the model for the employee alterations.
        These variables represent the values of the instance parameter alterations related to employees.

        :return: None
        """
        bounds = self._instance_parameter_alteration_bounds
        employee = self.employee
        if bounds is None:
            self._model.D_LB_e = pyo.Var(domain=pyo.NonNegativeIntegers, bounds=(0, employee.start_time_lb))
            self.var_D_LB_e = self._model.D_LB_e
            self._model.D_UB_e = pyo.Var(domain=pyo.NonNegativeIntegers, bounds=(0, 24 * 60 - employee.end_time_ub))
            self.var_D_UB_e = self._model.D_UB_e
        else:
            self.var_D_LB_e = None
            self.var_D_UB_e = None
            if self.var_X_LB_e is not None:
                new_start_time_lb = bounds.get_employee_start_time_lb(employee)
                self._model.D_LB_e = pyo.Var(
                    domain=pyo.NonNegativeIntegers, bounds=(0, employee.start_time_lb - new_start_time_lb)
                )
                self.var_D_LB_e = self._model.D_LB_e
            if self.var_X_UB_e is not None:
                new_end_time_ub = bounds.get_employee_end_time_ub(employee)
                self._model.D_UB_e = pyo.Var(
                    domain=pyo.NonNegativeIntegers, bounds=(0, new_end_time_ub - employee.end_time_ub)
                )
                self.var_D_UB_e = self._model.D_UB_e

    def _add_decision_variables_Delta_tasks(self):
        """
        Add the decision variables "Delta" to the model for the task alterations.
        These variables represent the values of the instance parameter alterations related to tasks.

        :return: None
        """
        bounds = self._instance_parameter_alteration_bounds
        if bounds is None:
            self._model.D_LB_t = pyo.Var(
                self._get_candidate_tasks_keys(), domain=pyo.NonNegativeIntegers,
                bounds=lambda model, task_key: (0, self.get_candidate_task_by_key(task_key).start_time_lb)
            )
            self.vars_D_LB_t = self._model.D_LB_t
            self._model.D_UB_t = pyo.Var(
                self._get_candidate_tasks_keys(), domain=pyo.NonNegativeIntegers,
                bounds=lambda model, task_key: (0, 24 * 60 - self.get_candidate_task_by_key(task_key).end_time_ub)
            )
            self.vars_D_UB_t = self._model.D_UB_t
            self._model.D_dt_t = pyo.Var(
                self._get_candidate_tasks_keys(), domain=pyo.NonNegativeIntegers,
                bounds=lambda model, task_key: (0, self.get_candidate_task_by_key(task_key).duration)
            )
            self.vars_D_dt_t = self._model.D_dt_t
        else:
            self.vars_D_LB_t = dict([(task_key, None) for task_key in self._get_candidate_tasks_keys()])
            self.vars_D_UB_t = dict([(task_key, None) for task_key in self._get_candidate_tasks_keys()])
            self.vars_D_dt_t = dict([(task_key, None) for task_key in self._get_candidate_tasks_keys()])
            for task in self.candidate_tasks():
                task_key = create_activity_key(task)
                if self.vars_X_LB_t[task_key] is not None:
                    new_start_time_lb = bounds.get_task_start_time_lb(task)
                    self._model.add_component(
                        f"D_LB_t[{task_key}]",
                        pyo.Var(domain=pyo.NonNegativeIntegers, bounds=(0, task.start_time_lb - new_start_time_lb))
                    )
                    self.vars_D_LB_t[task_key] = self._model.component(f"D_LB_t[{task_key}]")
                if self.vars_X_UB_t[task_key] is not None:
                    new_end_time_ub = bounds.get_task_end_time_ub(task)
                    self._model.add_component(
                        f"D_UB_t[{task_key}]",
                        pyo.Var(domain=pyo.NonNegativeIntegers, bounds=(0, new_end_time_ub - task.end_time_ub))
                    )
                    self.vars_D_UB_t[task_key] = self._model.component(f"D_UB_t[{task_key}]")
                if self.vars_X_dt_t[task_key] is not None:
                    new_duration = bounds.get_task_duration(task)
                    self._model.add_component(
                        f"D_dt_t[{task_key}]",
                        pyo.Var(domain=pyo.NonNegativeIntegers, bounds=(0, task.duration - new_duration))
                    )
                    self.vars_D_dt_t[task_key] = self._model.component(f"D_dt_t[{task_key}]")

    def _add_decision_variable_Delta_max(self):
        """
        Add the decision variable "Delta_max" to the model.
        This variable represents the largest time value of instance parameter alterations.

        :return: None
        """
        self._model.Delta_max = pyo.Var(domain=pyo.NonNegativeIntegers, bounds=(0, 24 * 60))
        self.var_D_max = self._model.Delta_max

    def _add_decision_variables_Delta(self):
        """
        Add the decision variables "Delta" to the model.
        These variables represent the values of the instance parameter alterations.

        :return: None
        """
        self._add_decision_variables_Delta_employee()
        self._add_decision_variables_Delta_tasks()
        self._add_decision_variable_Delta_max()

    #######################################
    # Objective function - Key quantities #
    #######################################

    def _build_task_performances_expressions(self):
        """
        Build the expressions corresponding to whether each task is performed or not

        :return: None
        """
        self._task_performances_expressions = dict([
            (j, pyo.quicksum([self.vars_U[j, k]
                              for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                              if k != j]))
            for j in self._get_candidate_tasks_keys()
        ])

    def _build_total_working_time_expression(self):
        """
        Build the expression corresponding to the total working time of the employees

        :return: None
        """
        self._total_working_time_expression = \
            pyo.quicksum([self._task_performances_expressions[j] * self.get_candidate_task_by_key(j).duration
                          for j in self._get_candidate_tasks_keys()])

    def _build_total_traveling_time_expression(self):
        """
        Build the expression corresponding to the total traveling time of the employees

        :return: None
        """
        self._total_traveling_time_expression = \
            pyo.quicksum([self.vars_U[indices] *
                          self.get_traveling_duration(activity_key1=indices[0], activity_key2=indices[1])
                          for indices in self.vars_U.keys()])

    def _build_time_gap_expression(self):
        """
        Build the expression corresponding to the total time gap between
        forward and backward start times of the pivot task

        :return: None
        """
        self._time_gap_expression = self.var_T_backward - self.var_T_forward

    def _build_nb_alterations_expression(self):
        """
        Build the expression corresponding to the number of instance parameter alterations

        :return: None
        """
        self._nb_alterations_expression = \
            pyo.quicksum([(self.vars_X_LB_t[j] if self.vars_X_LB_t[j] is not None else 0) +
                          (self.vars_X_UB_t[j] if self.vars_X_UB_t[j] is not None else 0) +
                          (self.vars_X_dt_t[j] if self.vars_X_dt_t[j] is not None else 0)
                          for j in self._get_candidate_tasks_keys()]) + \
            (self.var_X_LB_e if self.var_X_LB_e is not None else 0) + \
            (self.var_X_UB_e if self.var_X_UB_e is not None else 0)

    def _build_total_task_duration_alterations_expression(self):
        """
        Build the expression corresponding to the total altered task duration

        :return: None
        """
        self._total_altered_task_duration_expression = \
            pyo.quicksum([(self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0)
                          for j in self._get_candidate_tasks_keys()])

    def _build_total_time_alteration_expression(self):
        """
        Build the expression corresponding to the total time alteration task duration

        :return: None
        """
        self._total_time_alterations_expression = \
            pyo.quicksum([(self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0)
                          for j in self._get_candidate_tasks_keys()]) + \
            pyo.quicksum([(self.vars_D_LB_t[j] if self.vars_X_LB_t[j] is not None else 0)
                          for j in self._get_candidate_tasks_keys()]) + \
            pyo.quicksum([(self.vars_D_UB_t[j] if self.vars_X_UB_t[j] is not None else 0)
                          for j in self._get_candidate_tasks_keys()]) + \
            (self.var_D_LB_e if self.var_X_LB_e is not None else 0) + \
            (self.var_D_UB_e if self.var_X_UB_e is not None else 0)

    def _build_key_expressions(self):
        """
        Build the key expressions that are used in the objective function

        :return: None
        """
        self._build_task_performances_expressions()
        self._build_total_working_time_expression()
        self._build_total_traveling_time_expression()
        self._build_time_gap_expression()
        self._build_nb_alterations_expression()
        self._build_total_task_duration_alterations_expression()
        self._build_total_time_alteration_expression()

    ###############################
    # Objective function - Itself #
    ###############################

    def _add_objective_function(self):
        """
        Build the objectives that will be minimized according to a lexicographic order, highest priority first:

        - the time gap between backward and forward start times of the replacing task
        - the opposite of the total working time
        - the total traveling time
        - the total sum of task duration alterations
        - the largest time alteration
        - the number of instance parameter alterations
        - the total time alteration

        Solved lexicographically (one solve per objective, see _solve) since Pyomo/HiGHS have no equivalent
        of Gurobi's setObjectiveN hierarchical multi-objective feature.

        :return: None
        """
        self._build_key_expressions()
        self._objectives_in_priority_order = [
            self._time_gap_expression,
            - self._total_working_time_expression, self._total_traveling_time_expression,
            self._total_altered_task_duration_expression, self.var_D_max, self._nb_alterations_expression,
            self._total_time_alterations_expression
        ]

    def _solve(self, mute: bool, solver_name: str):
        solver = Solver(solver_name, mute=mute, time_limit=self._solving_time_limit)
        return solver.solve_lexicographically(self._model, self._objectives_in_priority_order)

    #####################
    # Constraints - All #
    #####################

    def _add_constraints(self):
        """
        Add all constraints to the model including:

        - covering constraints
        - flow constraints
        - time window constraints
        - sequence times constraints
        - split time constraints
        - instance parameter alterations bounds constraints
        - (no skill constraints)

        :return: None
        """
        super()._add_constraints()
        self._add_time_gap_constraint()
        self._add_alterations_bounds_constraints()

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_covering_constraints(self):
        """
        Add the covering constraints to the model.
        All the candidate tasks (including the pivot task) must be performed.

        :return: None
        """
        for j in self._get_candidate_tasks_keys():
            self._model.add_component(
                f"TaskCoveringConstraint[{j}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([self.vars_U[(j, k)]
                                  for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                                  if k != j]) == 1
                ))
            )

    ######################
    # Constraints - Flow #
    ######################

    # Flow constraints are unchanged

    #############################
    # Constraints - Time window #
    #############################

    def _add_time_window_constraints(self):
        """
        Add the time window constraints to the model.
        The tasks must be performed within their availability time windows.
        Time windows may get wider with the instance parameter alterations.

        :return: None
        """
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._model.add_component(
                f"TimeWindowLBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] - self.get_candidate_task_by_key(j).start_time_lb +
                    (self.vars_D_LB_t[j] if self.vars_X_LB_t[j] is not None else 0) >= 0
                ))
            )
            self._model.add_component(
                f"TimeWindowUBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                    (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) -
                    self.get_candidate_task_by_key(j).end_time_ub -
                    (self.vars_D_UB_t[j] if self.vars_X_UB_t[j] is not None else 0) <= 0
                ))
            )
        j = self._pivot_task_key
        self._model.add_component(
            f"TimeWindowLBConstraint[{j}]",
            pyo.Constraint(expr=(
                self.var_T_backward - self.get_candidate_task_by_key(j).start_time_lb +
                (self.vars_D_LB_t[j] if self.vars_X_LB_t[j] is not None else 0) >= 0
            ))
        )
        self._model.add_component(
            f"TimeWindowUBConstraint[{j}]",
            pyo.Constraint(expr=(
                self.var_T_forward + self.get_candidate_task_by_key(j).duration -
                (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) -
                self.get_candidate_task_by_key(j).end_time_ub -
                (self.vars_D_UB_t[j] if self.vars_X_UB_t[j] is not None else 0) <= 0
            ))
        )

    ################################
    # Constraints - Sequence times #
    ################################

    def _add_sequence_times_constraints(self):
        """
        Add the sequence times constraints to the model.
        Employees must have enough time to travel between tasks.
        Task durations may be shorter with the instance parameter alterations.
        Employee time windows may get wider with the instance parameter alterations.

        :return: None
        """
        # Add departure-to-first-task time sequence constraints
        for k in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._model.add_component(
                f"SequenceDepartureToTaskConstraint[{k}]",
                pyo.Constraint(expr=(
                    self.vars_T[k] - self.get_traveling_duration(LEAVING_HOME_KEY, k) - self.employee.start_time_lb +
                    (self.var_D_LB_e if self.var_X_LB_e is not None else 0) >= 0
                ))
            )
        k = self._pivot_task_key
        self._model.add_component(
            f"SequenceDepartureToTaskConstraint[{k}]",
            pyo.Constraint(expr=(
                self.var_T_backward - self.get_traveling_duration(LEAVING_HOME_KEY, k) - self.employee.start_time_lb +
                (self.var_D_LB_e if self.var_X_LB_e is not None else 0) >= 0
            ))
        )
        # Add last-task-to-comeback time sequence constraints
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._model.add_component(
                f"SequenceTaskToComebackConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                    (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                    self.get_traveling_duration(j, COMING_BACK_HOME_KEY) - self.employee.end_time_ub -
                    (self.var_D_UB_e if self.var_X_UB_e is not None else 0) <= 0
                ))
            )
        j = self._pivot_task_key
        self._model.add_component(
            f"SequenceTaskToComebackConstraint[{j}]",
            pyo.Constraint(expr=(
                self.var_T_forward + self.get_candidate_task_by_key(j).duration -
                (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                self.get_traveling_duration(j, COMING_BACK_HOME_KEY) - self.employee.end_time_ub -
                (self.var_D_UB_e if self.var_X_UB_e is not None else 0) <= 0
            ))
        )
        # Add task-to-task time sequence constraints
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            for k in self._get_candidate_tasks_keys(including_pivot_task=False):
                if k != j:
                    self._model.add_component(
                        f"SequenceTaskToTaskConstraint[{j, k}]",
                        pyo.Constraint(expr=(
                            self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                            (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                            self.vars_U[(j, k)] * self.get_traveling_duration(j, k) - self.vars_T[k] -
                            (1 - self.vars_U[(j, k)]) * 24 * 60 <= 0
                        ))
                    )
        j = self._pivot_task_key
        for k in self._get_candidate_tasks_keys(including_pivot_task=False):
            if k != j:
                self._model.add_component(
                    f"SequenceTaskToTaskConstraint[{j, k}]",
                    pyo.Constraint(expr=(
                        self.var_T_forward + self.get_candidate_task_by_key(j).duration -
                        (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                        self.vars_U[(j, k)] * self.get_traveling_duration(j, k) - self.vars_T[k] -
                        (1 - self.vars_U[(j, k)]) * 24 * 60 <= 0
                    ))
                )
        k = self._pivot_task_key
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            if k != j:
                self._model.add_component(
                    f"SequenceTaskToTaskConstraint[{j, k}]",
                    pyo.Constraint(expr=(
                        self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                        (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                        self.vars_U[(j, k)] * self.get_traveling_duration(j, k) - self.var_T_backward -
                        (1 - self.vars_U[(j, k)]) * 24 * 60 <= 0
                    ))
                )

    ##########################
    # Constraints - Time gap #
    ##########################

    def _add_time_gap_constraint(self):
        """
        Add time gap constraint.
        The time gap is the difference between the backward and forward start time of the pivot task.
        This time gap must be non-negative.

        :return: None
        """
        self._model.add_component(
            "TimeGapConstraint", pyo.Constraint(expr=(self.var_T_backward - self.var_T_forward >= 0))
        )

    ####################################
    # Constraints - Alterations bounds #
    ####################################

    def _add_employee_related_alterations_bounds_constraints(self):
        """
        Add employee-related alterations bounds constraints.

        :return: None
        """
        if self.var_X_LB_e is not None:
            self._model.add_component(
                "DepartureLBAlterationUBConstraint",
                pyo.Constraint(expr=(self.var_D_LB_e - self.var_X_LB_e * self.employee.start_time_lb <= 0))
            )
            self._model.add_component(
                "EmployeeLBAlterationAndMaximumAlterationConstraint",
                pyo.Constraint(expr=(self.var_D_LB_e - self.var_D_max <= 0))
            )
        if self.var_X_UB_e is not None:
            self._model.add_component(
                "ComebackUBAlterationUBConstraint",
                pyo.Constraint(expr=(
                    self.var_D_UB_e - self.var_X_UB_e * (24 * 60 - self.employee.end_time_ub) <= 0
                ))
            )
            self._model.add_component(
                "EmployeeUBAlterationAndMaximumAlterationConstraint",
                pyo.Constraint(expr=(self.var_D_UB_e - self.var_D_max <= 0))
            )

    def _add_alterations_bounds_constraints_tasks(self):
        """
        Add task-related alterations bounds constraints.

        :return: None
        """
        for j in self._get_candidate_tasks_keys():
            if self.vars_X_LB_t[j] is not None:
                self._model.add_component(
                    f"TimeWindowLBAlterationUBConstraint[{j}]",
                    pyo.Constraint(expr=(
                        self.vars_D_LB_t[j] - self.vars_X_LB_t[j] * self.get_candidate_task_by_key(j).start_time_lb
                        <= 0
                    ))
                )
                self._model.add_component(
                    f"TimeWindowLBAlterationAndMaximumAlterationConstraint[{j}]",
                    pyo.Constraint(expr=(self.vars_D_LB_t[j] - self.var_D_max <= 0))
                )
            if self.vars_X_UB_t[j] is not None:
                self._model.add_component(
                    f"TimeWindowUBAlterationUBConstraint[{j}]",
                    pyo.Constraint(expr=(
                        self.vars_D_UB_t[j] - self.vars_X_UB_t[j] * (
                                    24 * 60 - self.get_candidate_task_by_key(j).end_time_ub) <= 0
                    ))
                )
                self._model.add_component(
                    f"TimeWindowUBAlterationAndMaximumAlterationConstraint[{j}]",
                    pyo.Constraint(expr=(self.vars_D_UB_t[j] - self.var_D_max <= 0))
                )
            if self.vars_X_dt_t[j] is not None:
                self._model.add_component(
                    f"TaskDurationAlterationUBConstraint[{j}]",
                    pyo.Constraint(expr=(
                        self.vars_D_dt_t[j] - self.vars_X_dt_t[j] * self.get_candidate_task_by_key(j).duration <= 0
                    ))
                )
                self._model.add_component(
                    f"TaskDurationAlterationAndMaximumAlterationConstraint[{j}]",
                    pyo.Constraint(expr=(self.vars_D_dt_t[j] - self.var_D_max <= 0))
                )

    def _add_max_nb_alterations_constraint(self, max_nb_alterations: int):
        """
        Add the constraint that the number of alterations must be less than or equal to the given value

        :param max_nb_alterations: rhe maximum number of alterations (int)
        :return: None
        """
        self._model.add_component(
            "MaximumNbAlterationsConstraint",
            pyo.Constraint(expr=(self._nb_alterations_expression <= max_nb_alterations))
        )

    def _add_alterations_bounds_constraints(self):
        """
        Add the constraints that the alterations must be within bounds

        :return: None
        """
        self._add_employee_related_alterations_bounds_constraints()
        self._add_alterations_bounds_constraints_tasks()
        self._add_max_nb_alterations_constraint(MAX_NB_ALTERATIONS)
        # TODO: temp
        self._model.add_component(
            "NoDepartureLBAlterationConstraint", pyo.Constraint(expr=(self.var_X_LB_e == 0))
        )
        self._model.add_component(
            "NoComebackUBAlterationConstraint", pyo.Constraint(expr=(self.var_X_UB_e == 0))
        )

    ######################################################
    # Data extraction from IP solving results - Instance #
    ######################################################

    def _extract_support_instance_alterations_from_IP_solving(self):
        """
        Extract the instance parameter alterations from the results obtained by solving the Integer Program.
        By applying these alterations to the instance, we obtain a new instance that we call support instance.

        :return: None
        """
        alterations = InstanceChanges()
        employee_start_time_lb_is_altered = (
            (self.var_X_LB_e is not None) and round(pyo.value(self.var_X_LB_e)) == 1
        )
        employee_start_time_UB_is_altered = (
            (self.var_X_UB_e is not None) and round(pyo.value(self.var_X_UB_e)) == 1
        )
        # Employee parameter alterations
        if employee_start_time_lb_is_altered or employee_start_time_UB_is_altered:
            alterations.add_employee_change(
                self.employee,
                (round(self.employee.start_time_lb - pyo.value(self.var_D_LB_e))
                 if employee_start_time_lb_is_altered else None),
                (round(self.employee.end_time_ub + pyo.value(self.var_D_UB_e))
                 if employee_start_time_UB_is_altered else None),
                None
            )
        # Task parameter alterations
        for task_key in self._get_candidate_tasks_keys():
            lb_altered = round(pyo.value(self.vars_X_LB_t[task_key])) == 1
            ub_altered = round(pyo.value(self.vars_X_UB_t[task_key])) == 1
            dt_altered = round(pyo.value(self.vars_X_dt_t[task_key])) == 1
            if lb_altered or ub_altered or dt_altered:
                task = self.get_candidate_task_by_key(task_key)
                alterations.add_task_change(
                    task,
                    round(task.duration - pyo.value(self.vars_D_dt_t[task_key])) if dt_altered else None,
                    round(task.start_time_lb - pyo.value(self.vars_D_LB_t[task_key])) if lb_altered else None,
                    round(task.end_time_ub + pyo.value(self.vars_D_UB_t[task_key])) if ub_altered else None,
                    None
                )
        self._support_instance_alterations = alterations

    def _extract_support_instance_from_IP_solving(self):
        """
        Extract the support instance from the results obtained by solving the Integer Program

        :return: None
        """
        self._support_instance = EditableInstance.from_Instance(self.instance, name=self.instance.name + "_support")
        self._support_instance.alter(self._support_instance_alterations)

    ######################################################
    # Data extraction from IP solving results - Sequence #
    ######################################################

    def _extract_ordered_steps(self):
        """
        Extract the sequence ordered steps from the results obtained by solving the Integer Program

        :return: list of steps (List[Step])
        """
        employee_start_time_lb = \
            self.employee.start_time_lb - (round(pyo.value(self.var_D_LB_e)) if self.var_X_LB_e is not None else 0)
        employee_end_time_ub = \
            self.employee.end_time_ub + (round(pyo.value(self.var_D_UB_e)) if self.var_X_UB_e is not None else 0)
        start_times_and_steps = [
            (employee_start_time_lb, Step(Departure(self.employee), start_time=employee_start_time_lb)),
            (employee_end_time_ub, Step(ComeBack(self.employee), start_time=employee_end_time_ub))
        ]
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            if round(np.sum(
                [pyo.value(self.vars_U[j, k])
                 for k in self.get_activities_keys(including_departure=False, including_comeback=True) if k != j]
            )) == 1:
                task = self.get_candidate_task_by_key(j)
                start_time = round(pyo.value(self.vars_T[j]))
                start_times_and_steps.append((start_time, Step(task, start_time=start_time)))
        j = self._pivot_task_key
        task = self.get_candidate_task_by_key(j)
        start_time = round(pyo.value(self.var_T_backward))
        start_times_and_steps.append((start_time, Step(task, start_time=start_time)))
        for j in self.get_unavailabilities_keys():
            unavailability = self.get_unavailability_by_key(j)
            start_times_and_steps.append(
                (unavailability.start_time_lb, Step(unavailability, start_time=unavailability.start_time_lb))
            )
        start_times_and_steps.sort()
        _, first_step = start_times_and_steps[0]
        if not isinstance(first_step.activity, Departure):
            raise Exception(f"The first activity of the sequence is not a departure but {first_step.activity}")
        _, last_step = start_times_and_steps[-1]
        if not isinstance(last_step.activity, ComeBack):
            for _, step in start_times_and_steps:
                j = create_activity_key(step.activity)
                if j in self.get_activities_keys(including_departure=True, including_comeback=False):
                    for k in self.get_activities_keys(including_departure=False, including_comeback=True):
                        if k != j:
                            if pyo.value(self.vars_U[j, k]) > 0:
                                print(f"{j} to {k}")
            raise Exception(f"The last activity of the sequence is not a comeback but {last_step.activity.name}. \n"
                            f"The pivot task is {self._pivot_task.name} with "
                            f"backward start time {pyo.value(self.var_T_backward)} and "
                            f"forward start time {pyo.value(self.var_T_forward)}. \n"
                            f"The list of start times and steps is {start_times_and_steps}.")
        return [step for _, step in start_times_and_steps]

    def _extract_sequence_from_IP_solving(self):
        """
        Extract the sequence from the results obtained by solving the Integer Program

        :return: None
        """
        steps = self._extract_ordered_steps()
        sequence = SequenceForHeuristics(self.instance, self.employee, steps)
        sequence = EditableSequence.from_Sequence(sequence, self._support_instance)
        sequence.compute_times_based_on_fixed_start_times()
        self._sequence_from_IP_solving = sequence

    #################################################
    # Data extraction from IP solving results - All #
    #################################################

    def _extract_data_from_IP_solving(self):
        """
        Extract all the data from the results obtained by solving the Integer Program

        :return: None
        """
        self._extract_support_instance_alterations_from_IP_solving()
        self._extract_support_instance_from_IP_solving()
        self._extract_sequence_from_IP_solving()

    #################################
    # Exploiting IP solving results #
    #################################

    def _is_task_performed_given_key(self, task_key: str):
        """
        Check if a task is performed given its key

        :param task_key: the key of the task (str)
        :return: True if the task is performed, False otherwise
        """
        return round(pyo.value(self._task_performances_expressions[task_key])) == 1

    def is_task_performed(self, task: Task):
        """
        Check if a task is performed

        :param task: the task (Task)
        :return: True if the task is performed, False otherwise
        """
        return round(pyo.value(self._task_performances_expressions[create_activity_key(task)])) == 1
