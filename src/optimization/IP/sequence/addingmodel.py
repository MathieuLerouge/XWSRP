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


# Class IPModelForSequenceAdding
class IPModelForSequenceAdding(IPModelForSequenceOptimization):

    def __init__(self, sequence: Sequence, new_task: Task):
        candidate_tasks = sequence.get_contained_tasks() + [new_task]
        self._new_task = new_task
        super().__init__(sequence.instance, sequence.employee, candidate_tasks)

    @property
    def new_task(self):
        return self._new_task

    def get_candidate_tasks_keys(self, including_new_task: bool = True):
        if including_new_task:
            return [task.name for task in self.candidate_tasks]
        else:
            return [task.name for task in self.candidate_tasks if task != self._new_task]

    def get_new_task_key(self):
        return self._new_task.name

    @property
    def new_task_time_gap(self):
        if self.has_solution_sequence:
            return self.var_T_backward.x - self.var_T_forward.x
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def new_task_start_time(self):
        if self.has_solution_sequence:
            return self.var_T_backward.x
            # return int((self.var_T_backward.x + self.var_T_forward.x)/2)
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def new_task_start_time_for_backward(self):
        if self.has_solution_sequence:
            return self.var_T_backward.x
        else:
            raise AttributeError("There is no solution sequence stored")

    @property
    def new_task_start_time_for_forward(self):
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

    def _add_decision_variables_T(self):
        self.vars_T = self._GRB_model.addVars(
            self.get_candidate_tasks_keys(including_new_task=False),
            vtype=GRB.INTEGER, lb=0, name="T"
        )

    def _add_decision_variables_split_T(self):
        self.var_T_backward = self._GRB_model.addVar(
            vtype=GRB.INTEGER, lb=0, name="Tb"
        )
        self.var_T_forward = self._GRB_model.addVar(
            vtype=GRB.INTEGER, lb=0, name="Ta"
        )

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
        traveling_duration_expression = grb.LinExpr()
        traveling_duration_expression.add(
            grb.quicksum(
                [self.vars_U[indices] *
                 self.get_traveling_duration(activity_key1=indices[0], activity_key2=indices[1])
                 for indices in self.vars_U.keys()]
            )
        )

        # Set objective function expression as a weighted sum of the sub-objective functions
        self.weight_time_gap = 1000
        self.weight_traveling_duration = 1
        OF_expression = grb.LinExpr()
        OF_expression += self.weight_time_gap * time_gap_expression
        OF_expression += self.weight_traveling_duration * traveling_duration_expression
        self._GRB_model.setObjective(OF_expression, sense=GRB.MINIMIZE)

        # Set objective function expression as a multi-objective function
        # self._GRB_model.ModelSense = GRB.MINIMIZE
        # self._GRB_model.setObjectiveN(time_gap_expression, 0)
        # self._GRB_model.setObjectiveN(traveling_duration_expression, 1)

        # Update GRB model
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

        # Add time windows lower bounds constraints for prior tasks
        for j in self.get_candidate_tasks_keys(including_new_task=False):
            self._GRB_model.addLConstr(
                self.vars_T[j] - self.get_candidate_task_by_key(j).start_time_LB,
                sense=GRB.GREATER_EQUAL, rhs=0,
                name=f"TimeWindowLBConstraint[{j}]"
            )

        # Add time window lower bound constraint for new task
        j = self.get_new_task_key()
        self._GRB_model.addLConstr(
            self.var_T_backward - self.get_candidate_task_by_key(j).start_time_LB,
            sense=GRB.GREATER_EQUAL, rhs=0,
            name=f"TimeWindowLBConstraint[{j}]"
        )

        # Add time windows upper bounds constraints for prior tasks
        for j in self.get_candidate_tasks_keys(including_new_task=False):
            self._GRB_model.addLConstr(
                self.vars_T[j] + self.get_candidate_task_by_key(j).duration
                - self.get_candidate_task_by_key(j).end_time_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"TimeWindowUBConstraint[{j}]"
            )

        # Add time window upper bound constraint for new task
        j = self.get_new_task_key()
        self._GRB_model.addLConstr(
            self.var_T_forward + self.get_candidate_task_by_key(j).duration
            - self.get_candidate_task_by_key(j).end_time_UB,
            sense=GRB.LESS_EQUAL, rhs=0,
            name=f"TimeWindowUBConstraint[{j}]"
        )

        self._GRB_model.update()

    ################################
    # Constraints - Sequence times #
    ################################

    def _add_sequence_times_constraints(self):

        # Add departure-to-first-task time sequence constraints
        # - for prior tasks
        for k in self.get_candidate_tasks_keys(including_new_task=False):
            self._GRB_model.addLConstr(
                self.vars_T[k] -
                (self.employee.start_time_LB + self.get_traveling_duration(LEAVING_HOME_KEY, k)) *
                self.vars_U[(LEAVING_HOME_KEY, k)],
                sense=GRB.GREATER_EQUAL, rhs=0,
                name=f"SequenceDepartureToTaskConstraint[{k}]"
            )
        # - for new task
        k = self.get_new_task_key()
        self._GRB_model.addLConstr(
            self.var_T_backward -
            (self.employee.start_time_LB + self.get_traveling_duration(LEAVING_HOME_KEY, k)) *
            self.vars_U[(LEAVING_HOME_KEY, k)],
            sense=GRB.GREATER_EQUAL, rhs=0,
            name=f"SequenceDepartureToTaskConstraint[{k}]"
        )

        # Add last-task-to-comeback time sequence constraints
        # - for prior tasks
        for j in self.get_candidate_tasks_keys(including_new_task=False):
            self._GRB_model.addLConstr(
                self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                self.vars_U[(j, COMING_BACK_HOME_KEY)] *
                (self.employee.end_time_UB - self.get_traveling_duration(j, COMING_BACK_HOME_KEY)) -
                (1 - self.vars_U[(j, COMING_BACK_HOME_KEY)]) * self.get_candidate_task_by_key(j).end_time_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"SequenceTaskToComebackConstraint[{j}]"
            )
        # - for new task
        j = self.get_new_task_key()
        self._GRB_model.addLConstr(
            self.var_T_forward + self.get_candidate_task_by_key(j).duration -
            self.vars_U[(j, COMING_BACK_HOME_KEY)] *
            (self.employee.end_time_UB - self.get_traveling_duration(j, COMING_BACK_HOME_KEY)) -
            (1 - self.vars_U[(j, COMING_BACK_HOME_KEY)]) * self.get_candidate_task_by_key(j).end_time_UB,
            sense=GRB.LESS_EQUAL, rhs=0,
            name=f"SequenceTaskToComebackConstraint[{j}]"
        )

        # Add task-to-task time sequence constraints
        for j in self.get_candidate_tasks_keys(including_new_task=False):
            # - with j and k prior tasks
            for k in self.get_candidate_tasks_keys(including_new_task=False):
                if k != j:
                    self._GRB_model.addLConstr(
                        self.vars_T[j] + self.get_candidate_task_by_key(j).duration +
                        self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                        self.vars_T[k] -
                        (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_UB,
                        sense=GRB.LESS_EQUAL, rhs=0,
                        name=f"SequenceTaskToTaskConstraint[{j, k}]"
                    )
            # - with j prior task and k new task
            k = self.get_new_task_key()
            self._GRB_model.addLConstr(
                self.vars_T[j] + self.get_candidate_task_by_key(j).duration +
                self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                self.var_T_backward -
                (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"SequenceTaskToTaskConstraint[{j, k}]"
            )
        # - with j new task and k prior task
        j = self.get_new_task_key()
        for k in self.get_candidate_tasks_keys(including_new_task=False):
            self._GRB_model.addLConstr(
                self.var_T_forward + self.get_candidate_task_by_key(j).duration +
                self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                self.vars_T[k] -
                (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"SequenceTaskToTaskConstraint[{j, k}]"
            )

        # Add task-to-unavailability time sequence constraints
        # - for prior tasks
        for j in self.get_candidate_tasks_keys(including_new_task=False):
            for k in self.get_unavailabilities_keys():
                self._GRB_model.addLConstr(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration +
                    self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                    self.get_unavailability_by_key(k).start_time_LB -
                    (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_UB,
                    sense=GRB.LESS_EQUAL, rhs=0,
                    name=f"SequenceTaskToUnavailabilityConstraint[{j, k}]"
                )
        # - for new task
        j = self.get_new_task_key()
        for k in self.get_unavailabilities_keys():
            self._GRB_model.addLConstr(
                self.var_T_forward + self.get_candidate_task_by_key(j).duration +
                self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                self.get_unavailability_by_key(k).start_time_LB -
                (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"SequenceTaskToUnavailabilityConstraint[{j, k}]"
            )

        # Add unavailability-to-task time sequence constraints
        # - for old tasks
        for j in self.get_unavailabilities_keys():
            for k in self.get_candidate_tasks_keys(including_new_task=False):
                self._GRB_model.addLConstr(
                    self.get_unavailability_by_key(j).end_time_UB +
                    self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                    self.vars_T[k] -
                    (1 - self.vars_U[(j, k)]) * self.get_unavailability_by_key(j).end_time_UB,
                    sense=GRB.LESS_EQUAL, rhs=0,
                    name=f"SequenceUnavailabilityToTaskConstraint[{j, k}]"
                )
        # - for new task
        k = self.get_new_task_key()
        for j in self.get_unavailabilities_keys():
            self._GRB_model.addLConstr(
                self.get_unavailability_by_key(j).end_time_UB +
                self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                self.var_T_backward -
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

        self._GRB_model.update()

    ############################
    # Constraints - Split time #
    ############################

    def _add_split_time_constraint(self):
        self._GRB_model.addLConstr(
            self.var_T_backward - self.var_T_forward,
            sense=GRB.GREATER_EQUAL, rhs=0,
            name=f"TimeSplit[{self.get_new_task_key()}]"
        )
        self._GRB_model.update()

    ############
    # Solution #
    ############

    def _extract_ordered_steps(self):
        start_times_and_steps = [
            (
                self.employee.start_time_LB,
                Step(activity=Departure(employee=self.employee), start_time=self.employee.start_time_LB)
            ), (
                self.employee.end_time_UB,
                Step(activity=ComeBack(employee=self.employee), start_time=self.employee.end_time_UB)
            )
        ]
        for j in self.get_candidate_tasks_keys(including_new_task=False):
            task = self.get_candidate_task_by_key(j)
            start_time = int(self.vars_T[j].x)
            start_times_and_steps.append((start_time, Step(activity=task, start_time=start_time)))
        j = self.get_new_task_key()
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
