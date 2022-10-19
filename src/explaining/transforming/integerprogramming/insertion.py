# Third party libraries
import gurobipy as grb
from gurobipy import GRB

# Local libraries
from src.explaining.modeling.instance import EditableInstance
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.modeling.sequence import EditableSequence
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.sequence import Sequence
from src.modeling.step import Step
from src.modeling.task import Task
from src.optimization.IP.sequence.basemodel import IPModelForSequenceOptimization, LEAVING_HOME_KEY, COMING_BACK_HOME_KEY
from src.optimization.localsearch.sequence import SequenceLS


# Class IPModelForInsertionAlteringInput
class IPModelForInsertionAlteringInput(IPModelForSequenceOptimization):

    def __init__(self, sequence: Sequence, task_to_insert: Task, instance_slacks: InstanceChanges = None):
        candidate_tasks = sequence.get_contained_tasks() + [task_to_insert]
        self._task_to_insert = task_to_insert
        self._instance_slacks = instance_slacks
        super().__init__(sequence.instance, sequence.employee, candidate_tasks)

    @property
    def task_to_insert(self):
        return self._task_to_insert

    def get_candidate_tasks_keys(self, including_task_to_insert: bool = True):
        if including_task_to_insert:
            return [task.name for task in self.candidate_tasks]
        else:
            return [task.name for task in self.candidate_tasks if task != self._task_to_insert]

    def get_task_to_insert_key(self):
        return self._task_to_insert.name

    @property
    def task_to_insert_time_gap(self):
        if self.has_solution_sequence:
            return int(self.var_T_backward.x - self.var_T_forward.x)
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def task_to_insert_start_time(self):
        if self.has_solution_sequence:
            return int(self.var_T_backward.x)
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def task_to_insert_start_time_for_backward(self):
        if self.has_solution_sequence:
            return self.var_T_backward.x
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def task_to_insert_start_time_for_forward(self):
        if self.has_solution_sequence:
            return self.var_T_forward.x
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def support_instance_alterations(self):
        if self.has_solution_sequence:
            return self._support_instance_alterations
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def support_instance(self):
        if self.has_solution_sequence:
            return self._support_instance
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def support_sequence(self):
        return SequenceLS.from_Sequence(self.solution_sequence)

    ######################
    # Decision variables #
    ######################

    def _add_decision_variables_T(self):
        self.vars_T = self._GRB_model.addVars(
            self.get_candidate_tasks_keys(including_task_to_insert=False), vtype=GRB.INTEGER, lb=0, name="T"
        )

    def _add_decision_variables_split_T(self):
        self.var_T_backward = self._GRB_model.addVar(vtype=GRB.INTEGER, lb=0, name="Tb")
        self.var_T_forward = self._GRB_model.addVar(vtype=GRB.INTEGER, lb=0, name="Tf")

    # Decision variables U are unchanged

    # TODO depending on instance_slacks
    def _add_decision_variables_X_employee(self):
        self.var_X_LB_e = self._GRB_model.addVar(vtype=GRB.BINARY, name="X_LB_e")
        self.var_X_UB_e = self._GRB_model.addVar(vtype=GRB.BINARY, name="X_UB_e")

    # TODO depending on instance_slacks
    def _add_decision_variables_X_tasks(self):
        self.vars_X_LB_t = self._GRB_model.addVars(self.get_candidate_tasks_keys(), vtype=GRB.BINARY, name="X_LB_t")
        self.vars_X_UB_t = self._GRB_model.addVars(self.get_candidate_tasks_keys(), vtype=GRB.BINARY, name="X_UB_t")
        self.vars_X_dt_t = self._GRB_model.addVars(self.get_candidate_tasks_keys(), vtype=GRB.BINARY, name="X_dt")

    def _add_decision_variables_X(self):
        self._add_decision_variables_X_employee()
        self._add_decision_variables_X_tasks()

    # TODO depending on instance_slacks
    def _add_decision_variables_Delta_employee(self):
        self.var_D_LB_e = self._GRB_model.addVar(vtype=GRB.INTEGER, name="D_LB_e", lb=0, ub=self.employee.start_time_LB)
        self.var_D_UB_e = self._GRB_model.addVar(vtype=GRB.INTEGER, name="D_UB_e",
                                                 lb=0, ub=(24*60 - self.employee.end_time_UB))

    # TODO depending on instance_slacks
    def _add_decision_variables_Delta_tasks(self):
        self.vars_D_LB_t = self._GRB_model.addVars(self.get_candidate_tasks_keys(), vtype=GRB.INTEGER, name="D_LB_t",
                                                   lb=0, ub=[task.start_time_LB for task in self.candidate_tasks])
        self.vars_D_UB_t = self._GRB_model.addVars(self.get_candidate_tasks_keys(), vtype=GRB.INTEGER, name="D_UB_t",
                                                   lb=0, ub=[24*60 - task.end_time_UB for task in self.candidate_tasks])
        self.vars_D_dt_t = self._GRB_model.addVars(self.get_candidate_tasks_keys(), vtype=GRB.INTEGER, name="D_dt_t",
                                                   lb=0, ub=[task.duration for task in self.candidate_tasks])

    def _add_decision_variable_Delta_max(self):
        self.var_D_max = self._GRB_model.addVar(vtype=GRB.INTEGER, name="Delta_max", lb=0, ub=24*60)

    def _add_decision_variables_Delta(self):
        self._add_decision_variables_Delta_employee()
        self._add_decision_variables_Delta_tasks()
        self._add_decision_variable_Delta_max()

    def _add_decision_variables(self):
        self._add_decision_variables_T()
        self._add_decision_variables_split_T()
        self._add_decision_variables_U()
        self._add_decision_variables_X()
        self._add_decision_variables_Delta()

    ##################
    # Key quantities #
    ##################

    def _compute_traveling_duration_expression(self):
        self.traveling_duration_expression = \
            grb.quicksum(
                [self.vars_U[indices] *
                 self.get_traveling_duration(activity_key1=indices[0], activity_key2=indices[1])
                 for indices in self.vars_U.keys()]
            )

    def _compute_time_gap_expression(self):
        self.time_gap_expression = self.var_T_backward - self.var_T_forward

    def _compute_nb_alterations_expression(self):
        self.nb_alterations_expression = \
            grb.quicksum([self.vars_X_LB_t[j] + self.vars_X_UB_t[j] + self.vars_X_dt_t[j]
                          for j in self.get_candidate_tasks_keys()]) + \
            self.var_X_LB_e + self.var_X_UB_e

    def _compute_total_altered_task_duration(self):
        self.total_altered_task_duration = grb.quicksum([self.vars_D_dt_t[j] for j in self.get_candidate_tasks_keys()])

    def _compute_key_quantities(self):
        self._compute_time_gap_expression()
        self._compute_nb_alterations_expression()
        self._compute_total_altered_task_duration()
        self._compute_traveling_duration_expression()

    ######################
    # Objective function #
    ######################

    def _add_objective_function(self):
        self._compute_key_quantities()
        self._GRB_model.ModelSense = GRB.MINIMIZE
        # weighted_nb_alterations_expression = \
        #     grb.quicksum([self.vars_X_LB_t[j] + self.vars_X_UB_t[j] + 3*self.vars_X_dt_t[j]
        #                   for j in self.get_candidate_tasks_keys()]) + \
        #     self.var_X_LB_e + self.var_X_UB_e
        objectives = [self.time_gap_expression, self.total_altered_task_duration, self.var_D_max,
                      self.nb_alterations_expression, self.traveling_duration_expression]
        for index, objective in enumerate(objectives):
            self._GRB_model.setObjectiveN(objective, index, len(objectives)-1-index)
        self._GRB_model.update()

    ###############
    # Constraints #
    ###############

    def _add_constraints(self):
        self._add_covering_constraints()
        self._add_flow_constraints()
        self._add_time_window_constraints()
        self._add_sequence_times_constraints()
        self._add_split_time_constraint()
        self._add_alterations_bounds_constraints()
        # No skill constraints

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_covering_constraints(self):
        for j in self.get_candidate_tasks_keys():
            self._GRB_model.addLConstr(
                grb.quicksum(
                    [self.vars_U[(j, k)]
                     for k in self.get_activities_keys(including_departure=False, including_comeback=True) if k != j]
                ),
                sense=GRB.EQUAL, rhs=1,
                name=f"TaskCoveringConstraint[{j}]"
            )
        self._GRB_model.update()

    ######################
    # Constraints - Flow #
    ######################

    # Flow constraints are unchanged

    #############################
    # Constraints - Time window #
    #############################

    def _add_time_window_constraints(self):
        for j in self.get_candidate_tasks_keys(including_task_to_insert=False):
            self._GRB_model.addLConstr(
                self.vars_T[j] - self.get_candidate_task_by_key(j).start_time_LB + self.vars_D_LB_t[j],
                sense=GRB.GREATER_EQUAL, rhs=0,
                name=f"TimeWindowLBConstraint[{j}]"
            )
            self._GRB_model.addLConstr(
                self.vars_T[j] + self.get_candidate_task_by_key(j).duration - self.vars_D_dt_t[j]
                - self.get_candidate_task_by_key(j).end_time_UB - self.vars_D_UB_t[j],
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"TimeWindowUBConstraint[{j}]"
            )
        j = self.get_task_to_insert_key()
        self._GRB_model.addLConstr(
            self.var_T_backward - self.get_candidate_task_by_key(j).start_time_LB + self.vars_D_LB_t[j],
            sense=GRB.GREATER_EQUAL, rhs=0,
            name=f"TimeWindowLBConstraint[{j}]"
        )
        self._GRB_model.addLConstr(
            self.var_T_forward + self.get_candidate_task_by_key(j).duration - self.vars_D_dt_t[j]
            - self.get_candidate_task_by_key(j).end_time_UB - self.vars_D_UB_t[j],
            sense=GRB.LESS_EQUAL, rhs=0,
            name=f"TimeWindowUBConstraint[{j}]"
        )
        self._GRB_model.update()

    ################################
    # Constraints - Sequence times #
    ################################

    def _add_sequence_times_constraints(self):
        # Add departure-to-first-task time sequence constraints
        for k in self.get_candidate_tasks_keys(including_task_to_insert=False):
            self._GRB_model.addLConstr(
                self.vars_T[k]
                - self.employee.start_time_LB + self.var_D_LB_e - self.get_traveling_duration(LEAVING_HOME_KEY, k),
                sense=GRB.GREATER_EQUAL, rhs=0,
                name=f"SequenceDepartureToTaskConstraint[{k}]"
            )
        k = self.get_task_to_insert_key()
        self._GRB_model.addLConstr(
            self.var_T_backward - self.get_traveling_duration(LEAVING_HOME_KEY, k)
            - self.employee.start_time_LB + self.var_D_LB_e,
            sense=GRB.GREATER_EQUAL, rhs=0,
            name=f"SequenceDepartureToTaskConstraint[{k}]"
        )
        # Add last-task-to-comeback time sequence constraints
        for j in self.get_candidate_tasks_keys(including_task_to_insert=False):
            self._GRB_model.addLConstr(
                self.vars_T[j] + self.get_candidate_task_by_key(j).duration - self.vars_D_dt_t[j]
                + self.get_traveling_duration(j, COMING_BACK_HOME_KEY)
                - self.employee.end_time_UB - self.var_D_UB_e,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"SequenceTaskToComebackConstraint[{j}]"
            )
        j = self.get_task_to_insert_key()
        self._GRB_model.addLConstr(
            self.var_T_forward + self.get_candidate_task_by_key(j).duration - self.vars_D_dt_t[j]
            + self.get_traveling_duration(j, COMING_BACK_HOME_KEY)
            - self.employee.end_time_UB - self.var_D_UB_e,
            sense=GRB.LESS_EQUAL, rhs=0,
            name=f"SequenceTaskToComebackConstraint[{j}]"
        )
        # Add task-to-task time sequence constraints
        for j in self.get_candidate_tasks_keys(including_task_to_insert=False):
            for k in self.get_candidate_tasks_keys(including_task_to_insert=False):
                if k != j:
                    self._GRB_model.addLConstr(
                        self.vars_T[j] + self.get_candidate_task_by_key(j).duration - self.vars_D_dt_t[j]
                        + self.vars_U[(j, k)] * self.get_traveling_duration(j, k) - self.vars_T[k]
                        - (1 - self.vars_U[(j, k)]) * 24 * 60,
                        sense=GRB.LESS_EQUAL, rhs=0,
                        name=f"SequenceTaskToTaskConstraint[{j, k}]"
                    )
        j = self.get_task_to_insert_key()
        for k in self.get_candidate_tasks_keys(including_task_to_insert=False):
            if k != j:
                self._GRB_model.addLConstr(
                    self.var_T_forward + self.get_candidate_task_by_key(j).duration - self.vars_D_dt_t[j]
                    + self.vars_U[(j, k)] * self.get_traveling_duration(j, k) - self.vars_T[k]
                    - (1 - self.vars_U[(j, k)]) * 24 * 60,
                    sense=GRB.LESS_EQUAL, rhs=0,
                    name=f"SequenceTaskToTaskConstraint[{j, k}]"
                )
        k = self.get_task_to_insert_key()
        for j in self.get_candidate_tasks_keys(including_task_to_insert=False):
            if k != j:
                self._GRB_model.addLConstr(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration - self.vars_D_dt_t[j]
                    + self.vars_U[(j, k)] * self.get_traveling_duration(j, k) - self.var_T_backward
                    - (1 - self.vars_U[(j, k)]) * 24 * 60,
                    sense=GRB.LESS_EQUAL, rhs=0,
                    name=f"SequenceTaskToTaskConstraint[{j, k}]"
                )
        self._GRB_model.update()

    ############################
    # Constraints - Split time #
    ############################

    def _add_split_time_constraint(self):
        self._GRB_model.addLConstr(self.var_T_backward - self.var_T_forward,
                                   sense=GRB.GREATER_EQUAL, rhs=0,
                                   name=f"TaskTimeSplit[{self.get_task_to_insert_key()}]")
        self._GRB_model.update()

    ####################################
    # Constraints - Alterations bounds #
    ####################################

    def _add_alterations_bounds_constraints_employees(self):
        self._GRB_model.addLConstr(
            self.var_D_LB_e - self.var_X_LB_e * self.employee.start_time_LB,
            sense=GRB.LESS_EQUAL, rhs=0,
            name=f"DepartureLBAlterationUBConstraint"
        )
        self._GRB_model.addLConstr(
            self.var_D_LB_e - self.var_D_max,
            sense=GRB.LESS_EQUAL, rhs=0,
            name=f"EmployeeLBAlterationAndMaximumAlterationConstraint"
        )
        self._GRB_model.addLConstr(
            self.var_D_UB_e - self.var_X_UB_e * (24 * 60 - self.employee.end_time_UB),
            sense=GRB.LESS_EQUAL, rhs=0,
            name=f"ComebackUBAlterationUBConstraint"
        )
        self._GRB_model.addLConstr(
            self.var_D_UB_e - self.var_D_max,
            sense=GRB.LESS_EQUAL, rhs=0,
            name=f"EmployeeUBAlterationAndMaximumAlterationConstraint"
        )
        self._GRB_model.update()

    def _add_alterations_bounds_constraints_tasks(self):
        for j in self.get_candidate_tasks_keys():
            self._GRB_model.addLConstr(
                self.vars_D_LB_t[j] - self.vars_X_LB_t[j] * self.get_candidate_task_by_key(j).start_time_LB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"TimeWindowLBAlterationUBConstraint[{j}]"
            )
            self._GRB_model.addLConstr(
                self.vars_D_LB_t[j] - self.var_D_max,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"TimeWindowLBAlterationAndMaximumAlterationConstraint[{j}]"
            )
            self._GRB_model.addLConstr(
                self.vars_D_UB_t[j] - self.vars_X_UB_t[j] * (24*60 - self.get_candidate_task_by_key(j).end_time_UB),
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"TimeWindowUBAlterationUBConstraint[{j}]"
            )
            self._GRB_model.addLConstr(
                self.vars_D_UB_t[j] - self.var_D_max,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"TimeWindowUBAlterationAndMaximumAlterationConstraint[{j}]"
            )
            self._GRB_model.addLConstr(
                self.vars_D_dt_t[j] - self.vars_X_dt_t[j] * self.get_candidate_task_by_key(j).duration,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"TaskDurationAlterationUBConstraint[{j}]"
            )
            self._GRB_model.addLConstr(
                self.vars_D_dt_t[j] - self.var_D_max,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"TaskDurationAlterationAndMaximumAlterationConstraint[{j}]"
            )
        self._GRB_model.update()

    def _add_max_nb_alterations_constraint(self, max_nb_alteration: int):
        self._GRB_model.addLConstr(
            self.nb_alterations_expression,
            sense=GRB.LESS_EQUAL, rhs=max_nb_alteration,
            name=f"MaximumNbAlterationsConstraint"
        )
        self._GRB_model.update()

    def _add_alterations_bounds_constraints(self):
        self._add_alterations_bounds_constraints_employees()
        self._add_alterations_bounds_constraints_tasks()
        self._add_max_nb_alterations_constraint(6)

    ###################################
    # Data extraction from IP solving #
    ###################################

    def _extract_support_instance_alterations_from_IP_solving(self):
        alterations = InstanceChanges()
        if self.var_X_LB_e.x == 1 or self.var_X_UB_e.x == 1:
            alterations.add_employee_change(
                self.employee,
                int(self.employee.start_time_LB - self.var_D_LB_e.x) if self.var_X_LB_e.x == 1 else None,
                int(self.employee.end_time_UB + self.var_D_UB_e.x) if self.var_X_UB_e.x == 1 else None,
                None
            )
        for task_key in self.get_candidate_tasks_keys():
            if (self.vars_X_LB_t[task_key].x == 1 or self.vars_X_UB_t[task_key].x == 1 or
                    self.vars_X_dt_t[task_key].x == 1):
                task = self.get_candidate_task_by_key(task_key)
                alterations.add_task_change(
                    task,
                    int(task.duration - self.vars_D_dt_t[task_key].x) if self.vars_X_dt_t[task_key].x == 1 else None,
                    int(task.start_time_LB - self.vars_D_LB_t[task_key].x) if self.vars_X_LB_t[
                                                                                  task_key].x == 1 else None,
                    int(task.end_time_UB + self.vars_D_UB_t[task_key].x) if self.vars_X_UB_t[task_key].x == 1 else None,
                    None
                )
        self._support_instance_alterations = alterations

    def _extract_support_instance_from_IP_solving(self):
        self._support_instance = EditableInstance.from_Instance(self.instance, name=self.instance.name + "_support")
        self._support_instance.alter(self._support_instance_alterations)

    def _extract_ordered_steps(self):
        start_times_and_steps = [
            (
                self.employee.start_time_LB - int(self.var_D_LB_e.x),
                Step(activity=Departure(employee=self.employee),
                     start_time=self.employee.start_time_LB - int(self.var_D_LB_e.x))
            ), (
                self.employee.end_time_UB + int(self.var_D_UB_e.x),
                Step(activity=ComeBack(employee=self.employee),
                     start_time=self.employee.end_time_UB + int(self.var_D_UB_e.x))
            )
        ]
        for j in self.get_candidate_tasks_keys(including_task_to_insert=False):
            task = self.get_candidate_task_by_key(j)
            start_time = int(self.vars_T[j].x)
            start_times_and_steps.append((start_time, Step(activity=task, start_time=start_time)))
        j = self.get_task_to_insert_key()
        task = self.get_candidate_task_by_key(j)
        start_time = self.var_T_backward.x
        start_times_and_steps.append((start_time, Step(activity=task, start_time=start_time)))
        for j in self.get_unavailabilities_keys():
            unavailability = self.get_unavailability_by_key(j)
            start_times_and_steps.append(
                (unavailability.start_time_LB, Step(activity=unavailability, start_time=unavailability.start_time_LB))
            )
        start_times_and_steps.sort()
        _, first_step = start_times_and_steps[0]
        if not isinstance(first_step.activity, Departure):
            raise Exception(f"The first activity of the sequence is not a departure but {first_step.activity}")
        _, last_step = start_times_and_steps[-1]
        if not isinstance(last_step.activity, ComeBack):
            raise Exception(f"The first activity of the sequence is not a comeback but {last_step.activity}")
        return [step for _, step in start_times_and_steps]

    def _extract_sequence_from_IP_solving(self):
        steps = self._extract_ordered_steps()
        sequence = Sequence(self.instance, self.employee, steps)
        sequence = EditableSequence.from_Sequence(sequence, self._support_instance)
        sequence.compute_times_based_on_fixed_start_times()
        self._sequence_from_IP_solving = sequence

    def _extract_data_from_IP_solving(self):
        self._extract_support_instance_alterations_from_IP_solving()
        self._extract_support_instance_from_IP_solving()
        self._extract_sequence_from_IP_solving()
