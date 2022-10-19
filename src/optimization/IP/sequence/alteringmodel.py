# Third-party libraries
import numpy as np
import gurobipy as grb
from gurobipy import GRB

# Local libraries
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.sequence import Sequence
from src.modeling.step import Step
from src.modeling.task import Task
from src.optimization.alteration.alterations import Alterations
from src.optimization.IP.sequence.basemodel import (
    LEAVING_HOME_KEY, COMING_BACK_HOME_KEY, IPModelForSequenceOptimization
)


# Global variables
TASK_TW_BOUNDS_ALTERATION_UB = 30
UNAVAILABILITY_TW_BOUNDS_ALTERATION_UB = 30
EMPLOYEE_TW_BOUNDS_ALTERATION_UB = 30
DURATION_PART_ALTERATION_UB = 0.1


# Class IPModelForAlteringSequence
class IPModelForAlteringSequence(IPModelForSequenceOptimization):

    def __init__(self, sequence: Sequence, additional_task: Task):
        candidate_tasks = sequence.get_contained_tasks() + [additional_task]
        super().__init__(sequence.instance, sequence.employee, candidate_tasks)
        self._alterations = Alterations()
        self._altered_instance = sequence.instance

    def get_candidate_task_by_key(self, task_key: str, altered: bool = False):
        if not altered:
            return self._candidate_tasks[task_key]
        else:
            return self._altered_instance.get_task_by_name(task_key)

    def get_unavailability_by_key(self, unavailability_key: str, altered: bool = False):
        if not altered:
            return self._employee.get_unavailability_by_name(unavailability_key)
        else:
            altered_employee = self._altered_instance.get_employee_by_name(self.employee.name)
            return altered_employee.get_unavailability_by_name(unavailability_key)

    @property
    def alterations(self):
        return self._alterations

    @property
    def vars_X_at(self) -> grb.MVar:
        return self._decision_variables['X_at']

    @vars_X_at.setter
    def vars_X_at(self, X_at: grb.MVar):
        self._decision_variables['X_at'] = X_at

    @property
    def vars_Delta_at(self) -> grb.MVar:
        return self._decision_variables['Delta_at']

    @vars_Delta_at.setter
    def vars_Delta_at(self, Delta_at: grb.MVar):
        self._decision_variables['Delta_at'] = Delta_at

    @property
    def vars_X_bt(self) -> grb.MVar:
        return self._decision_variables['X_bt']

    @vars_X_bt.setter
    def vars_X_bt(self, X_bt: grb.MVar):
        self._decision_variables['X_bt'] = X_bt

    @property
    def vars_Delta_bt(self) -> grb.MVar:
        return self._decision_variables['Delta_bt']

    @vars_Delta_bt.setter
    def vars_Delta_bt(self, Delta_bt: grb.MVar):
        self._decision_variables['Delta_bt'] = Delta_bt

    @property
    def vars_X_au(self) -> grb.MVar:
        return self._decision_variables['X_au']

    @vars_X_au.setter
    def vars_X_au(self, X_au: grb.MVar):
        self._decision_variables['X_au'] = X_au

    @property
    def vars_Delta_au(self) -> grb.MVar:
        return self._decision_variables['Delta_au']

    @vars_Delta_au.setter
    def vars_Delta_au(self, Delta_au: grb.MVar):
        self._decision_variables['Delta_au'] = Delta_au

    @property
    def vars_X_bu(self) -> grb.MVar:
        return self._decision_variables['X_bu']

    @vars_X_bu.setter
    def vars_X_bu(self, X_bu: grb.MVar):
        self._decision_variables['X_bu'] = X_bu

    @property
    def vars_Delta_bu(self) -> grb.MVar:
        return self._decision_variables['Delta_bu']

    @vars_Delta_bu.setter
    def vars_Delta_bu(self, Delta_bu: grb.MVar):
        self._decision_variables['Delta_bu'] = Delta_bu

    @property
    def var_X_ae(self) -> grb.Var:
        return self._decision_variables['X_ae']

    @var_X_ae.setter
    def var_X_ae(self, X_ae: grb.Var):
        self._decision_variables['X_ae'] = X_ae

    @property
    def var_Delta_ae(self) -> grb.Var:
        return self._decision_variables['Delta_ae']

    @var_Delta_ae.setter
    def var_Delta_ae(self, Delta_ae: grb.Var):
        self._decision_variables['Delta_ae'] = Delta_ae

    @property
    def var_X_be(self) -> grb.Var:
        return self._decision_variables['X_be']

    @var_X_be.setter
    def var_X_be(self, X_be: grb.Var):
        self._decision_variables['X_be'] = X_be

    @property
    def var_Delta_be(self) -> grb.Var:
        return self._decision_variables['Delta_be']

    @var_Delta_be.setter
    def var_Delta_be(self, Delta_be: grb.Var):
        self._decision_variables['Delta_be'] = Delta_be

    @property
    def vars_X_dt(self) -> grb.MVar:
        return self._decision_variables['X_dt']

    @vars_X_dt.setter
    def vars_X_dt(self, X_dt: grb.MVar):
        self._decision_variables['X_dt'] = X_dt

    @property
    def vars_Delta_dt(self) -> grb.MVar:
        return self._decision_variables['Delta_dt']

    @vars_Delta_dt.setter
    def vars_Delta_dt(self, Delta_dt: grb.MVar):
        self._decision_variables['Delta_dt'] = Delta_dt

    ######################
    # Decision variables #
    ######################

    def _add_decision_variables_X(self):
        self.vars_X_at = self._GRB_model.addVars(
            self.get_candidate_tasks_keys(),
            vtype=GRB.BINARY, name="X_at"
        )
        self.vars_X_bt = self._GRB_model.addVars(
            self.get_candidate_tasks_keys(),
            vtype=GRB.BINARY, name="X_bt"
        )
        self.vars_X_au = self._GRB_model.addVars(
            self.get_unavailabilities_keys(),
            vtype=GRB.BINARY, name="X_au"
        )
        self.vars_X_bu = self._GRB_model.addVars(
            self.get_unavailabilities_keys(),
            vtype=GRB.BINARY, name="X_bu"
        )
        self.var_X_ae = self._GRB_model.addVar(
            vtype=GRB.BINARY, name="X_ae"
        )
        self.var_X_be = self._GRB_model.addVar(
            vtype=GRB.BINARY, name="X_be"
        )
        self.vars_X_dt = self._GRB_model.addVars(
            self.get_candidate_tasks_keys(),
            vtype=GRB.BINARY, name="X_dt"
        )

    def _add_decision_variables_Delta(self):
        self.vars_Delta_at = self._GRB_model.addVars(
            self.get_candidate_tasks_keys(),
            vtype=GRB.INTEGER, lb=0, name="Delta_at"
        )
        self.vars_Delta_bt = self._GRB_model.addVars(
            self.get_candidate_tasks_keys(),
            vtype=GRB.INTEGER, lb=0, name="Delta_bt"
        )
        self.vars_Delta_au = self._GRB_model.addVars(
            self.get_unavailabilities_keys(),
            vtype=GRB.INTEGER, lb=0, name="Delta_au"
        )
        self.vars_Delta_bu = self._GRB_model.addVars(
            self.get_unavailabilities_keys(),
            vtype=GRB.INTEGER, lb=0, name="Delta_bu"
        )
        self.var_Delta_ae = self._GRB_model.addVar(
            vtype=GRB.INTEGER, lb=0, name="Delta_ae"
        )
        self.var_Delta_be = self._GRB_model.addVar(
            vtype=GRB.INTEGER, lb=0, name="Delta_be"
        )
        self.vars_Delta_dt = self._GRB_model.addVars(
            self.get_candidate_tasks_keys(),
            vtype=GRB.INTEGER, lb=0, name="Delta_dt"
        )

    def _add_decision_variables(self):
        self._add_decision_variables_T()
        self._add_decision_variables_U()
        self._add_decision_variables_X()
        self._add_decision_variables_Delta()

    ######################
    # Objective function #
    ######################

    def _add_objective_function(self):

        # Define the number-of-alterations expression
        nb_alterations_expression = grb.LinExpr()
        nb_alterations_expression.add(
            grb.quicksum([self.vars_X_at[j] + self.vars_X_bt[j] for j in self.get_candidate_tasks_keys()]) +
            grb.quicksum([self.vars_X_au[j] + self.vars_X_bu[j] for j in self.get_unavailabilities_keys()]) +
            self.var_X_ae + self.var_X_be +
            grb.quicksum([self.vars_X_dt[j] for j in self.get_candidate_tasks_keys()])
        )

        # Define the quantity-of-alterations expression
        quantity_alterations_expression = grb.LinExpr()
        quantity_alterations_expression.add(
            grb.quicksum([self.vars_Delta_at[j] + self.vars_Delta_bt[j] for j in self.get_candidate_tasks_keys()]) +
            grb.quicksum([self.vars_Delta_au[j] + self.vars_Delta_bu[j] for j in self.get_unavailabilities_keys()]) +
            self.var_Delta_ae + self.var_Delta_be +
            grb.quicksum([self.vars_Delta_dt[j] for j in self.get_candidate_tasks_keys()])
        )

        # Set objective function expression as a weight sum of sub objective functions
        weight_nb_alterations = 1000
        weight_quantity_alterations = 1
        OF_expression = grb.LinExpr()
        OF_expression += weight_nb_alterations * nb_alterations_expression
        OF_expression += weight_quantity_alterations * quantity_alterations_expression
        self._GRB_model.setObjective(OF_expression, sense=GRB.MINIMIZE)

        # Set objective function expression as a multi-objective function
        # self._GRB_model.ModelSense = GRB.MAXIMIZE
        # self._GRB_model.setObjectiveN(nb_alterations_expression, 0)
        # self._GRB_model.setObjectiveN(quantity_alterations_expression, 1)

        # Update GRB model
        self._GRB_model.update()

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_covering_constraints(self):

        # Add constraints about candidate tasks covering
        for j in self.get_candidate_tasks_keys():
            self._GRB_model.addLConstr(
                grb.quicksum(
                    [self.vars_U[(j, k)]
                     for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                     if k != j]
                ),
                sense=GRB.EQUAL, rhs=1,
                name=f"TaskCoveringConstraint[{j}]"
            )

        # Add constraints about unavailabilities covering
        for j in self.get_unavailabilities_keys():
            self._GRB_model.addLConstr(
                grb.quicksum(
                    [self.vars_U[(j, k)]
                     for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                     if k != j]
                ),
                sense=GRB.EQUAL, rhs=1,
                name=f"UnavailabilityCoveringConstraint[{j}]"
            )

        self._GRB_model.update()

    #############################
    # Constraints - Time window #
    #############################

    def _add_time_window_constraints(self):

        # Add time windows lower bound constraints
        for j in self.get_candidate_tasks_keys():
            self._GRB_model.addLConstr(
                self.vars_T[j] - self.get_candidate_task_by_key(j).start_time_LB + self.vars_Delta_at[j],
                sense=GRB.GREATER_EQUAL, rhs=0,
                name=f"TimeWindowLBConstraint[{j}]"
            )
            self._GRB_model.addLConstr(
                self.vars_Delta_at[j] - self.vars_X_at[j] * TASK_TW_BOUNDS_ALTERATION_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"TimeWindowLBAlterationUBConstraint[{j}]"
            )

        # Add time windows upper bound constraints
        for j in self.get_candidate_tasks_keys():
            self._GRB_model.addLConstr(
                self.vars_T[j] - self.get_candidate_task_by_key(j).end_time_UB - self.vars_Delta_dt[j]
                + self.get_candidate_task_by_key(j).duration - self.vars_Delta_bt[j],
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"TimeWindowUBConstraint[{j}]"
            )
            self._GRB_model.addLConstr(
                self.vars_Delta_bt[j] - self.vars_X_bt[j] * TASK_TW_BOUNDS_ALTERATION_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"TimeWindowUBAlterationUBConstraint[{j}]"
            )
            duration_alteration_LB = \
                np.floor(DURATION_PART_ALTERATION_UB * self.get_candidate_task_by_key(j).duration)
            self._GRB_model.addLConstr(
                self.vars_Delta_dt[j] - self.vars_X_dt[j] * duration_alteration_LB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"TaskToActivityDurationAlterationUBConstraint[{j}]"
            )

        self._GRB_model.update()

    ################################
    # Constraints - Sequence times #
    ################################

    def _add_sequence_times_constraints(self):

        # Add departure-to-first-task time sequence constraints
        for k in self.get_candidate_tasks_keys():
            self._GRB_model.addLConstr(
                self.vars_T[k]
                - self.vars_U[(LEAVING_HOME_KEY, k)]
                * (self.employee.start_time_LB + self.get_traveling_duration(LEAVING_HOME_KEY, k))
                + self.var_Delta_ae,
                sense=GRB.GREATER_EQUAL, rhs=0,
                name=f"SequenceDepartureToTaskConstraint[{k}]"
            )
        self._GRB_model.addLConstr(
            self.var_Delta_ae - self.var_X_ae * EMPLOYEE_TW_BOUNDS_ALTERATION_UB,
            sense=GRB.LESS_EQUAL, rhs=0,
            name=f"DepartureLBAlterationUBConstraint"
        )

        # Add last-task-to-comeback time sequence constraints
        for j in self.get_candidate_tasks_keys():
            self._GRB_model.addLConstr(
                self.vars_T[j] + self.get_candidate_task_by_key(j).duration - self.vars_Delta_dt[j]
                - self.vars_U[(j, COMING_BACK_HOME_KEY)]
                * (self.employee.end_time_UB - self.get_traveling_duration(j, COMING_BACK_HOME_KEY))
                - self.var_Delta_be
                - (1 - self.vars_U[(j, COMING_BACK_HOME_KEY)]) * self.get_candidate_task_by_key(j).end_time_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"SequenceTaskToComebackConstraint[{j}]"
            )
        self._GRB_model.addLConstr(
            self.var_Delta_be - self.var_X_be * EMPLOYEE_TW_BOUNDS_ALTERATION_UB,
            sense=GRB.LESS_EQUAL, rhs=0,
            name=f"ComebackUBAlterationUBConstraint"
        )

        # Add task-to-task time sequence constraints
        for j in self.get_candidate_tasks_keys():
            for k in self.get_candidate_tasks_keys():
                if k != j:
                    self._GRB_model.addLConstr(
                        self.vars_T[j] + self.get_candidate_task_by_key(j).duration - self.vars_Delta_dt[j]
                        + self.vars_U[(j, k)] * self.get_traveling_duration(j, k)
                        - self.vars_T[k] - (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_UB,
                        sense=GRB.LESS_EQUAL, rhs=0,
                        name=f"SequenceTaskToTaskConstraint[{j, k}]"
                    )

        # Add task-to-unavailability time sequence constraints
        for j in self.get_candidate_tasks_keys():
            for k in self.get_unavailabilities_keys():
                self._GRB_model.addLConstr(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration - self.vars_Delta_dt[j]
                    + self.vars_U[(j, k)] * self.get_traveling_duration(j, k)
                    - self.get_unavailability_by_key(k).start_time_LB - self.vars_Delta_au[k]
                    - (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_UB,
                    sense=GRB.LESS_EQUAL, rhs=0,
                    name=f"SequenceTaskToUnavailabilityConstraint[{j, k}]"
                )
        for k in self.get_unavailabilities_keys():
            self._GRB_model.addLConstr(
                self.vars_Delta_au[k] - self.vars_X_au[k] * UNAVAILABILITY_TW_BOUNDS_ALTERATION_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"UnavailabilityLBAlterationUBConstraint[{k}]"
            )

        # Add unavailability-to-task time sequence constraints
        for j in self.get_unavailabilities_keys():
            for k in self.get_candidate_tasks_keys():
                self._GRB_model.addLConstr(
                    self.get_unavailability_by_key(j).end_time_UB
                    + self.vars_U[(j, k)] * self.get_traveling_duration(j, k)
                    - self.vars_Delta_bu[j] - self.vars_T[k]
                    - (1 - self.vars_U[(j, k)]) * self.get_unavailability_by_key(j).end_time_UB,
                    sense=GRB.LESS_EQUAL, rhs=0,
                    name=f"SequenceUnavailabilityToTaskConstraint[{j, k}]"
                )
        for j in self.get_unavailabilities_keys():
            self._GRB_model.addLConstr(
                self.vars_Delta_bu[j] - self.vars_X_bu[j] * UNAVAILABILITY_TW_BOUNDS_ALTERATION_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"UnavailabilityUBAlterationUBConstraint[{j}]"
            )

        # Add unavailability-to-unavailability time sequence constraints
        for j in self.get_unavailabilities_keys():
            for k in self.get_unavailabilities_keys():
                if j != k:
                    self._GRB_model.addLConstr(
                        self.vars_U[(j, k)],
                        sense=GRB.LESS_EQUAL,
                        rhs=int(self.get_unavailability_by_key(j).end_time_UB +
                                self.get_traveling_duration(j, k) <=
                                self.get_unavailability_by_key(k).start_time_LB),
                        name=f"SequenceUnavailabilityToUnavailabilityConstraint[{j, k}]"
                    )

        self._GRB_model.update()

    ############
    # Solution #
    ############

    def _extract_instance_alterations(self):
        for task_key in self.get_candidate_tasks_keys():
            task = self.get_candidate_task_by_key(task_key)
            if self.vars_X_at[task_key].x == 1:
                self._alterations.set_activity_LB(task, int(-self.vars_Delta_at[task_key].x))
            if self.vars_X_bt[task_key].x == 1:
                self._alterations.set_activity_UB(task, int(self.vars_Delta_bt[task_key].x))
            if self.vars_X_dt[task_key].x == 1:
                self._alterations.set_task_duration(task, int(-self.vars_Delta_dt[task_key].x))
        for unavailability_key in self.get_unavailabilities_keys():
            unavailability = self.get_unavailability_by_key(unavailability_key)
            if self.vars_X_au[unavailability_key].x == 1:
                self._alterations.set_activity_LB(
                    unavailability, int(self.vars_Delta_au[unavailability_key].x)
                )
            if self.vars_X_bu[unavailability_key].x == 1:
                self._alterations.set_activity_UB(
                    unavailability, int(-self.vars_Delta_bu[unavailability_key].x)
                )
        if self.var_X_ae.x == 1:
            self._alterations.set_employee_LB(self.employee, int(-self.var_Delta_ae.x))
        if self.var_X_be.x == 1:
            self._alterations.set_employee_UB(self.employee, int(self.var_Delta_be.x))

    def _extract_ordered_steps(self):
        altered_employee = self._altered_instance.get_employee_by_name(self.employee.name)
        start_times_and_steps = [
            (
                altered_employee.start_time_LB,
                Step(activity=Departure(employee=altered_employee), start_time=altered_employee.start_time_LB)
            ), (
                altered_employee.end_time_UB,
                Step(activity=ComeBack(employee=altered_employee), start_time=altered_employee.end_time_UB)
            )
        ]
        for j in self.get_candidate_tasks_keys():
            if int(np.sum(
                [self.vars_U[j, k].x
                 for k in self.get_activities_keys(including_departure=False, including_comeback=True) if k != j]
            )) == 1:
                task = self.get_candidate_task_by_key(j, altered=True)
                start_time = int(self.vars_T[j].x)
                start_times_and_steps.append((start_time, Step(activity=task, start_time=start_time)))
        for j in self.get_unavailabilities_keys():
            unavailability = self.get_unavailability_by_key(j, altered=True)
            start_times_and_steps.append(
                (unavailability.start_time_LB, Step(activity=unavailability, start_time=unavailability.start_time_LB))
            )
        start_times_and_steps.sort()
        return [step for _, step in start_times_and_steps]

    def _extract_sequence_from_IP_solving(self):
        self._extract_instance_alterations()
        self._altered_instance = self.instance  # TODO alter instance with alterations
        altered_employee = self._altered_instance.get_employee_by_name(self.employee.name)
        steps = self._extract_ordered_steps()
        sequence = Sequence(self._altered_instance, altered_employee, steps)
        sequence.compute_times_based_on_fixed_start_times()
        self._sequence_from_IP_solving = sequence
