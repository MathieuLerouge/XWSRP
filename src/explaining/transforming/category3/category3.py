# Standard library
from abc import abstractmethod

# Third party libraries
import gurobipy as grb
from gurobipy import GRB

# Local libraries
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.sequence import Sequence
from src.modeling.step import Step
from src.modeling.task import Task
from src.optimization.IP.sequence.basemodel import IPModelForSequenceOptimization, LEAVING_HOME_KEY, COMING_BACK_HOME_KEY


# Class IPModelForCategory3
class IPModelForCategory3(IPModelForSequenceOptimization):

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

    def get_candidate_tasks_keys(self, including_pivot_task: bool = True):
        if including_pivot_task:
            return [task.name for task in self.candidate_tasks]
        else:
            return [task.name for task in self.candidate_tasks if task != self._pivot_task]

    def get_pivot_task_key(self):
        return self._pivot_task.name

    @property
    def pivot_task_key(self):
        return self._pivot_task.name

    @property
    def pivot_task_time_gap(self):
        if self.has_solution_sequence:
            return self.var_T_backward.x - self.var_T_forward.x
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def pivot_task_start_time(self):
        if self.has_solution_sequence:
            return self.var_T_backward.x
            # return int((self.var_T_backward.x + self.var_T_forward.x)/2)
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def pivot_task_start_time_for_backward(self):
        if self.has_solution_sequence:
            return self.var_T_backward.x
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def pivot_task_start_time_for_forward(self):
        if self.has_solution_sequence:
            return self.var_T_forward.x
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def support_sequence(self) -> Sequence:
        return self.solution_sequence

    ######################
    # Decision variables #
    ######################

    def _add_decision_variables(self):
        self._add_decision_variables_T()
        self._add_decision_variables_split_T()
        self._add_decision_variables_U()
        self._GRB_model.update()

    def _add_decision_variables_T(self):
        self.vars_T = self._GRB_model.addVars(
            self.get_candidate_tasks_keys(including_pivot_task=False), vtype=GRB.INTEGER, lb=0, name="T"
        )

    def _add_decision_variables_split_T(self):
        self.var_T_backward = self._GRB_model.addVar(vtype=GRB.INTEGER, lb=0, name="Tb")
        self.var_T_forward = self._GRB_model.addVar(vtype=GRB.INTEGER, lb=0, name="Ta")

    ##################
    # Key quantities #
    ##################

    def _compute_time_gap_expression(self):
        self.time_gap_expression = self.var_T_backward - self.var_T_forward

    def _compute_tasks_performances_expressions(self):
        self.tasks_performances_expressions = dict([
            (j, grb.quicksum([self.vars_U[j, k]
                              for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                              if k != j]))
            for j in self.get_candidate_tasks_keys()
        ])

    def _compute_working_duration_expression(self):
        self.working_duration_expression = \
            grb.quicksum(
                [self.tasks_performances_expressions[j] * self.get_candidate_task_by_key(j).duration
                 for j in self.get_candidate_tasks_keys()]
            )

    def _compute_traveling_duration_expression(self):
        self.traveling_duration_expression = \
            grb.quicksum(
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
        self._compute_key_quantities()
        self._GRB_model.ModelSense = GRB.MINIMIZE
        objectives = [self.time_gap_expression, self.working_duration_expression, self.traveling_duration_expression]
        for index, objective in enumerate(objectives):
            self._GRB_model.setObjectiveN(objective, index, len(objectives) - 1 - index)
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
        # No skill constraints
        self._GRB_model.update()

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
            self._GRB_model.addLConstr(
                grb.quicksum(
                    [self.vars_U[(j, k)]
                     for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                     if k != j]
                ),
                sense=GRB.EQUAL, rhs=1,
                name=f"UnavailabilityCoveringConstraint[{j}]"
            )

    #############################
    # Constraints - Time window #
    #############################

    def _add_time_window_constraints(self):
        # Add time window lower bound constraint for pivot task
        j = self.get_pivot_task_key()
        self._GRB_model.addLConstr(
            self.var_T_backward - self.get_candidate_task_by_key(j).start_time_LB,
            sense=GRB.GREATER_EQUAL, rhs=0,
            name=f"TimeWindowLBConstraint[{j}]"
        )
        # Add time windows lower bounds constraints for all other tasks
        for j in self.get_candidate_tasks_keys(including_pivot_task=False):
            self._GRB_model.addLConstr(
                self.vars_T[j] - self.get_candidate_task_by_key(j).start_time_LB,
                sense=GRB.GREATER_EQUAL, rhs=0,
                name=f"TimeWindowLBConstraint[{j}]"
            )
        # Add time window upper bound constraint for pivot task
        j = self.get_pivot_task_key()
        self._GRB_model.addLConstr(
            self.var_T_forward + self.get_candidate_task_by_key(j).duration
            - self.get_candidate_task_by_key(j).end_time_UB,
            sense=GRB.LESS_EQUAL, rhs=0,
            name=f"TimeWindowUBConstraint[{j}]"
        )
        # Add time windows upper bounds constraints for all other tasks
        for j in self.get_candidate_tasks_keys(including_pivot_task=False):
            self._GRB_model.addLConstr(
                self.vars_T[j] + self.get_candidate_task_by_key(j).duration
                - self.get_candidate_task_by_key(j).end_time_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"TimeWindowUBConstraint[{j}]"
            )

    ################################
    # Constraints - Sequence times #
    ################################

    def _add_sequence_times_constraints(self):
        # Add departure-to-first-task time sequence constraints - for pivot task
        k = self.get_pivot_task_key()
        self._GRB_model.addLConstr(
            self.var_T_backward -
            (self.employee.start_time_LB + self.get_traveling_duration(LEAVING_HOME_KEY, k)) *
            self.vars_U[(LEAVING_HOME_KEY, k)],
            sense=GRB.GREATER_EQUAL, rhs=0,
            name=f"SequenceDepartureToTaskConstraint[{k}]"
        )
        # Add departure-to-first-task time sequence constraints - for all other tasks
        for k in self.get_candidate_tasks_keys(including_pivot_task=False):
            self._GRB_model.addLConstr(
                self.vars_T[k] -
                (self.employee.start_time_LB + self.get_traveling_duration(LEAVING_HOME_KEY, k)) *
                self.vars_U[(LEAVING_HOME_KEY, k)],
                sense=GRB.GREATER_EQUAL, rhs=0,
                name=f"SequenceDepartureToTaskConstraint[{k}]"
            )
        # Add last-task-to-comeback time sequence constraints - for pivot task
        j = self.get_pivot_task_key()
        self._GRB_model.addLConstr(
            self.var_T_forward + self.get_candidate_task_by_key(j).duration -
            self.vars_U[(j, COMING_BACK_HOME_KEY)] *
            (self.employee.end_time_UB - self.get_traveling_duration(j, COMING_BACK_HOME_KEY)) -
            (1 - self.vars_U[(j, COMING_BACK_HOME_KEY)]) * self.get_candidate_task_by_key(j).end_time_UB,
            sense=GRB.LESS_EQUAL, rhs=0,
            name=f"SequenceTaskToComebackConstraint[{j}]"
        )
        # Add last-task-to-comeback time sequence constraints - for all other tasks
        for j in self.get_candidate_tasks_keys(including_pivot_task=False):
            self._GRB_model.addLConstr(
                self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                self.vars_U[(j, COMING_BACK_HOME_KEY)] *
                (self.employee.end_time_UB - self.get_traveling_duration(j, COMING_BACK_HOME_KEY)) -
                (1 - self.vars_U[(j, COMING_BACK_HOME_KEY)]) * self.get_candidate_task_by_key(j).end_time_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"SequenceTaskToComebackConstraint[{j}]"
            )
        # Add task-to-task time sequence constraints
        for j in self.get_candidate_tasks_keys(including_pivot_task=False):
            # - with j and k prior tasks
            for k in self.get_candidate_tasks_keys(including_pivot_task=False):
                if k != j:
                    self._GRB_model.addLConstr(
                        self.vars_T[j] + self.get_candidate_task_by_key(j).duration +
                        self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                        self.vars_T[k] -
                        (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_UB,
                        sense=GRB.LESS_EQUAL, rhs=0,
                        name=f"SequenceTaskToTaskConstraint[{j, k}]"
                    )
            # - with j prior task and k pivot task
            k = self.get_pivot_task_key()
            self._GRB_model.addLConstr(
                self.vars_T[j] + self.get_candidate_task_by_key(j).duration +
                self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                self.var_T_backward -
                (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"SequenceTaskToTaskConstraint[{j, k}]"
            )
        # - with j pivot task and k other task
        j = self.get_pivot_task_key()
        for k in self.get_candidate_tasks_keys(including_pivot_task=False):
            self._GRB_model.addLConstr(
                self.var_T_forward + self.get_candidate_task_by_key(j).duration +
                self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                self.vars_T[k] -
                (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"SequenceTaskToTaskConstraint[{j, k}]"
            )
        # Add task-to-unavailability time sequence constraints - for pivot task
        j = self.get_pivot_task_key()
        for k in self.get_unavailabilities_keys():
            self._GRB_model.addLConstr(
                self.var_T_forward + self.get_candidate_task_by_key(j).duration +
                self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                self.get_unavailability_by_key(k).start_time_LB -
                (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"SequenceTaskToUnavailabilityConstraint[{j, k}]"
            )
        # Add task-to-unavailability time sequence constraints - for all other tasks
        for j in self.get_candidate_tasks_keys(including_pivot_task=False):
            for k in self.get_unavailabilities_keys():
                self._GRB_model.addLConstr(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration +
                    self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                    self.get_unavailability_by_key(k).start_time_LB -
                    (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_UB,
                    sense=GRB.LESS_EQUAL, rhs=0,
                    name=f"SequenceTaskToUnavailabilityConstraint[{j, k}]"
                )
        # Add unavailability-to-task time sequence constraints - for new task
        k = self.get_pivot_task_key()
        for j in self.get_unavailabilities_keys():
            self._GRB_model.addLConstr(
                self.get_unavailability_by_key(j).end_time_UB +
                self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                self.var_T_backward -
                (1 - self.vars_U[(j, k)]) * self.get_unavailability_by_key(j).end_time_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"SequenceUnavailabilityToTaskConstraint[{j, k}]"
            )
        # Add unavailability-to-task time sequence constraints - for all other tasks
        for j in self.get_unavailabilities_keys():
            for k in self.get_candidate_tasks_keys(including_pivot_task=False):
                self._GRB_model.addLConstr(
                    self.get_unavailability_by_key(j).end_time_UB +
                    self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                    self.vars_T[k] -
                    (1 - self.vars_U[(j, k)]) * self.get_unavailability_by_key(j).end_time_UB,
                    sense=GRB.LESS_EQUAL, rhs=0,
                    name=f"SequenceUnavailabilityToTaskConstraint[{j, k}]"
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

    ############################
    # Constraints - Split time #
    ############################

    def _add_split_time_constraint(self):
        self._GRB_model.addLConstr(
            self.var_T_backward - self.var_T_forward,
            sense=GRB.GREATER_EQUAL, rhs=0,
            name=f"TimeSplit[{self.get_pivot_task_key()}]"
        )
        self._GRB_model.update()

    ############
    # Solution #
    ############

    def _check_task_is_performed_by_key(self, task_key: str):
        return self.tasks_performances_expressions[task_key].getValue()

    def _extract_ordered_steps(self):
        start_times_and_steps = [
            (self.employee.start_time_LB,
             Step(activity=Departure(employee=self.employee), start_time=self.employee.start_time_LB)),
            (self.employee.end_time_UB,
             Step(activity=ComeBack(employee=self.employee), start_time=self.employee.end_time_UB))
        ]
        for j in self.get_candidate_tasks_keys(including_pivot_task=False):
            if self._check_task_is_performed_by_key(j):
                task = self.get_candidate_task_by_key(j)
                start_time = int(self.vars_T[j].x)
                start_times_and_steps.append((start_time, Step(activity=task, start_time=start_time)))
        j = self.get_pivot_task_key()
        task = self.get_candidate_task_by_key(j)
        start_time = self.var_T_backward.x
        start_times_and_steps.append((start_time, Step(activity=task, start_time=start_time)))
        for j in self.get_unavailabilities_keys():
            unavailability = self.get_unavailability_by_key(j)
            start_times_and_steps.append(
                (unavailability.start_time_LB, Step(activity=unavailability, start_time=unavailability.start_time_LB))
            )
        start_times_and_steps.sort()
        return [step for _, step in start_times_and_steps]
