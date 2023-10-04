# Third party libraries
import gurobipy as grb
from gurobipy import GRB
import numpy as np

# Local libraries
from src.explaining.modeling.instance import EditableInstance
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.modeling.sequence import EditableSequence
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.step import Step
from src.modeling.task import Task
from src.optimization.IP.sequence.basemodel import IPModelForSequenceOptimization, LEAVING_HOME_KEY, \
    COMING_BACK_HOME_KEY, create_activity_key
from src.optimization.heuristics.sequence import SequenceForHeuristics

# Global variables
MAX_NB_ALTERATIONS = 2


#########################################################
# Class IPModelForTransformationWithInstanceAlterations #
#########################################################

class IPModelForTransformationWithInstanceAlterations(IPModelForSequenceOptimization):
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
            return int(self.var_T_backward.x - self.var_T_forward.x)
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def pivot_task_start_time(self):
        """
        Return the start time of the pivot task

        :return: the start time of the pivot task (int)
        """
        if self.has_solution_sequence:
            return int(self.var_T_backward.x)
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def pivot_task_start_time_for_backward(self):
        """
        Return the start time of the pivot task which respects time constraints in backward direction

        :return: the backward start time of the pivot task (int)
        """
        if self.has_solution_sequence:
            return self.var_T_backward.x
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def pivot_task_start_time_for_forward(self):
        """
        Return the start time of the pivot task which respects time constraints in forward direction

        :return: the forward start time of the pivot task (int)
        """
        if self.has_solution_sequence:
            return self.var_T_forward.x
        else:
            raise AttributeError("There is no solution sequence stored")

    #################################################
    # Getters and setters - Optimization time limit #
    #################################################

    @property
    def solving_time_limit(self):
        """
        Return the solving time limit in seconds

        :return: the solving time limit in seconds (int)
        """
        return self._solving_time_limit

    @solving_time_limit.setter
    def solving_time_limit(self, limit: int):
        """
        Set the solving time limit in seconds

        :param limit: the solving time limit in seconds (int)
        :return: None
        """
        self._solving_time_limit = limit
        self._GRB_model.setParam('OutputFlag', 0)
        self._GRB_model.setParam('TimeLimit', limit)

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
        self._GRB_model.update()

    #############################
    # Decision variables - Time #
    #############################

    def _add_decision_variables_T(self):
        """
        Add the decision variables "T" to the model.
        These variables represent the start times of the tasks.

        :return: None
        """
        self.vars_T = self._GRB_model.addVars(
            self._get_candidate_tasks_keys(including_pivot_task=False), vtype=GRB.INTEGER, lb=0, name="T"
        )

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
        self.var_T_backward = self._GRB_model.addVar(vtype=GRB.INTEGER, lb=0, name="Tb")
        self.var_T_forward = self._GRB_model.addVar(vtype=GRB.INTEGER, lb=0, name="Ta")

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
            self.var_X_LB_e = self._GRB_model.addVar(vtype=GRB.BINARY, name="X_LB_e")
            self.var_X_UB_e = self._GRB_model.addVar(vtype=GRB.BINARY, name="X_UB_e")
        else:
            self.var_X_LB_e = None
            self.var_X_UB_e = None
            if bounds.is_affecting_employee(employee):
                new_start_time_LB = bounds.get_employee_start_time_LB(employee)
                if new_start_time_LB is not None and new_start_time_LB < employee.start_time_LB:
                    self.var_X_LB_e = self._GRB_model.addVar(vtype=GRB.BINARY, name="X_LB_e")
                new_end_time_UB = bounds.get_employee_end_time_UB(employee)
                if new_end_time_UB is not None and new_end_time_UB > employee.end_time_UB:
                    self.var_X_UB_e = self._GRB_model.addVar(vtype=GRB.BINARY, name="X_UB_e")

    def _add_decision_variables_X_tasks(self):
        """
        Add the decision variables "X" to the model for the task alterations.
        These variables enable the activations of the instance parameter alterations related to tasks.

        :return: None
        """
        bounds = self._instance_parameter_alteration_bounds
        if bounds is None:
            self.vars_X_LB_t = \
                self._GRB_model.addVars(self._get_candidate_tasks_keys(), vtype=GRB.BINARY, name="X_LB_t")
            self.vars_X_UB_t = \
                self._GRB_model.addVars(self._get_candidate_tasks_keys(), vtype=GRB.BINARY, name="X_UB_t")
            self.vars_X_dt_t = \
                self._GRB_model.addVars(self._get_candidate_tasks_keys(), vtype=GRB.BINARY, name="X_dt")
        else:
            self.vars_X_LB_t = dict([(task_key, None) for task_key in self._get_candidate_tasks_keys()])
            self.vars_X_UB_t = dict([(task_key, None) for task_key in self._get_candidate_tasks_keys()])
            self.vars_X_dt_t = dict([(task_key, None) for task_key in self._get_candidate_tasks_keys()])
            for task in self.candidate_tasks():
                if bounds.is_affecting_task(task):
                    task_key = create_activity_key(task)
                    new_start_time_LB = bounds.get_task_start_time_LB(task)
                    if new_start_time_LB is not None and new_start_time_LB < task.start_time_LB:
                        self.vars_X_LB_t[task_key] = \
                            self._GRB_model.addVar(vtype=GRB.BINARY, name=f"X_LB_t[{task_key}]")
                    new_end_time_UB = bounds.get_task_end_time_UB(task)
                    if new_end_time_UB is not None and new_end_time_UB > task.end_time_UB:
                        self.vars_X_UB_t[task_key] = \
                            self._GRB_model.addVar(vtype=GRB.BINARY, name=f"X_UB_t[{task_key}]")
                    new_duration = bounds.get_task_duration(task)
                    if new_duration is not None and new_duration < task.duration:
                        self.vars_X_dt_t[task_key] = \
                            self._GRB_model.addVar(vtype=GRB.BINARY, name=f"X_dt_t[{task_key}]")

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
            self.var_D_LB_e = self._GRB_model.addVar(vtype=GRB.INTEGER, name="D_LB_e",
                                                     lb=0, ub=employee.start_time_LB)
            self.var_D_UB_e = self._GRB_model.addVar(vtype=GRB.INTEGER, name="D_UB_e",
                                                     lb=0, ub=(24 * 60 - employee.end_time_UB))
        else:
            self.var_D_LB_e = None
            self.var_D_UB_e = None
            if self.var_X_LB_e is not None:
                new_start_time_LB = bounds.get_employee_start_time_LB(employee)
                self.var_D_LB_e = self._GRB_model.addVar(vtype=GRB.INTEGER, name="D_LB_e",
                                                         lb=0, ub=(employee.start_time_LB - new_start_time_LB))
            if self.var_X_UB_e is not None:
                new_end_time_UB = bounds.get_employee_end_time_UB(employee)
                self.var_D_UB_e = self._GRB_model.addVar(vtype=GRB.INTEGER, name="D_UB_e",
                                                         lb=0, ub=(new_end_time_UB - employee.end_time_UB))

    def _add_decision_variables_Delta_tasks(self):
        """
        Add the decision variables "Delta" to the model for the task alterations.
        These variables represent the values of the instance parameter alterations related to tasks.

        :return: None
        """
        bounds = self._instance_parameter_alteration_bounds
        if bounds is None:
            self.vars_D_LB_t = \
                self._GRB_model.addVars(self._get_candidate_tasks_keys(), vtype=GRB.INTEGER, name="D_LB_t",
                                        lb=0, ub=[task.start_time_LB for task in self.candidate_tasks])
            self.vars_D_UB_t = \
                self._GRB_model.addVars(self._get_candidate_tasks_keys(), vtype=GRB.INTEGER, name="D_UB_t",
                                        lb=0, ub=[24 * 60 - task.end_time_UB for task in self.candidate_tasks])
            self.vars_D_dt_t = \
                self._GRB_model.addVars(self._get_candidate_tasks_keys(), vtype=GRB.INTEGER, name="D_dt_t",
                                        lb=0, ub=[task.duration for task in self.candidate_tasks])
        else:
            self.vars_D_LB_t = dict([(task_key, None) for task_key in self._get_candidate_tasks_keys()])
            self.vars_D_UB_t = dict([(task_key, None) for task_key in self._get_candidate_tasks_keys()])
            self.vars_D_dt_t = dict([(task_key, None) for task_key in self._get_candidate_tasks_keys()])
            for task in self.candidate_tasks():
                task_key = create_activity_key(task)
                if self.vars_X_LB_t[task_key] is not None:
                    new_start_time_LB = bounds.get_task_start_time_LB(task)
                    self.vars_D_LB_t[task_key] = \
                        self._GRB_model.addVar(vtype=GRB.INTEGER, name=f"D_LB_t[{task_key}]",
                                               lb=0, ub=(task.start_time_LB - new_start_time_LB))
                if self.vars_X_UB_t[task_key] is not None:
                    new_end_time_UB = bounds.get_task_end_time_UB(task)
                    self.vars_D_UB_t[task_key] = \
                        self._GRB_model.addVar(vtype=GRB.INTEGER, name=f"D_UB_t[{task_key}]",
                                               lb=0, ub=(new_end_time_UB - task.end_time_UB))
                if self.vars_X_dt_t[task_key] is not None:
                    new_duration = bounds.get_task_duration(task)
                    self.vars_D_dt_t[task_key] = \
                        self._GRB_model.addVar(vtype=GRB.INTEGER, name=f"D_dt_t[{task_key}]",
                                               lb=0, ub=(task.duration - new_duration))

    def _add_decision_variable_Delta_max(self):
        """
        Add the decision variable "Delta_max" to the model.
        This variable represents the largest time value of instance parameter alterations.

        :return: None
        """
        self.var_D_max = self._GRB_model.addVar(vtype=GRB.INTEGER, name="Delta_max", lb=0, ub=24 * 60)

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
            (j, grb.quicksum([self.vars_U[j, k]
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
            grb.quicksum([self._task_performances_expressions[j] * self.get_candidate_task_by_key(j).duration
                          for j in self._get_candidate_tasks_keys()])

    def _build_total_traveling_time_expression(self):
        """
        Build the expression corresponding to the total traveling time of the employees

        :return: None
        """
        self._total_traveling_time_expression = \
            grb.quicksum([self.vars_U[indices] *
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
            grb.quicksum([(self.vars_X_LB_t[j] if self.vars_X_LB_t[j] is not None else 0) +
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
            grb.quicksum([(self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0)
                          for j in self._get_candidate_tasks_keys()])

    def _build_total_time_alteration_expression(self):
        """
        Build the expression corresponding to the total time alteration task duration

        :return: None
        """
        self._total_time_alterations_expression = \
            grb.quicksum([(self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0)
                          for j in self._get_candidate_tasks_keys()]) + \
            grb.quicksum([(self.vars_D_LB_t[j] if self.vars_X_LB_t[j] is not None else 0)
                          for j in self._get_candidate_tasks_keys()]) + \
            grb.quicksum([(self.vars_D_UB_t[j] if self.vars_X_UB_t[j] is not None else 0)
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
        Add the objective function to the model, which minimizes according to a lexicographic order:

        - the time gap between backward and forward start times of the replacing task
        - the total sum of task duration alterations
        - the largest time alteration
        - the number of instance parameter alterations
        - the opposite of the total working time
        - the total traveling time

        :return: None
        """
        self._build_key_expressions()
        self._GRB_model.ModelSense = GRB.MINIMIZE
        # objectives = [self._time_gap_expression,
        #               self._total_altered_task_duration_expression, self.var_D_max, self._nb_alterations_expression,
        #               - self._total_working_time_expression, self._total_traveling_time_expression]
        objectives = [self._time_gap_expression,
                      - self._total_working_time_expression, self._total_traveling_time_expression,
                      self._total_altered_task_duration_expression, self.var_D_max, self._nb_alterations_expression,
                      self._total_time_alterations_expression]
        for index, objective in enumerate(objectives):
            self._GRB_model.setObjectiveN(objective, index, len(objectives)-1-index)
        self._GRB_model.update()

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
        self._GRB_model.update()

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
            self._GRB_model.addLConstr(
                grb.quicksum([self.vars_U[(j, k)]
                              for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                              if k != j]),
                sense=GRB.EQUAL, rhs=1, name=f"TaskCoveringConstraint[{j}]"
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
            self._GRB_model.addLConstr(
                self.vars_T[j] - self.get_candidate_task_by_key(j).start_time_LB +
                (self.vars_D_LB_t[j] if self.vars_X_LB_t[j] is not None else 0),
                sense=GRB.GREATER_EQUAL, rhs=0, name=f"TimeWindowLBConstraint[{j}]"
            )
            self._GRB_model.addLConstr(
                self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) -
                self.get_candidate_task_by_key(j).end_time_UB -
                (self.vars_D_UB_t[j] if self.vars_X_UB_t[j] is not None else 0),
                sense=GRB.LESS_EQUAL, rhs=0, name=f"TimeWindowUBConstraint[{j}]"
            )
        j = self._pivot_task_key
        self._GRB_model.addLConstr(
            self.var_T_backward - self.get_candidate_task_by_key(j).start_time_LB +
            (self.vars_D_LB_t[j] if self.vars_X_LB_t[j] is not None else 0),
            sense=GRB.GREATER_EQUAL, rhs=0, name=f"TimeWindowLBConstraint[{j}]"
        )
        self._GRB_model.addLConstr(
            self.var_T_forward + self.get_candidate_task_by_key(j).duration -
            (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) -
            self.get_candidate_task_by_key(j).end_time_UB -
            (self.vars_D_UB_t[j] if self.vars_X_UB_t[j] is not None else 0),
            sense=GRB.LESS_EQUAL, rhs=0, name=f"TimeWindowUBConstraint[{j}]"
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
            self._GRB_model.addLConstr(
                self.vars_T[k] - self.get_traveling_duration(LEAVING_HOME_KEY, k) - self.employee.start_time_LB +
                (self.var_D_LB_e if self.var_X_LB_e is not None else 0),
                sense=GRB.GREATER_EQUAL, rhs=0, name=f"SequenceDepartureToTaskConstraint[{k}]"
            )
        k = self._pivot_task_key
        self._GRB_model.addLConstr(
            self.var_T_backward - self.get_traveling_duration(LEAVING_HOME_KEY, k) - self.employee.start_time_LB +
            (self.var_D_LB_e if self.var_X_LB_e is not None else 0),
            sense=GRB.GREATER_EQUAL, rhs=0, name=f"SequenceDepartureToTaskConstraint[{k}]"
        )
        # Add last-task-to-comeback time sequence constraints
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._GRB_model.addLConstr(
                self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                self.get_traveling_duration(j, COMING_BACK_HOME_KEY) - self.employee.end_time_UB -
                (self.var_D_UB_e if self.var_X_UB_e is not None else 0),
                sense=GRB.LESS_EQUAL, rhs=0, name=f"SequenceTaskToComebackConstraint[{j}]"
            )
        j = self._pivot_task_key
        self._GRB_model.addLConstr(
            self.var_T_forward + self.get_candidate_task_by_key(j).duration -
            (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
            self.get_traveling_duration(j, COMING_BACK_HOME_KEY) - self.employee.end_time_UB -
            (self.var_D_UB_e if self.var_X_UB_e is not None else 0),
            sense=GRB.LESS_EQUAL, rhs=0, name=f"SequenceTaskToComebackConstraint[{j}]"
        )
        # Add task-to-task time sequence constraints
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            for k in self._get_candidate_tasks_keys(including_pivot_task=False):
                if k != j:
                    self._GRB_model.addLConstr(
                        self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                        (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                        self.vars_U[(j, k)] * self.get_traveling_duration(j, k) - self.vars_T[k] -
                        (1 - self.vars_U[(j, k)]) * 24 * 60,
                        sense=GRB.LESS_EQUAL, rhs=0, name=f"SequenceTaskToTaskConstraint[{j, k}]"
                    )
        j = self._pivot_task_key
        for k in self._get_candidate_tasks_keys(including_pivot_task=False):
            if k != j:
                self._GRB_model.addLConstr(
                    self.var_T_forward + self.get_candidate_task_by_key(j).duration -
                    (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                    self.vars_U[(j, k)] * self.get_traveling_duration(j, k) - self.vars_T[k] -
                    (1 - self.vars_U[(j, k)]) * 24 * 60,
                    sense=GRB.LESS_EQUAL, rhs=0, name=f"SequenceTaskToTaskConstraint[{j, k}]"
                )
        k = self._pivot_task_key
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            if k != j:
                self._GRB_model.addLConstr(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                    (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                    self.vars_U[(j, k)] * self.get_traveling_duration(j, k) - self.var_T_backward -
                    (1 - self.vars_U[(j, k)]) * 24 * 60,
                    sense=GRB.LESS_EQUAL, rhs=0, name=f"SequenceTaskToTaskConstraint[{j, k}]"
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
        self._GRB_model.addLConstr(self.var_T_backward - self.var_T_forward,
                                   sense=GRB.GREATER_EQUAL, rhs=0, name=f"TimeGapConstraint")

    ####################################
    # Constraints - Alterations bounds #
    ####################################

    def _add_employee_related_alterations_bounds_constraints(self):
        """
        Add employee-related alterations bounds constraints.

        :return: None
        """
        if self.var_X_LB_e is not None:
            self._GRB_model.addLConstr(
                self.var_D_LB_e - self.var_X_LB_e * self.employee.start_time_LB,
                sense=GRB.LESS_EQUAL, rhs=0, name=f"DepartureLBAlterationUBConstraint"
            )
            self._GRB_model.addLConstr(
                self.var_D_LB_e - self.var_D_max,
                sense=GRB.LESS_EQUAL, rhs=0, name=f"EmployeeLBAlterationAndMaximumAlterationConstraint"
            )
        if self.var_X_UB_e is not None:
            self._GRB_model.addLConstr(
                self.var_D_UB_e - self.var_X_UB_e * (24 * 60 - self.employee.end_time_UB),
                sense=GRB.LESS_EQUAL, rhs=0, name=f"ComebackUBAlterationUBConstraint"
            )
            self._GRB_model.addLConstr(
                self.var_D_UB_e - self.var_D_max,
                sense=GRB.LESS_EQUAL, rhs=0, name=f"EmployeeUBAlterationAndMaximumAlterationConstraint"
            )

    def _add_alterations_bounds_constraints_tasks(self):
        """
        Add task-related alterations bounds constraints.

        :return: None
        """
        for j in self._get_candidate_tasks_keys():
            if self.vars_X_LB_t[j] is not None:
                self._GRB_model.addLConstr(
                    self.vars_D_LB_t[j] - self.vars_X_LB_t[j] * self.get_candidate_task_by_key(j).start_time_LB,
                    sense=GRB.LESS_EQUAL, rhs=0, name=f"TimeWindowLBAlterationUBConstraint[{j}]"
                )
                self._GRB_model.addLConstr(
                    self.vars_D_LB_t[j] - self.var_D_max,
                    sense=GRB.LESS_EQUAL, rhs=0, name=f"TimeWindowLBAlterationAndMaximumAlterationConstraint[{j}]"
                )
            if self.vars_X_UB_t[j] is not None:
                self._GRB_model.addLConstr(
                    self.vars_D_UB_t[j] - self.vars_X_UB_t[j] * (
                                24 * 60 - self.get_candidate_task_by_key(j).end_time_UB),
                    sense=GRB.LESS_EQUAL, rhs=0, name=f"TimeWindowUBAlterationUBConstraint[{j}]"
                )
                self._GRB_model.addLConstr(
                    self.vars_D_UB_t[j] - self.var_D_max,
                    sense=GRB.LESS_EQUAL, rhs=0, name=f"TimeWindowUBAlterationAndMaximumAlterationConstraint[{j}]"
                )
            if self.vars_X_dt_t[j] is not None:
                self._GRB_model.addLConstr(
                    self.vars_D_dt_t[j] - self.vars_X_dt_t[j] * self.get_candidate_task_by_key(j).duration,
                    sense=GRB.LESS_EQUAL, rhs=0, name=f"TaskDurationAlterationUBConstraint[{j}]"
                )
                self._GRB_model.addLConstr(
                    self.vars_D_dt_t[j] - self.var_D_max,
                    sense=GRB.LESS_EQUAL, rhs=0, name=f"TaskDurationAlterationAndMaximumAlterationConstraint[{j}]"
                )

    def _add_max_nb_alterations_constraint(self, max_nb_alterations: int):
        """
        Add the constraint that the number of alterations must be less than or equal to the given value

        :param max_nb_alterations: rhe maximum number of alterations (int)
        :return: None
        """
        self._GRB_model.addLConstr(
            self._nb_alterations_expression, sense=GRB.LESS_EQUAL, rhs=max_nb_alterations,
            name=f"MaximumNbAlterationsConstraint"
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
        self._GRB_model.addLConstr(
            self.var_X_LB_e,
            sense=GRB.EQUAL, rhs=0, name=f"NoDepartureLBAlterationConstraint"
        )
        self._GRB_model.addLConstr(
            self.var_X_UB_e,
            sense=GRB.EQUAL, rhs=0, name=f"NoComebackUBAlterationConstraint"
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
        employee_start_time_LB_is_altered = (self.var_X_LB_e is not None) and self.var_X_LB_e.x == 1
        employee_start_time_UB_is_altered = (self.var_X_UB_e is not None) and self.var_X_UB_e.x == 1
        # Employee parameter alterations
        if employee_start_time_LB_is_altered or employee_start_time_UB_is_altered:
            alterations.add_employee_change(
                self.employee,
                int(self.employee.start_time_LB - self.var_D_LB_e.x) if employee_start_time_LB_is_altered else None,
                int(self.employee.end_time_UB + self.var_D_UB_e.x) if employee_start_time_UB_is_altered else None,
                None
            )
        # Task parameter alterations
        for task_key in self._get_candidate_tasks_keys():
            if (self.vars_X_LB_t[task_key].x == 1 or self.vars_X_UB_t[task_key].x == 1 or
                    self.vars_X_dt_t[task_key].x == 1):
                task = self.get_candidate_task_by_key(task_key)
                alterations.add_task_change(
                    task,
                    int(task.duration - self.vars_D_dt_t[task_key].x) if self.vars_X_dt_t[task_key].x == 1 else None,
                    (int(task.start_time_LB - self.vars_D_LB_t[task_key].x)
                     if self.vars_X_LB_t[task_key].x == 1 else None),
                    int(task.end_time_UB + self.vars_D_UB_t[task_key].x) if self.vars_X_UB_t[task_key].x == 1 else None,
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
        employee_start_time_LB = \
            self.employee.start_time_LB - (int(self.var_D_LB_e.x) if self.var_X_LB_e is not None else 0)
        employee_end_time_UB = \
            self.employee.end_time_UB + (int(self.var_D_UB_e.x) if self.var_X_UB_e is not None else 0)
        start_times_and_steps = [
            (employee_start_time_LB, Step(Departure(self.employee), start_time=employee_start_time_LB)),
            (employee_end_time_UB, Step(ComeBack(self.employee), start_time=employee_end_time_UB))
        ]
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            if int(np.sum(
                [self.vars_U[j, k].x
                 for k in self.get_activities_keys(including_departure=False, including_comeback=True) if k != j]
            )) == 1:
                task = self.get_candidate_task_by_key(j)
                start_time = int(self.vars_T[j].x)
                start_times_and_steps.append((start_time, Step(task, start_time=start_time)))
        j = self._pivot_task_key
        task = self.get_candidate_task_by_key(j)
        start_time = self.var_T_backward.x
        start_times_and_steps.append((start_time, Step(task, start_time=start_time)))
        for j in self.get_unavailabilities_keys():
            unavailability = self.get_unavailability_by_key(j)
            start_times_and_steps.append(
                (unavailability.start_time_LB, Step(unavailability, start_time=unavailability.start_time_LB))
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
                            if self.vars_U[j, k].x > 0:
                                print(f"{j} to {k}")
            raise Exception(f"The last activity of the sequence is not a comeback but {last_step.activity.name}. \n"
                            f"The pivot task is {self._pivot_task.name} with "
                            f"backward start time {self.var_T_backward.x} and "
                            f"forward start time {self.var_T_forward.x}. \n"
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
        return self._task_performances_expressions[task_key].getValue()

    def is_task_performed(self, task: Task):
        """
        Check if a task is performed

        :param task: the task (Task)
        :return: True if the task is performed, False otherwise
        """
        return self._task_performances_expressions[create_activity_key(task)].getValue()
