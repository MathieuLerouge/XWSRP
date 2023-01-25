# Third-party libraries
import numpy as np
import gurobipy as grb
from gurobipy import GRB

# Local libraries
from src.modeling.activity import Activity
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.sequence import Sequence
from src.modeling.unavailability import Unavailability
from src.modeling.step import Step
from src.modeling.task import Task


# Global variables
LEAVING_HOME_KEY = 'DPT'
COMING_BACK_HOME_KEY = 'CBK'


# Function
def create_activity_key(activity: Activity):
    if isinstance(activity, Task) or isinstance(activity, Unavailability):
        return activity.name
    elif isinstance(activity, Departure):
        return LEAVING_HOME_KEY
    elif isinstance(activity, ComeBack):
        return COMING_BACK_HOME_KEY
    else:
        raise ValueError(f"The {activity} does not have any key.")


# Class IPModelForSequenceOptimization
class IPModelForSequenceOptimization:

    def __init__(self, instance: Instance, employee: Employee, candidate_tasks: list[Task]):
        self._instance = instance
        self._employee = employee
        self._candidate_activities = dict()
        departure = Departure(employee)
        self._candidate_activities[create_activity_key(departure)] = departure
        for task in candidate_tasks:
            self._candidate_activities[create_activity_key(task)] = task
        for unavailability in employee.unavailabilities:
            self._candidate_activities[create_activity_key(unavailability)] = unavailability
        comeback = ComeBack(employee)
        self._candidate_activities[create_activity_key(comeback)] = comeback
        self._candidate_tasks = dict([(create_activity_key(task), task) for task in candidate_tasks])
        self._GRB_model = grb.Model()
        self._decision_variables = dict()
        self._sequence_from_IP_solving = None
        self._add_decision_variables()
        self._add_objective_function()
        self._add_constraints()

    @property
    def instance(self):
        return self._instance

    @property
    def employee(self):
        return self._employee

    @property
    def candidate_tasks(self):
        return list(self._candidate_tasks.values())

    def get_activities_keys(self, including_departure: bool = True, including_comeback: bool = True,
                            including_unavailabilities: bool = True):
        activities_keys = list(self._candidate_activities.keys())
        if not including_departure:
            activities_keys.remove(LEAVING_HOME_KEY)
        if not including_comeback:
            activities_keys.remove(COMING_BACK_HOME_KEY)
        if not including_unavailabilities:
            for unavailability in self._employee.unavailabilities:
                activities_keys.remove(unavailability.name)
        return activities_keys

    def get_candidate_tasks_keys(self):
        return [task.name for task in self.candidate_tasks]

    def get_unavailabilities_keys(self):
        return [unavailability.name for unavailability in self._employee.unavailabilities]

    def get_candidate_task_by_key(self, task_key: str):
        return self._candidate_tasks[task_key]

    def get_unavailability_by_key(self, unavailability_key: str):
        return self._employee.get_unavailability_by_name(unavailability_key)

    @property
    def vars_T(self) -> grb.MVar:
        return self._decision_variables['T']

    @vars_T.setter
    def vars_T(self, T: grb.MVar):
        self._decision_variables['T'] = T

    @property
    def vars_U(self) -> grb.MVar:
        return self._decision_variables['U']

    @vars_U.setter
    def vars_U(self, U: grb.MVar):
        self._decision_variables['U'] = U

    @property
    def has_solution_sequence(self):
        return self._sequence_from_IP_solving is not None

    @property
    def solution_sequence(self) -> Sequence:
        if self.has_solution_sequence:
            return self._sequence_from_IP_solving
        else:
            raise AttributeError("There is no solution sequence stored")

    def get_traveling_duration(self, activity_key1, activity_key2):
        return self._instance.compute_traveling_duration(
            self._candidate_activities[activity_key1], self._candidate_activities[activity_key2]
        )

    ######################
    # Decision variables #
    ######################

    def _add_decision_variables_T(self):
        self.vars_T = self._GRB_model.addVars(
            self.get_candidate_tasks_keys(),
            vtype=GRB.INTEGER, lb=0, name="T"
        )

    def _add_decision_variables_U(self):
        self.vars_U = self._GRB_model.addVars(
            [(j, k)
             for j in self.get_activities_keys(including_departure=True, including_comeback=False)
             for k in self.get_activities_keys(including_departure=False, including_comeback=True) if k != j],
            vtype=GRB.BINARY, name="U"
        )

    def _add_decision_variables(self):
        self._add_decision_variables_T()
        self._add_decision_variables_U()

    ######################
    # Objective function #
    ######################

    def _add_objective_function(self):

        # Define the total-working-duration expression
        working_duration_expression = grb.LinExpr()
        working_duration_expression.add(
            grb.quicksum([self.vars_U[j, k] * self.get_candidate_task_by_key(j).duration
                          for j in self.get_candidate_tasks_keys()
                          for k in self.get_activities_keys(including_departure=False) if k != j])
        )

        # Define the total-traveling-duration expression
        traveling_duration_expression = grb.LinExpr()
        traveling_duration_expression.add(
            grb.quicksum([self.vars_U[indices] *
                          self.get_traveling_duration(activity_key1=indices[0], activity_key2=indices[1])
                          for indices in self.vars_U.keys()])
        )

        # Set objective function expression as a weighted sum of the sub-objective functions
        self.weight_traveling_duration = 1
        self.weight_working_duration = 100
        OF_expression = grb.LinExpr()
        OF_expression += self.weight_working_duration*working_duration_expression
        OF_expression += -self.weight_traveling_duration*traveling_duration_expression
        self._GRB_model.setObjective(OF_expression, sense=GRB.MAXIMIZE)

        # Set objective function expression as a multi-objective function
        # self._GRB_model.ModelSense = GRB.MAXIMIZE
        # self._GRB_model.setObjectiveN(working_duration_expression, 0)
        # self._GRB_model.setObjectiveN(-traveling_duration_expression, 1)

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
        # No skill constraints

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_covering_constraints(self):

        # Add constraints about candidate tasks covering
        for j in self.get_candidate_tasks_keys():
            self._GRB_model.addLConstr(
                grb.quicksum([self.vars_U[(j, k)]
                              for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                              if k != j]),
                sense=GRB.LESS_EQUAL, rhs=1,
                name=f"TaskCoveringConstraint[{j}]"
            )

        # Add constraints about unavailabilities covering
        for j in self.get_unavailabilities_keys():
            self._GRB_model.addLConstr(
                grb.quicksum([self.vars_U[(j, k)]
                              for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                              if k != j]),
                sense=GRB.EQUAL, rhs=1,
                name=f"UnavailabilityCoveringConstraint[{j}]"
            )

        self._GRB_model.update()

    ######################
    # Constraints - Flow #
    ######################

    def _add_flow_constraints(self):

        # Add flow constraint about departure
        self._GRB_model.addLConstr(
            grb.quicksum([self.vars_U[(LEAVING_HOME_KEY, k)]
                          for k in self.get_activities_keys(including_departure=False, including_comeback=True)]),
            sense=GRB.EQUAL, rhs=1,
            name=f"FlowConstraint[{LEAVING_HOME_KEY}]"
        )

        # Add flow constraint about comeback
        self._GRB_model.addLConstr(
            grb.quicksum([self.vars_U[(j, COMING_BACK_HOME_KEY)]
                          for j in self.get_activities_keys(including_departure=True, including_comeback=False)]),
            sense=GRB.EQUAL, rhs=1,
            name=f"FlowConstraint[{COMING_BACK_HOME_KEY}]"
        )

        # Add flow constraints at other activities
        for k in self.get_activities_keys(including_departure=False, including_comeback=False):
            self._GRB_model.addLConstr(
                grb.quicksum(
                    [self.vars_U[(j, k)]
                     for j in self.get_activities_keys(including_departure=True, including_comeback=False)
                     if j != k]
                )
                - grb.quicksum(
                    [self.vars_U[(k, j)]
                     for j in self.get_activities_keys(including_departure=False, including_comeback=True)
                     if j != k]
                ),
                sense=GRB.EQUAL, rhs=0,
                name=f"FlowConstraint[{k}]"
            )

        self._GRB_model.update()

    #############################
    # Constraints - Time window #
    #############################

    def _add_time_window_constraints(self):

        # Add time windows lower bound constraints
        for j in self.get_candidate_tasks_keys():
            self._GRB_model.addLConstr(
                self.vars_T[j]
                - grb.quicksum(
                    [self.vars_U[(j, k)]
                     for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                     if k != j]
                ) * self.get_candidate_task_by_key(j).start_time_LB,
                sense=GRB.GREATER_EQUAL, rhs=0,
                name=f"TimeWindowLBConstraint[{j}]"
            )

        # Add time windows upper bound constraints
        for j in self.get_candidate_tasks_keys():
            self._GRB_model.addLConstr(
                self.vars_T[j]
                - grb.quicksum(
                    [self.vars_U[(j, k)]
                     for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                     if k != j]
                ) * (self.get_candidate_task_by_key(j).end_time_UB - self.get_candidate_task_by_key(j).duration),
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"TimeWindowUBConstraint[{j}]"
            )

        self._GRB_model.update()

    ################################
    # Constraints - Sequence times #
    ################################

    def _add_sequence_times_constraints(self):

        # Add departure-to-first-task time sequence constraints
        for k in self.get_candidate_tasks_keys():
            self._GRB_model.addLConstr(
                self.vars_T[k] -
                (self.employee.start_time_LB + self.get_traveling_duration(LEAVING_HOME_KEY, k)) *
                self.vars_U[(LEAVING_HOME_KEY, k)],
                sense=GRB.GREATER_EQUAL, rhs=0,
                name=f"SequenceDepartureToTaskConstraint[{k}]"
            )

        # Add last-task-to-comeback time sequence constraint
        for j in self.get_candidate_tasks_keys():
            self._GRB_model.addLConstr(
                self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                self.vars_U[(j, COMING_BACK_HOME_KEY)] *
                (self.employee.end_time_UB - self.get_traveling_duration(j, COMING_BACK_HOME_KEY)) -
                (1 - self.vars_U[(j, COMING_BACK_HOME_KEY)]) * self.get_candidate_task_by_key(j).end_time_UB,
                sense=GRB.LESS_EQUAL, rhs=0,
                name=f"SequenceTaskToComebackConstraint[{j}]"
            )

        # Add task-to-task time sequence constraint
        for j in self.get_candidate_tasks_keys():
            for k in self.get_candidate_tasks_keys():
                if k != j:
                    self._GRB_model.addLConstr(
                        self.vars_T[j] + self.get_candidate_task_by_key(j).duration +
                        self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                        self.vars_T[k] -
                        (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_UB,
                        sense=GRB.LESS_EQUAL, rhs=0,
                        name=f"SequenceTaskToTaskConstraint[{j, k}]"
                    )

        # Add task-to-unavailability time sequence constraint
        for j in self.get_candidate_tasks_keys():
            for k in self.get_unavailabilities_keys():
                self._GRB_model.addLConstr(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration +
                    self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                    self.get_unavailability_by_key(k).start_time_LB -
                    (1 - self.vars_U[(j, k)]) * self.get_candidate_task_by_key(j).end_time_UB,
                    sense=GRB.LESS_EQUAL, rhs=0,
                    name=f"SequenceTaskToUnavailabilityConstraint[{j, k}]"
                )

        # Add unavailability-to-task time sequence constraint
        for j in self.get_unavailabilities_keys():
            for k in self.get_candidate_tasks_keys():
                self._GRB_model.addLConstr(
                    self.get_unavailability_by_key(j).end_time_UB +
                    self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                    self.vars_T[k] -
                    (1 - self.vars_U[(j, k)]) * self.get_unavailability_by_key(j).end_time_UB,
                    sense=GRB.LESS_EQUAL, rhs=0,
                    name=f"SequenceUnavailabilityToTaskConstraint[{j, k}]"
                )

        # Add unavailability-to-unavailability time sequence constraint
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

    ################
    # Optimization #
    ################

    def optimize(self, mute=True):
        if mute:
            self._GRB_model.params.outputflag = 0
        self._GRB_model.optimize()
        if self._GRB_model.Status == GRB.INFEASIBLE:
            print("IP model is infeasible")
            print("")
        elif self._GRB_model.Status == GRB.UNBOUNDED:
            print("IP model is unbounded")
            print("")
        else:
            if self._GRB_model.Status == GRB.TIME_LIMIT:
                print("IP model solving was stopped as it reached given time limit")
                if self._GRB_model.SolCount > 0:
                    print(f"but {self._GRB_model.SolCount} solutions were found")
                    self._extract_data_from_IP_solving()
                else:
                    print(f"and no solutions were found")
                print("")
            else:
                self._extract_data_from_IP_solving()

    ###################################
    # Data extraction from IP solving #
    ###################################

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
        for j in self.get_candidate_tasks_keys():
            if int(np.sum(
                [self.vars_U[j, k].x
                 for k in self.get_activities_keys(including_departure=False, including_comeback=True) if k != j]
            )) == 1:
                task = self.get_candidate_task_by_key(j)
                start_time = int(self.vars_T[j].x)
                start_times_and_steps.append((start_time, Step(activity=task, start_time=start_time)))
        for j in self.get_unavailabilities_keys():
            unavailability = self.get_unavailability_by_key(j)
            start_times_and_steps.append(
                (unavailability.start_time_LB, Step(activity=unavailability, start_time=unavailability.start_time_LB))
            )
        start_times_and_steps.sort()
        _, first_step = start_times_and_steps[0]
        if not isinstance(first_step.activity, Departure):
            raise Exception(f"The first activity of the sequence is not a departure but {first_step}")
        _, last_step = start_times_and_steps[-1]
        if not isinstance(last_step.activity, ComeBack):
            raise Exception(f"The last activity of the sequence is not a comeback but {last_step}")
        return [step for _, step in start_times_and_steps]

    def _extract_sequence_from_IP_solving(self):
        steps = self._extract_ordered_steps()
        sequence = Sequence(self.instance, self.employee, steps)
        sequence.compute_times_based_on_fixed_start_times()
        self._sequence_from_IP_solving = sequence

    def _extract_data_from_IP_solving(self):
        self._extract_sequence_from_IP_solving()
