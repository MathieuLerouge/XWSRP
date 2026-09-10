# Standard library
from abc import abstractmethod

# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.sequence import Sequence
from src.modeling.step import Step
from src.modeling.task import Task
from src.optimization.milp.solver.solver import Solver
from src.optimization.milp.subproblems.sequencemodel import SequenceModel, \
    LEAVING_HOME_KEY, COMING_BACK_HOME_KEY


#######################
# IPModelForCategory3 #
#######################

class IPModelForCategory3(SequenceModel):

    def __init__(self, sequence: Sequence, pivot_task: Task):
        self._pivot_task = pivot_task
        self._sequence = sequence
        super().__init__(sequence.instance, sequence.employee, self._compute_candidate_tasks())

    @abstractmethod
    def _compute_candidate_tasks(self):
        pass

    @property
    def pivot_task(self):
        return self._pivot_task

    def get_pivot_task_key(self):
        return self._pivot_task.name

    @property
    def pivot_task_key(self):
        return self._pivot_task.name

    @property
    def pivot_task_time_gap(self):
        if self.has_solution_sequence:
            return round(pyo.value(self.var_T_backward) - pyo.value(self.var_T_forward))
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def pivot_task_start_time(self):
        if self.has_solution_sequence:
            return round(pyo.value(self.var_T_backward))
            # return int((self.var_T_backward.x + self.var_T_forward.x)/2)
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def pivot_task_start_time_for_backward(self):
        if self.has_solution_sequence:
            return round(pyo.value(self.var_T_backward))
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def pivot_task_start_time_for_forward(self):
        if self.has_solution_sequence:
            return round(pyo.value(self.var_T_forward))
        else:
            raise AttributeError("There is no solution sequence stored")

    def _get_candidate_tasks_keys(self, including_pivot_task: bool = True):
        if including_pivot_task:
            return [task.name for task in self.candidate_tasks]
        else:
            return [task.name for task in self.candidate_tasks if task != self._pivot_task]

    @property
    def support_sequence(self) -> Sequence:
        return self.solution_sequence

    @property
    def time_limit(self):
        return self.solving_time_limit

    @time_limit.setter
    def time_limit(self, time_limit: int):
        self.solving_time_limit = time_limit

    ######################
    # Decision variables #
    ######################

    def _add_decision_variables(self):
        self._add_decision_variables_T()
        self._add_decision_variables_split_T()
        self._add_decision_variables_U()

    def _add_decision_variables_T(self):
        self._model.T = pyo.Var(
            self._get_candidate_tasks_keys(including_pivot_task=False), domain=pyo.NonNegativeIntegers
        )
        self.vars_T = self._model.T

    def _add_decision_variables_split_T(self):
        self._model.Tb = pyo.Var(domain=pyo.NonNegativeIntegers)
        self._model.Ta = pyo.Var(domain=pyo.NonNegativeIntegers)
        self.var_T_backward = self._model.Tb
        self.var_T_forward = self._model.Ta

    ##################
    # Key quantities #
    ##################

    def _compute_time_gap_expression(self):
        self.time_gap_expression = self.var_T_backward - self.var_T_forward

    def _compute_tasks_performances_expressions(self):
        self.tasks_performances_expressions = dict([
            (j, pyo.quicksum([self.vars_U[j, k]
                              for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                              if k != j]))
            for j in self._get_candidate_tasks_keys()
        ])

    def _compute_working_duration_expression(self):
        self.working_duration_expression = \
            pyo.quicksum(
                [self.tasks_performances_expressions[j] * self.get_candidate_task_by_key(j).duration
                 for j in self._get_candidate_tasks_keys()]
            )

    def _compute_traveling_duration_expression(self):
        self.traveling_duration_expression = \
            pyo.quicksum(
                [self.vars_U[indices] *
                 self.get_traveling_duration(activity_key1=indices[0], activity_key2=indices[1])
                 for indices in self.vars_U.keys()]
            )

    def _compute_key_quantities(self):
        self._compute_time_gap_expression()
        self._compute_tasks_performances_expressions()
        self._compute_working_duration_expression()
        self._compute_traveling_duration_expression()

    ######################
    # Objective function #
    ######################

    def _add_objective_function(self):
        """
        Build the objectives that will be minimized according to a lexicographic order, highest priority first:
        the time gap, the working duration, then the traveling duration. Solved lexicographically (one solve per
        objective, see _solve) since Pyomo/HiGHS have no equivalent of Gurobi's setObjectiveN hierarchical
        multi-objective feature.
        """
        self._compute_key_quantities()
        self._objectives_in_priority_order = [
            self.time_gap_expression, self.working_duration_expression, self.traveling_duration_expression
        ]

    def _solve(self, mute: bool, solver_name: str):
        solver = Solver(solver_name, mute=mute, time_limit=self._solving_time_limit)
        return solver.solve_lexicographically(self._model, self._objectives_in_priority_order)

    ###############
    # Constraints #
    ###############

    def _add_constraints(self):
        self._add_covering_constraints()
        self._add_flow_constraints()
        self._add_time_window_constraints()
        self._add_sequence_times_constraints()
        self._add_split_time_constraint()
        self._add_no_sub_loops_around_pivot_task_constraints()
        # No skill constraints

    ##########################
    # Constraints - Covering #
    ##########################

    @abstractmethod
    def _add_tasks_covering_constraints(self):
        pass

    def _add_covering_constraints(self):
        # Add constraints about candidate tasks covering
        self._add_tasks_covering_constraints()
        # Add constraints about employees unavailabilities covering
        for j in self.get_unavailabilities_keys():
            self._model.add_component(
                f"UnavailabilityCoveringConstraint[{j}]",
                pyo.Constraint(expr=(
                    pyo.quicksum(
                        [self.vars_U[(j, k)]
                         for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                         if k != j]
                    ) == 1
                ))
            )

    #############################
    # Constraints - Time window #
    #############################

    def _add_time_window_constraints(self):
        # Add time window lower bound constraint for pivot task
        j = self.get_pivot_task_key()
        self._model.add_component(
            f"TimeWindowLBConstraint[{j}]",
            pyo.Constraint(expr=(self.var_T_backward - self.get_candidate_task_by_key(j).start_time_lb >= 0))
        )
        # Add time windows lower bounds constraints for all other tasks
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._model.add_component(
                f"TimeWindowLBConstraint[{j}]",
                pyo.Constraint(expr=(self.vars_T[j] - self.get_candidate_task_by_key(j).start_time_lb >= 0))
            )
        # Add time window upper bound constraint for pivot task
        j = self.get_pivot_task_key()
        self._model.add_component(
            f"TimeWindowUBConstraint[{j}]",
            pyo.Constraint(expr=(
                self.var_T_forward + self.get_candidate_task_by_key(j).duration
                - self.get_candidate_task_by_key(j).end_time_ub <= 0
            ))
        )
        # Add time windows upper bounds constraints for all other tasks
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._model.add_component(
                f"TimeWindowUBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration
                    - self.get_candidate_task_by_key(j).end_time_ub <= 0
                ))
            )

    ################################
    # Constraints - Sequence times #
    ################################

    def _add_sequence_times_constraints(self):
        # Add departure-to-first-task time sequence constraints - for pivot task
        k = self.get_pivot_task_key()
        self._model.add_component(
            f"SequenceDepartureToTaskConstraint[{k}]",
            pyo.Constraint(expr=(
                self.var_T_backward -
                (self.employee.start_time_lb + self.get_traveling_duration(LEAVING_HOME_KEY, k)) *
                self.vars_U[(LEAVING_HOME_KEY, k)] >= 0
            ))
        )
        # Add departure-to-first-task time sequence constraints - for all other tasks
        for k in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._model.add_component(
                f"SequenceDepartureToTaskConstraint[{k}]",
                pyo.Constraint(expr=(
                    self.vars_T[k] -
                    (self.employee.start_time_lb + self.get_traveling_duration(LEAVING_HOME_KEY, k)) *
                    self.vars_U[(LEAVING_HOME_KEY, k)] >= 0
                ))
            )
        # Add last-task-to-comeback time sequence constraints - for pivot task
        j = self.get_pivot_task_key()
        self._model.add_component(
            f"SequenceTaskToComebackConstraint[{j}]",
            pyo.Constraint(expr=(
                self.var_T_forward + self.get_candidate_task_by_key(j).duration -
                self.vars_U[(j, COMING_BACK_HOME_KEY)] *
                (self.employee.end_time_ub - self.get_traveling_duration(j, COMING_BACK_HOME_KEY)) -
                (1 - self.vars_U[(j, COMING_BACK_HOME_KEY)]) * self.get_candidate_task_by_key(j).end_time_ub <= 0
            ))
        )
        # Add last-task-to-comeback time sequence constraints - for all other tasks
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._model.add_component(
                f"SequenceTaskToComebackConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                    self.vars_U[(j, COMING_BACK_HOME_KEY)] *
                    (self.employee.end_time_ub - self.get_traveling_duration(j, COMING_BACK_HOME_KEY)) -
                    (1 - self.vars_U[(j, COMING_BACK_HOME_KEY)]) * self.get_candidate_task_by_key(j).end_time_ub <= 0
                ))
            )
        # Add task-to-task time sequence constraints
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            # - with j and k prior tasks
            for k in self._get_candidate_tasks_keys(including_pivot_task=False):
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
            # - with j prior task and k pivot task
            k = self.get_pivot_task_key()
            self._model.add_component(
                f"SequenceTaskToTaskConstraint[{j, k}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration +
                    self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                    self.var_T_backward -
                    (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_ub <= 0
                ))
            )
        # - with j pivot task and k other task
        j = self.get_pivot_task_key()
        for k in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._model.add_component(
                f"SequenceTaskToTaskConstraint[{j, k}]",
                pyo.Constraint(expr=(
                    self.var_T_forward + self.get_candidate_task_by_key(j).duration +
                    self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                    self.vars_T[k] -
                    (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_ub <= 0
                ))
            )
        # Add task-to-unavailability time sequence constraints - for pivot task
        j = self.get_pivot_task_key()
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
        # Add task-to-unavailability time sequence constraints - for all other tasks
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
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
        # Add unavailability-to-task time sequence constraints - for new task
        k = self.get_pivot_task_key()
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
        # Add unavailability-to-task time sequence constraints - for all other tasks
        for j in self.get_unavailabilities_keys():
            for k in self._get_candidate_tasks_keys(including_pivot_task=False):
                self._model.add_component(
                    f"SequenceUnavailabilityToTaskConstraint[{j, k}]",
                    pyo.Constraint(expr=(
                        self.get_unavailability_by_key(j).end_time_ub +
                        self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                        self.vars_T[k] -
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
        self._model.add_component(
            f"TimeSplit[{self.get_pivot_task_key()}]",
            pyo.Constraint(expr=(self.var_T_backward - self.var_T_forward >= 0))
        )

    ###########################
    # Constraints - Sub-loops #
    ###########################

    def _add_no_sub_loops_around_pivot_task_constraints(self):
        j = self.get_pivot_task_key()
        for k in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._model.add_component(
                f"NoSubLoops[{k}]",
                pyo.Constraint(expr=(self.vars_U[(j, k)] + self.vars_U[(k, j)] <= 1))
            )

    ############
    # Solution #
    ############

    def _check_task_is_performed_by_key(self, task_key: str):
        return round(pyo.value(self.tasks_performances_expressions[task_key])) == 1

    def _extract_ordered_steps(self):
        start_times_and_steps = [
            (self.employee.start_time_lb,
             Step(activity=Departure(employee=self.employee), start_time=self.employee.start_time_lb))
        ]
        j = LEAVING_HOME_KEY
        while j != COMING_BACK_HOME_KEY:
            for (k, l) in self.vars_U.keys():
                if k == j and round(pyo.value(self.vars_U[(k, l)])) == 1:
                    j = l
                    if j == COMING_BACK_HOME_KEY:
                        break
                    else:
                        task = self.get_candidate_task_by_key(j)
                        if j == self.get_pivot_task_key():
                            start_time = round(pyo.value(self.var_T_backward))
                        else:
                            start_time = round(pyo.value(self.vars_T[j]))
                        start_times_and_steps.append((start_time, Step(activity=task, start_time=start_time)))
                        break
        start_times_and_steps.append(
            (self.employee.end_time_ub,
             Step(activity=ComeBack(employee=self.employee), start_time=self.employee.end_time_ub))
        )
        _, first_step = start_times_and_steps[0]
        if not isinstance(first_step.activity, Departure):
            raise Exception(f"The first activity of the sequence is not a departure but {first_step}")
        _, last_step = start_times_and_steps[-1]
        if not isinstance(last_step.activity, ComeBack):
            raise Exception(f"The last activity of the sequence is not a comeback but {last_step}")
        return [step for _, step in start_times_and_steps]
