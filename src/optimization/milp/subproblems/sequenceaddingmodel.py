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
from src.optimization.milp.subproblems.sequencemodel import SequenceModel, LEAVING_HOME_KEY, COMING_BACK_HOME_KEY


#######################
# SequenceAddingModel #
#######################

class SequenceAddingModel(SequenceModel):
    """
    Fits one new task into an existing sequence at its best position,
    using a split backward/forward start-time pair to measure the resulting time gap,
    minimized alongside traveling duration.
    """

    def __init__(self, sequence: Sequence, new_task: Task):
        """
        Args:
            sequence: the existing sequence to add the new task into.
            new_task: the task to add.
        """
        candidate_tasks = sequence.get_contained_tasks() + [new_task]
        self._new_task = new_task
        super().__init__(sequence.instance, sequence.employee, candidate_tasks)

    @property
    def new_task(self):
        """The task being added to the sequence."""
        return self._new_task

    def _get_candidate_tasks_keys(self, including_new_task: bool = True):
        """
        Return the keys of the candidate tasks, optionally excluding the new task
        (which is handled separately via the split var_T_backward/var_T_forward variables).

        Args:
            including_new_task: if True, include the new task's key.
        """
        if including_new_task:
            return [task.name for task in self.candidate_tasks]
        else:
            return [task.name for task in self.candidate_tasks if task != self._new_task]

    def get_new_task_key(self):
        """Return the new task's key."""
        return self._new_task.name

    @property
    def new_task_time_gap(self):
        """
        The gap between the new task's backward and forward start-time bounds in the solution found.

        Raises:
            AttributeError: if solve() hasn't been called yet, or found no feasible solution.
        """
        if self.has_solution_sequence:
            return pyo.value(self.var_T_backward) - pyo.value(self.var_T_forward)
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def new_task_start_time(self):
        """
        The new task's start time in the solution found (its backward start-time bound).

        Raises:
            AttributeError: if solve() hasn't been called yet, or found no feasible solution.
        """
        if self.has_solution_sequence:
            return pyo.value(self.var_T_backward)
            # return int((self.var_T_backward.x + self.var_T_forward.x)/2)
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def new_task_start_time_for_backward(self):
        """
        The new task's backward start-time bound in the solution found.

        Raises:
            AttributeError: if solve() hasn't been called yet, or found no feasible solution.
        """
        if self.has_solution_sequence:
            return pyo.value(self.var_T_backward)
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def new_task_start_time_for_forward(self):
        """
        The new task's forward start-time bound in the solution found.

        Raises:
            AttributeError: if solve() hasn't been called yet, or found no feasible solution.
        """
        if self.has_solution_sequence:
            return pyo.value(self.var_T_forward)
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def support_sequence(self) -> Sequence:
        """The solution sequence found, including the new task."""
        return self.solution_sequence

    ######################
    # Decision variables #
    ######################

    def _add_decision_variables_T(self):
        self._model.T = pyo.Var(
            self._get_candidate_tasks_keys(including_new_task=False), domain=pyo.NonNegativeIntegers
        )
        self.vars_T = self._model.T

    def _add_decision_variables_split_T(self):
        self._model.Tb = pyo.Var(domain=pyo.NonNegativeIntegers)
        self._model.Ta = pyo.Var(domain=pyo.NonNegativeIntegers)
        self.var_T_backward = self._model.Tb
        self.var_T_forward = self._model.Ta

    def _add_decision_variables(self):
        self._add_decision_variables_T()
        self._add_decision_variables_split_T()
        self._add_decision_variables_U()

    ######################
    # Objective function #
    ######################

    def _add_objective_function(self):

        # Define the times gap expression
        time_gap_expression = self.var_T_backward - self.var_T_forward

        # Define the total-traveling-duration expression
        traveling_duration_expression = pyo.quicksum([
            self.vars_U[indices] *
            self.get_traveling_duration(activity_key1=indices[0], activity_key2=indices[1])
            for indices in self.vars_U.keys()
        ])

        # Set objective function expression as a weighted sum of the sub-objective functions
        self.weight_time_gap = 1000
        self.weight_traveling_duration = 1
        objective_expression = (self.weight_time_gap * time_gap_expression +
                                self.weight_traveling_duration * traveling_duration_expression)
        self._model.objective = pyo.Objective(expr=objective_expression, sense=pyo.minimize)

        # Set objective function expression as a multi-objective function
        # self._model.ModelSense = GRB.MINIMIZE
        # self._model.setObjectiveN(time_gap_expression, 0)
        # self._model.setObjectiveN(traveling_duration_expression, 1)

    ###############
    # Constraints #
    ###############

    def _add_constraints(self):
        """Add all constraints to the model: same as SequenceModel, plus the split-time constraint."""
        self._add_covering_constraints()
        self._add_flow_constraints()
        self._add_time_window_constraints()
        self._add_sequence_times_constraints()
        self._add_split_time_constraint()
        # No skill constraints

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

        # Add time windows lower bounds constraints for prior tasks
        for j in self._get_candidate_tasks_keys(including_new_task=False):
            self._model.add_component(
                f"TimeWindowLBConstraint[{j}]",
                pyo.Constraint(expr=(self.vars_T[j] - self.get_candidate_task_by_key(j).start_time_lb >= 0))
            )

        # Add time window lower bound constraint for new task
        j = self.get_new_task_key()
        self._model.add_component(
            f"TimeWindowLBConstraint[{j}]",
            pyo.Constraint(expr=(self.var_T_backward - self.get_candidate_task_by_key(j).start_time_lb >= 0))
        )

        # Add time windows upper bounds constraints for prior tasks
        for j in self._get_candidate_tasks_keys(including_new_task=False):
            self._model.add_component(
                f"TimeWindowUBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration
                    - self.get_candidate_task_by_key(j).end_time_ub <= 0
                ))
            )

        # Add time window upper bound constraint for new task
        j = self.get_new_task_key()
        self._model.add_component(
            f"TimeWindowUBConstraint[{j}]",
            pyo.Constraint(expr=(
                self.var_T_forward + self.get_candidate_task_by_key(j).duration
                - self.get_candidate_task_by_key(j).end_time_ub <= 0
            ))
        )

    ################################
    # Constraints - Sequence times #
    ################################

    def _add_sequence_times_constraints(self):

        # Add departure-to-first-task time sequence constraints
        # - for prior tasks
        for k in self._get_candidate_tasks_keys(including_new_task=False):
            self._model.add_component(
                f"SequenceDepartureToTaskConstraint[{k}]",
                pyo.Constraint(expr=(
                    self.vars_T[k] -
                    (self.employee.start_time_lb + self.get_traveling_duration(LEAVING_HOME_KEY, k)) *
                    self.vars_U[(LEAVING_HOME_KEY, k)] >= 0
                ))
            )
        # - for new task
        k = self.get_new_task_key()
        self._model.add_component(
            f"SequenceDepartureToTaskConstraint[{k}]",
            pyo.Constraint(expr=(
                self.var_T_backward -
                (self.employee.start_time_lb + self.get_traveling_duration(LEAVING_HOME_KEY, k)) *
                self.vars_U[(LEAVING_HOME_KEY, k)] >= 0
            ))
        )

        # Add last-task-to-comeback time sequence constraints
        # - for prior tasks
        for j in self._get_candidate_tasks_keys(including_new_task=False):
            self._model.add_component(
                f"SequenceTaskToComebackConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                    self.vars_U[(j, COMING_BACK_HOME_KEY)] *
                    (self.employee.end_time_ub - self.get_traveling_duration(j, COMING_BACK_HOME_KEY)) -
                    (1 - self.vars_U[(j, COMING_BACK_HOME_KEY)]) * self.get_candidate_task_by_key(j).end_time_ub <= 0
                ))
            )
        # - for new task
        j = self.get_new_task_key()
        self._model.add_component(
            f"SequenceTaskToComebackConstraint[{j}]",
            pyo.Constraint(expr=(
                self.var_T_forward + self.get_candidate_task_by_key(j).duration -
                self.vars_U[(j, COMING_BACK_HOME_KEY)] *
                (self.employee.end_time_ub - self.get_traveling_duration(j, COMING_BACK_HOME_KEY)) -
                (1 - self.vars_U[(j, COMING_BACK_HOME_KEY)]) * self.get_candidate_task_by_key(j).end_time_ub <= 0
            ))
        )

        # Add task-to-task time sequence constraints
        for j in self._get_candidate_tasks_keys(including_new_task=False):
            # - with j and k prior tasks
            for k in self._get_candidate_tasks_keys(including_new_task=False):
                if k != j:
                    self._model.add_component(
                        f"SequenceTaskToTaskConstraint[{j, k}]",
                        pyo.Constraint(expr=(
                            self.vars_T[j] + self.get_candidate_task_by_key(j).duration +
                            self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                            self.vars_T[k] -
                            (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_ub <= 0
                        ))
                    )
            # - with j prior task and k new task
            k = self.get_new_task_key()
            self._model.add_component(
                f"SequenceTaskToTaskConstraint[{j, k}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration +
                    self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                    self.var_T_backward -
                    (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_ub <= 0
                ))
            )
        # - with j new task and k prior task
        j = self.get_new_task_key()
        for k in self._get_candidate_tasks_keys(including_new_task=False):
            self._model.add_component(
                f"SequenceTaskToTaskConstraint[{j, k}]",
                pyo.Constraint(expr=(
                    self.var_T_forward + self.get_candidate_task_by_key(j).duration +
                    self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                    self.vars_T[k] -
                    (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_ub <= 0
                ))
            )

        # Add task-to-unavailability time sequence constraints
        # - for prior tasks
        for j in self._get_candidate_tasks_keys(including_new_task=False):
            for k in self.get_unavailabilities_keys():
                self._model.add_component(
                    f"SequenceTaskToUnavailabilityConstraint[{j, k}]",
                    pyo.Constraint(expr=(
                        self.vars_T[j] + self.get_candidate_task_by_key(j).duration +
                        self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                        self.get_unavailability_by_key(k).start_time_lb -
                        (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_ub <= 0
                    ))
                )
        # - for new task
        j = self.get_new_task_key()
        for k in self.get_unavailabilities_keys():
            self._model.add_component(
                f"SequenceTaskToUnavailabilityConstraint[{j, k}]",
                pyo.Constraint(expr=(
                    self.var_T_forward + self.get_candidate_task_by_key(j).duration +
                    self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                    self.get_unavailability_by_key(k).start_time_lb -
                    (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_ub <= 0
                ))
            )

        # Add unavailability-to-task time sequence constraints
        # - for old tasks
        for j in self.get_unavailabilities_keys():
            for k in self._get_candidate_tasks_keys(including_new_task=False):
                self._model.add_component(
                    f"SequenceUnavailabilityToTaskConstraint[{j, k}]",
                    pyo.Constraint(expr=(
                        self.get_unavailability_by_key(j).end_time_ub +
                        self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                        self.vars_T[k] -
                        (1 - self.vars_U[(j, k)]) * self.get_unavailability_by_key(j).end_time_ub <= 0
                    ))
                )
        # - for new task
        k = self.get_new_task_key()
        for j in self.get_unavailabilities_keys():
            self._model.add_component(
                f"SequenceUnavailabilityToTaskConstraint[{j, k}]",
                pyo.Constraint(expr=(
                    self.get_unavailability_by_key(j).end_time_ub +
                    self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                    self.var_T_backward -
                    (1 - self.vars_U[(j, k)]) * self.get_unavailability_by_key(j).end_time_ub <= 0
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

    ############################
    # Constraints - Split time #
    ############################

    def _add_split_time_constraint(self):
        """Force the new task's backward start-time bound to be at least its forward one."""
        self._model.add_component(
            f"TimeSplit[{self.get_new_task_key()}]",
            pyo.Constraint(expr=(self.var_T_backward - self.var_T_forward >= 0))
        )

    ###########
    # Results #
    ###########

    def _extract_ordered_steps(self):
        """Build the ordered list of Steps making up the solution sequence, including the new task."""
        start_times_and_steps = [
            (
                self.employee.start_time_lb,
                Step(activity=Departure(employee=self.employee), start_time=self.employee.start_time_lb)
            ), (
                self.employee.end_time_ub,
                Step(activity=ComeBack(employee=self.employee), start_time=self.employee.end_time_ub)
            )
        ]
        for j in self._get_candidate_tasks_keys(including_new_task=False):
            task = self.get_candidate_task_by_key(j)
            start_time = round(pyo.value(self.vars_T[j]))
            start_times_and_steps.append((start_time, Step(activity=task, start_time=start_time)))
        j = self.get_new_task_key()
        task = self.get_candidate_task_by_key(j)
        start_time = round(pyo.value(self.var_T_backward))
        start_times_and_steps.append((start_time, Step(activity=task, start_time=start_time)))
        for j in self.get_unavailabilities_keys():
            unavailability = self.get_unavailability_by_key(j)
            start_times_and_steps.append(
                (unavailability.start_time_lb, Step(activity=unavailability, start_time=unavailability.start_time_lb))
            )
        start_times_and_steps.sort()
        return [step for _, step in start_times_and_steps]
