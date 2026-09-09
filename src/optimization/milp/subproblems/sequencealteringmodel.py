# Standard library
import numpy as np

# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.sequence import Sequence
from src.modeling.step import Step
from src.modeling.task import Task
from src.optimization.alteration.alterations import Alterations
from src.optimization.milp.subproblems.sequencemodel import (
    LEAVING_HOME_KEY, COMING_BACK_HOME_KEY, SequenceModel
)


# Global variables
TASK_TW_BOUNDS_ALTERATION_UB = 30
UNAVAILABILITY_TW_BOUNDS_ALTERATION_UB = 30
EMPLOYEE_TW_BOUNDS_ALTERATION_UB = 30
DURATION_PART_ALTERATION_UB = 0.1


#########################
# SequenceAlteringModel #
#########################

class SequenceAlteringModel(SequenceModel):
    """
    Extends SequenceModel with the ability to relax instance parameters (task/unavailability/employee
    time windows, task durations) when fitting an additional task, minimizing first the number of
    alterations used, then their total magnitude.
    """

    def __init__(self, sequence: Sequence, additional_task: Task):
        """
        Args:
            sequence: the existing sequence to fit the additional task into.
            additional_task: the task to fit, possibly requiring instance alterations.
        """
        candidate_tasks = sequence.get_contained_tasks() + [additional_task]
        super().__init__(sequence.instance, sequence.employee, candidate_tasks)
        self._alterations = Alterations()
        self._altered_instance = sequence.instance

    def get_candidate_task_by_key(self, task_key: str, altered: bool = False):
        """
        Return the candidate task corresponding to the given key.

        Args:
            task_key: the task's key.
            altered: if True, return the task as altered by the solution found (from
                self._altered_instance) instead of the original candidate task.
        """
        if not altered:
            return self._candidate_tasks[task_key]
        else:
            return self._altered_instance.get_task_by_name(task_key)

    def get_unavailability_by_key(self, unavailability_key: str, altered: bool = False):
        """
        Return the employee's unavailability corresponding to the given key.

        Args:
            unavailability_key: the unavailability's key.
            altered: if True, return the unavailability as altered by the solution found (from
                self._altered_instance) instead of the original unavailability.
        """
        if not altered:
            return self._employee.get_unavailability_by_name(unavailability_key)
        else:
            altered_employee = self._altered_instance.get_employee_by_name(self.employee.name)
            return altered_employee.get_unavailability_by_name(unavailability_key)

    @property
    def alterations(self):
        """The instance alterations extracted from the solution found."""
        return self._alterations

    @property
    def vars_X_at(self) -> pyo.Var:
        """Whether each candidate task's lower time-window bound is altered."""
        return self._decision_variables['X_at']

    @vars_X_at.setter
    def vars_X_at(self, X_at: pyo.Var):
        self._decision_variables['X_at'] = X_at

    @property
    def vars_Delta_at(self) -> pyo.Var:
        """The magnitude of each candidate task's lower time-window bound alteration."""
        return self._decision_variables['Delta_at']

    @vars_Delta_at.setter
    def vars_Delta_at(self, Delta_at: pyo.Var):
        self._decision_variables['Delta_at'] = Delta_at

    @property
    def vars_X_bt(self) -> pyo.Var:
        """Whether each candidate task's upper time-window bound is altered."""
        return self._decision_variables['X_bt']

    @vars_X_bt.setter
    def vars_X_bt(self, X_bt: pyo.Var):
        self._decision_variables['X_bt'] = X_bt

    @property
    def vars_Delta_bt(self) -> pyo.Var:
        """The magnitude of each candidate task's upper time-window bound alteration."""
        return self._decision_variables['Delta_bt']

    @vars_Delta_bt.setter
    def vars_Delta_bt(self, Delta_bt: pyo.Var):
        self._decision_variables['Delta_bt'] = Delta_bt

    @property
    def vars_X_au(self) -> pyo.Var:
        """Whether each unavailability's lower time-window bound is altered."""
        return self._decision_variables['X_au']

    @vars_X_au.setter
    def vars_X_au(self, X_au: pyo.Var):
        self._decision_variables['X_au'] = X_au

    @property
    def vars_Delta_au(self) -> pyo.Var:
        """The magnitude of each unavailability's lower time-window bound alteration."""
        return self._decision_variables['Delta_au']

    @vars_Delta_au.setter
    def vars_Delta_au(self, Delta_au: pyo.Var):
        self._decision_variables['Delta_au'] = Delta_au

    @property
    def vars_X_bu(self) -> pyo.Var:
        """Whether each unavailability's upper time-window bound is altered."""
        return self._decision_variables['X_bu']

    @vars_X_bu.setter
    def vars_X_bu(self, X_bu: pyo.Var):
        self._decision_variables['X_bu'] = X_bu

    @property
    def vars_Delta_bu(self) -> pyo.Var:
        """The magnitude of each unavailability's upper time-window bound alteration."""
        return self._decision_variables['Delta_bu']

    @vars_Delta_bu.setter
    def vars_Delta_bu(self, Delta_bu: pyo.Var):
        self._decision_variables['Delta_bu'] = Delta_bu

    @property
    def var_X_ae(self) -> pyo.Var:
        """Whether the employee's lower time-window bound (departure) is altered."""
        return self._decision_variables['X_ae']

    @var_X_ae.setter
    def var_X_ae(self, X_ae: pyo.Var):
        self._decision_variables['X_ae'] = X_ae

    @property
    def var_Delta_ae(self) -> pyo.Var:
        """The magnitude of the employee's lower time-window bound (departure) alteration."""
        return self._decision_variables['Delta_ae']

    @var_Delta_ae.setter
    def var_Delta_ae(self, Delta_ae: pyo.Var):
        self._decision_variables['Delta_ae'] = Delta_ae

    @property
    def var_X_be(self) -> pyo.Var:
        """Whether the employee's upper time-window bound (comeback) is altered."""
        return self._decision_variables['X_be']

    @var_X_be.setter
    def var_X_be(self, X_be: pyo.Var):
        self._decision_variables['X_be'] = X_be

    @property
    def var_Delta_be(self) -> pyo.Var:
        """The magnitude of the employee's upper time-window bound (comeback) alteration."""
        return self._decision_variables['Delta_be']

    @var_Delta_be.setter
    def var_Delta_be(self, Delta_be: pyo.Var):
        self._decision_variables['Delta_be'] = Delta_be

    @property
    def vars_X_dt(self) -> pyo.Var:
        """Whether each candidate task's duration is altered."""
        return self._decision_variables['X_dt']

    @vars_X_dt.setter
    def vars_X_dt(self, X_dt: pyo.Var):
        self._decision_variables['X_dt'] = X_dt

    @property
    def vars_Delta_dt(self) -> pyo.Var:
        """The magnitude of each candidate task's duration alteration."""
        return self._decision_variables['Delta_dt']

    @vars_Delta_dt.setter
    def vars_Delta_dt(self, Delta_dt: pyo.Var):
        self._decision_variables['Delta_dt'] = Delta_dt

    ######################
    # Decision variables #
    ######################

    def _add_decision_variables_X(self):
        self._model.X_at = pyo.Var(self._get_candidate_tasks_keys(), domain=pyo.Binary)
        self.vars_X_at = self._model.X_at
        self._model.X_bt = pyo.Var(self._get_candidate_tasks_keys(), domain=pyo.Binary)
        self.vars_X_bt = self._model.X_bt
        self._model.X_au = pyo.Var(self.get_unavailabilities_keys(), domain=pyo.Binary)
        self.vars_X_au = self._model.X_au
        self._model.X_bu = pyo.Var(self.get_unavailabilities_keys(), domain=pyo.Binary)
        self.vars_X_bu = self._model.X_bu
        self._model.X_ae = pyo.Var(domain=pyo.Binary)
        self.var_X_ae = self._model.X_ae
        self._model.X_be = pyo.Var(domain=pyo.Binary)
        self.var_X_be = self._model.X_be
        self._model.X_dt = pyo.Var(self._get_candidate_tasks_keys(), domain=pyo.Binary)
        self.vars_X_dt = self._model.X_dt

    def _add_decision_variables_Delta(self):
        self._model.Delta_at = pyo.Var(self._get_candidate_tasks_keys(), domain=pyo.NonNegativeIntegers)
        self.vars_Delta_at = self._model.Delta_at
        self._model.Delta_bt = pyo.Var(self._get_candidate_tasks_keys(), domain=pyo.NonNegativeIntegers)
        self.vars_Delta_bt = self._model.Delta_bt
        self._model.Delta_au = pyo.Var(self.get_unavailabilities_keys(), domain=pyo.NonNegativeIntegers)
        self.vars_Delta_au = self._model.Delta_au
        self._model.Delta_bu = pyo.Var(self.get_unavailabilities_keys(), domain=pyo.NonNegativeIntegers)
        self.vars_Delta_bu = self._model.Delta_bu
        self._model.Delta_ae = pyo.Var(domain=pyo.NonNegativeIntegers)
        self.var_Delta_ae = self._model.Delta_ae
        self._model.Delta_be = pyo.Var(domain=pyo.NonNegativeIntegers)
        self.var_Delta_be = self._model.Delta_be
        self._model.Delta_dt = pyo.Var(self._get_candidate_tasks_keys(), domain=pyo.NonNegativeIntegers)
        self.vars_Delta_dt = self._model.Delta_dt

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
        nb_alterations_expression = (
            pyo.quicksum([self.vars_X_at[j] + self.vars_X_bt[j] for j in self._get_candidate_tasks_keys()]) +
            pyo.quicksum([self.vars_X_au[j] + self.vars_X_bu[j] for j in self.get_unavailabilities_keys()]) +
            self.var_X_ae + self.var_X_be +
            pyo.quicksum([self.vars_X_dt[j] for j in self._get_candidate_tasks_keys()])
        )

        # Define the quantity-of-alterations expression
        quantity_alterations_expression = (
            pyo.quicksum([
                self.vars_Delta_at[j] + self.vars_Delta_bt[j] for j in self._get_candidate_tasks_keys()
            ]) +
            pyo.quicksum([
                self.vars_Delta_au[j] + self.vars_Delta_bu[j] for j in self.get_unavailabilities_keys()
            ]) +
            self.var_Delta_ae + self.var_Delta_be +
            pyo.quicksum([self.vars_Delta_dt[j] for j in self._get_candidate_tasks_keys()])
        )

        # Set objective function expression as a weight sum of sub objective functions
        weight_nb_alterations = 1000
        weight_quantity_alterations = 1
        objective_expression = (weight_nb_alterations * nb_alterations_expression +
                                weight_quantity_alterations * quantity_alterations_expression)
        self._model.objective = pyo.Objective(expr=objective_expression, sense=pyo.minimize)

        # Set objective function expression as a multi-objective function
        # self._model.ModelSense = GRB.MAXIMIZE
        # self._model.setObjectiveN(nb_alterations_expression, 0)
        # self._model.setObjectiveN(quantity_alterations_expression, 1)

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_covering_constraints(self):

        # Add constraints about candidate tasks covering
        for j in self._get_candidate_tasks_keys():
            self._model.add_component(
                f"TaskCoveringConstraint[{j}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([
                        self.vars_U[(j, k)]
                        for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                        if k != j
                    ]) == 1
                ))
            )

        # Add constraints about unavailabilities covering
        for j in self.get_unavailabilities_keys():
            self._model.add_component(
                f"UnavailabilityCoveringConstraint[{j}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([
                        self.vars_U[(j, k)]
                        for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                        if k != j
                    ]) == 1
                ))
            )

    #############################
    # Constraints - Time window #
    #############################

    def _add_time_window_constraints(self):

        # Add time windows lower bound constraints
        for j in self._get_candidate_tasks_keys():
            self._model.add_component(
                f"TimeWindowLBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] - self.get_candidate_task_by_key(j).start_time_lb + self.vars_Delta_at[j] >= 0
                ))
            )
            self._model.add_component(
                f"TimeWindowLBAlterationUBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_Delta_at[j] - self.vars_X_at[j] * TASK_TW_BOUNDS_ALTERATION_UB <= 0
                ))
            )

        # Add time windows upper bound constraints
        for j in self._get_candidate_tasks_keys():
            self._model.add_component(
                f"TimeWindowUBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] - self.get_candidate_task_by_key(j).end_time_ub - self.vars_Delta_dt[j]
                    + self.get_candidate_task_by_key(j).duration - self.vars_Delta_bt[j] <= 0
                ))
            )
            self._model.add_component(
                f"TimeWindowUBAlterationUBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_Delta_bt[j] - self.vars_X_bt[j] * TASK_TW_BOUNDS_ALTERATION_UB <= 0
                ))
            )
            duration_alteration_lb = \
                np.floor(DURATION_PART_ALTERATION_UB * self.get_candidate_task_by_key(j).duration)
            self._model.add_component(
                f"TaskToActivityDurationAlterationUBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_Delta_dt[j] - self.vars_X_dt[j] * duration_alteration_lb <= 0
                ))
            )

    ################################
    # Constraints - Sequence times #
    ################################

    def _add_sequence_times_constraints(self):

        # Add departure-to-first-task time sequence constraints
        for k in self._get_candidate_tasks_keys():
            self._model.add_component(
                f"SequenceDepartureToTaskConstraint[{k}]",
                pyo.Constraint(expr=(
                    self.vars_T[k]
                    - self.vars_U[(LEAVING_HOME_KEY, k)]
                    * (self.employee.start_time_lb + self.get_traveling_duration(LEAVING_HOME_KEY, k))
                    + self.var_Delta_ae >= 0
                ))
            )
        self._model.add_component(
            "DepartureLBAlterationUBConstraint",
            pyo.Constraint(expr=(self.var_Delta_ae - self.var_X_ae * EMPLOYEE_TW_BOUNDS_ALTERATION_UB <= 0))
        )

        # Add last-task-to-comeback time sequence constraints
        for j in self._get_candidate_tasks_keys():
            self._model.add_component(
                f"SequenceTaskToComebackConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration - self.vars_Delta_dt[j]
                    - self.vars_U[(j, COMING_BACK_HOME_KEY)]
                    * (self.employee.end_time_ub - self.get_traveling_duration(j, COMING_BACK_HOME_KEY))
                    - self.var_Delta_be
                    - (1 - self.vars_U[(j, COMING_BACK_HOME_KEY)]) * self.get_candidate_task_by_key(j).end_time_ub
                    <= 0
                ))
            )
        self._model.add_component(
            "ComebackUBAlterationUBConstraint",
            pyo.Constraint(expr=(self.var_Delta_be - self.var_X_be * EMPLOYEE_TW_BOUNDS_ALTERATION_UB <= 0))
        )

        # Add task-to-task time sequence constraints
        for j in self._get_candidate_tasks_keys():
            for k in self._get_candidate_tasks_keys():
                if k != j:
                    self._model.add_component(
                        f"SequenceTaskToTaskConstraint[{j, k}]",
                        pyo.Constraint(expr=(
                            self.vars_T[j] + self.get_candidate_task_by_key(j).duration - self.vars_Delta_dt[j]
                            + self.vars_U[(j, k)] * self.get_traveling_duration(j, k)
                            - self.vars_T[k] - (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_ub
                            <= 0
                        ))
                    )

        # Add task-to-unavailability time sequence constraints
        for j in self._get_candidate_tasks_keys():
            for k in self.get_unavailabilities_keys():
                self._model.add_component(
                    f"SequenceTaskToUnavailabilityConstraint[{j, k}]",
                    pyo.Constraint(expr=(
                        self.vars_T[j] + self.get_candidate_task_by_key(j).duration - self.vars_Delta_dt[j]
                        + self.vars_U[(j, k)] * self.get_traveling_duration(j, k)
                        - self.get_unavailability_by_key(k).start_time_lb - self.vars_Delta_au[k]
                        - (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_ub <= 0
                    ))
                )
        for k in self.get_unavailabilities_keys():
            self._model.add_component(
                f"UnavailabilityLBAlterationUBConstraint[{k}]",
                pyo.Constraint(expr=(
                    self.vars_Delta_au[k] - self.vars_X_au[k] * UNAVAILABILITY_TW_BOUNDS_ALTERATION_UB <= 0
                ))
            )

        # Add unavailability-to-task time sequence constraints
        for j in self.get_unavailabilities_keys():
            for k in self._get_candidate_tasks_keys():
                self._model.add_component(
                    f"SequenceUnavailabilityToTaskConstraint[{j, k}]",
                    pyo.Constraint(expr=(
                        self.get_unavailability_by_key(j).end_time_ub
                        + self.vars_U[(j, k)] * self.get_traveling_duration(j, k)
                        - self.vars_Delta_bu[j] - self.vars_T[k]
                        - (1 - self.vars_U[(j, k)]) * self.get_unavailability_by_key(j).end_time_ub <= 0
                    ))
                )
        for j in self.get_unavailabilities_keys():
            self._model.add_component(
                f"UnavailabilityUBAlterationUBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_Delta_bu[j] - self.vars_X_bu[j] * UNAVAILABILITY_TW_BOUNDS_ALTERATION_UB <= 0
                ))
            )

        # Add unavailability-to-unavailability time sequence constraints
        for j in self.get_unavailabilities_keys():
            for k in self.get_unavailabilities_keys():
                if j != k:
                    self._model.add_component(
                        f"SequenceUnavailabilityToUnavailabilityConstraint[{j, k}]",
                        pyo.Constraint(expr=(
                            self.vars_U[(j, k)] <=
                            int(self.get_unavailability_by_key(j).end_time_ub +
                                self.get_traveling_duration(j, k) <=
                                self.get_unavailability_by_key(k).start_time_lb)
                        ))
                    )

    ############
    # Solution #
    ############

    def _extract_instance_alterations(self):
        """Populate self._alterations from the activation/magnitude decision variables' values in the solution."""
        for task_key in self._get_candidate_tasks_keys():
            task = self.get_candidate_task_by_key(task_key)
            if round(pyo.value(self.vars_X_at[task_key])) == 1:
                self._alterations.set_activity_LB(task, -round(pyo.value(self.vars_Delta_at[task_key])))
            if round(pyo.value(self.vars_X_bt[task_key])) == 1:
                self._alterations.set_activity_UB(task, round(pyo.value(self.vars_Delta_bt[task_key])))
            if round(pyo.value(self.vars_X_dt[task_key])) == 1:
                self._alterations.set_task_duration(task, -round(pyo.value(self.vars_Delta_dt[task_key])))
        for unavailability_key in self.get_unavailabilities_keys():
            unavailability = self.get_unavailability_by_key(unavailability_key)
            if round(pyo.value(self.vars_X_au[unavailability_key])) == 1:
                self._alterations.set_activity_LB(
                    unavailability, round(pyo.value(self.vars_Delta_au[unavailability_key]))
                )
            if round(pyo.value(self.vars_X_bu[unavailability_key])) == 1:
                self._alterations.set_activity_UB(
                    unavailability, -round(pyo.value(self.vars_Delta_bu[unavailability_key]))
                )
        if round(pyo.value(self.var_X_ae)) == 1:
            self._alterations.set_employee_LB(self.employee, -round(pyo.value(self.var_Delta_ae)))
        if round(pyo.value(self.var_X_be)) == 1:
            self._alterations.set_employee_UB(self.employee, round(pyo.value(self.var_Delta_be)))

    def _extract_ordered_steps(self):
        """Build the ordered list of Steps making up the solution sequence, using altered activities."""
        altered_employee = self._altered_instance.get_employee_by_name(self.employee.name)
        start_times_and_steps = [
            (
                altered_employee.start_time_lb,
                Step(activity=Departure(employee=altered_employee), start_time=altered_employee.start_time_lb)
            ), (
                altered_employee.end_time_ub,
                Step(activity=ComeBack(employee=altered_employee), start_time=altered_employee.end_time_ub)
            )
        ]
        for j in self._get_candidate_tasks_keys():
            if round(np.sum(
                [pyo.value(self.vars_U[j, k])
                 for k in self.get_activities_keys(including_departure=False, including_comeback=True) if k != j]
            )) == 1:
                task = self.get_candidate_task_by_key(j, altered=True)
                start_time = round(pyo.value(self.vars_T[j]))
                start_times_and_steps.append((start_time, Step(activity=task, start_time=start_time)))
        for j in self.get_unavailabilities_keys():
            unavailability = self.get_unavailability_by_key(j, altered=True)
            start_times_and_steps.append(
                (unavailability.start_time_lb, Step(activity=unavailability, start_time=unavailability.start_time_lb))
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
