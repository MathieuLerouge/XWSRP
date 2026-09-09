# Standard library
from typing import Optional

# Third-party libraries
import numpy as np
import pyomo.environ as pyo

# Local libraries
from main_configuration import SOLVER_NAME
from src.modeling.activity import Activity
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.sequence import Sequence
from src.modeling.step import Step
from src.modeling.task import Task
from src.modeling.unavailability import Unavailability
from src.optimization.milp.solver.exceptions import TimeLimitReachedWithSolutionException, \
    TimeLimitReachedWithoutSolutionException
from src.optimization.milp.solver.outcome import Outcome
from src.optimization.milp.solver.solver import Solver


# Global variables
LEAVING_HOME_KEY = 'DPT'
COMING_BACK_HOME_KEY = 'CBK'


####################
# Global functions #
####################

def create_activity_key(activity: Activity):
    """
    Return the key identifying the given activity among a SequenceModel's candidate activities:
    a task's or unavailability's name, or one of the fixed LEAVING_HOME_KEY/COMING_BACK_HOME_KEY
    constants for a departure/comeback.

    Args:
        activity: the activity to build a key for.

    Raises:
        ValueError: if the given activity is not a Task, Unavailability, Departure or ComeBack.
    """
    if isinstance(activity, Task) or isinstance(activity, Unavailability):
        return activity.name
    elif isinstance(activity, Departure):
        return LEAVING_HOME_KEY
    elif isinstance(activity, ComeBack):
        return COMING_BACK_HOME_KEY
    else:
        raise ValueError(f"The {activity} does not have any key.")


#################
# SequenceModel #
#################

class SequenceModel:
    """
    Base MILP model optimizing a single employee's sequence: deciding which of a list of candidate
    tasks that employee performs, and in what order, maximizing working duration net of traveling
    duration.
    """

    def __init__(self, instance: Instance, employee: Employee, candidate_tasks: list[Task]):
        """
        Args:
            instance: the instance the employee belongs to.
            employee: the employee for which the sequence is optimized.
            candidate_tasks: the tasks that can be part of the employee's sequence.
        """
        self._instance = instance
        self._employee = employee
        self._candidate_activities: dict[str, Activity] = dict()
        departure = Departure(employee)
        self._candidate_activities[create_activity_key(departure)] = departure
        for task in candidate_tasks:
            self._candidate_activities[create_activity_key(task)] = task
        for unavailability in employee.unavailabilities:
            self._candidate_activities[create_activity_key(unavailability)] = unavailability
        comeback = ComeBack(employee)
        self._candidate_activities[create_activity_key(comeback)] = comeback
        self._candidate_tasks: dict[str, Task] = dict(
            [(create_activity_key(task), task) for task in candidate_tasks]
        )
        self._model = pyo.ConcreteModel()
        self._decision_variables: dict[str, pyo.Var] = dict()
        self._solving_time_limit: Optional[int] = None
        self._sequence_from_IP_solving: Optional[Sequence] = None
        self._solve_outcome: Optional[Outcome] = None
        self._add_decision_variables()
        self._add_objective_function()
        self._add_constraints()

    @property
    def instance(self):
        """The instance the employee belongs to."""
        return self._instance

    @property
    def employee(self):
        """The employee for which the sequence is optimized."""
        return self._employee

    def get_activities_keys(self, including_departure: bool = True, including_comeback: bool = True,
                            including_unavailabilities: bool = True):
        """
        Return the keys of the employee's candidate activities (departure, candidate tasks,
        unavailabilities, comeback), optionally excluding some of them.

        Args:
            including_departure: if True, include the departure's key (LEAVING_HOME_KEY).
            including_comeback: if True, include the comeback's key (COMING_BACK_HOME_KEY).
            including_unavailabilities: if True, include the employee's unavailabilities' keys.

        Returns:
            the list of candidate activities' keys.
        """
        activities_keys = list(self._candidate_activities.keys())
        if not including_departure:
            activities_keys.remove(LEAVING_HOME_KEY)
        if not including_comeback:
            activities_keys.remove(COMING_BACK_HOME_KEY)
        if not including_unavailabilities:
            for unavailability in self._employee.unavailabilities:
                activities_keys.remove(unavailability.name)
        return activities_keys

    @property
    def candidate_tasks(self):
        """The candidate tasks, i.e. the tasks that can be part of the employee's sequence."""
        return list(self._candidate_tasks.values())

    @property
    def candidate_tasks_keys(self):
        """The keys of the candidate tasks, i.e. the tasks that can be part of the employee's sequence."""
        return [task.name for task in self.candidate_tasks]

    def _get_candidate_tasks_keys(self):
        """
        Return the keys of the candidate tasks to build decision variables/constraints for.

        Hook for subclasses that need to restrict or extend this set (e.g. to exclude a task being
        inserted, whose key is handled separately); the base implementation just returns
        candidate_tasks_keys.
        """
        return self.candidate_tasks_keys

    def get_candidate_task_by_key(self, task_key: str):
        """Return the candidate task corresponding to the given key."""
        return self._candidate_tasks[task_key]

    def get_unavailabilities_keys(self):
        """Return the keys of the employee's unavailabilities."""
        return [unavailability.name for unavailability in self._employee.unavailabilities]

    def get_unavailability_by_key(self, unavailability_key: str):
        """Return the employee's unavailability corresponding to the given key."""
        return self._employee.get_unavailability_by_name(unavailability_key)

    @property
    def vars_T(self) -> pyo.Var:
        """The T decision variables: each candidate task's performance start time."""
        return self._decision_variables['T']

    @vars_T.setter
    def vars_T(self, T: pyo.Var):
        self._decision_variables['T'] = T

    @property
    def vars_U(self) -> pyo.Var:
        """The U decision variables: whether each pair of candidate activities is a sequence arc."""
        return self._decision_variables['U']

    @vars_U.setter
    def vars_U(self, U: pyo.Var):
        self._decision_variables['U'] = U

    @property
    def has_solution_sequence(self):
        """Whether a solution sequence has been extracted."""
        return self._sequence_from_IP_solving is not None

    @property
    def solution_sequence(self) -> Sequence:
        """
        The sequence extracted from the last solve() call.

        Raises:
            AttributeError: if solve() hasn't been called yet, or found no feasible solution.
        """
        if self.has_solution_sequence:
            return self._sequence_from_IP_solving
        else:
            raise AttributeError("There is no solution sequence stored")

    def get_traveling_duration(self, activity_key1, activity_key2):
        """Return the employee's traveling duration between the two given candidate activities."""
        return self._instance.compute_traveling_duration(
            self._candidate_activities[activity_key1], self._candidate_activities[activity_key2]
        )

    ######################
    # Decision variables #
    ######################

    def _add_decision_variables_T(self):
        self._model.T = pyo.Var(self._get_candidate_tasks_keys(), domain=pyo.NonNegativeIntegers)
        self.vars_T = self._model.T

    def _add_decision_variables_U(self):
        self._model.U = pyo.Var(
            [(j, k)
             for j in self.get_activities_keys(including_departure=True, including_comeback=False)
             for k in self.get_activities_keys(including_departure=False, including_comeback=True) if k != j],
            domain=pyo.Binary
        )
        self.vars_U = self._model.U

    def _add_decision_variables(self):
        self._add_decision_variables_T()
        self._add_decision_variables_U()

    ######################
    # Objective function #
    ######################

    def _add_objective_function(self):

        # Define the total-working-duration expression
        working_duration_expression = pyo.quicksum([
            self.vars_U[j, k] * self.get_candidate_task_by_key(j).duration
            for j in self._get_candidate_tasks_keys()
            for k in self.get_activities_keys(including_departure=False) if k != j
        ])

        # Define the total-traveling-duration expression
        traveling_duration_expression = pyo.quicksum([
            self.vars_U[indices] *
            self.get_traveling_duration(activity_key1=indices[0], activity_key2=indices[1])
            for indices in self.vars_U.keys()
        ])

        # Set objective function expression as a weighted sum of the sub-objective functions
        self.weight_traveling_duration = 1
        self.weight_working_duration = 100
        objective_expression = (self.weight_working_duration * working_duration_expression -
                                self.weight_traveling_duration * traveling_duration_expression)
        self._model.objective = pyo.Objective(expr=objective_expression, sense=pyo.maximize)

    ###############
    # Constraints #
    ###############

    def _add_constraints(self):
        """
        Add all constraints to the model: covering, flow, time-window and sequence-times constraints
        (no skill constraints).
        """
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
        for j in self._get_candidate_tasks_keys():
            self._model.add_component(
                f"TaskCoveringConstraint[{j}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([
                        self.vars_U[(j, k)]
                        for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                        if k != j
                    ]) <= 1
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

    ######################
    # Constraints - Flow #
    ######################

    def _add_flow_constraints(self):
        # Add flow constraint about departure
        self._model.add_component(
            f"FlowConstraint[{LEAVING_HOME_KEY}]",
            pyo.Constraint(expr=(
                pyo.quicksum([
                    self.vars_U[(LEAVING_HOME_KEY, k)]
                    for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                ]) == 1
            ))
        )
        # Add flow constraint about comeback
        self._model.add_component(
            f"FlowConstraint[{COMING_BACK_HOME_KEY}]",
            pyo.Constraint(expr=(
                pyo.quicksum([
                    self.vars_U[(j, COMING_BACK_HOME_KEY)]
                    for j in self.get_activities_keys(including_departure=True, including_comeback=False)
                ]) == 1
            ))
        )
        # Add flow constraints at other activities
        for k in self.get_activities_keys(including_departure=False, including_comeback=False):
            self._model.add_component(
                f"FlowConstraint[{k}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([
                        self.vars_U[(j, k)]
                        for j in self.get_activities_keys(including_departure=True, including_comeback=False)
                        if j != k
                    ]) -
                    pyo.quicksum([
                        self.vars_U[(k, j)]
                        for j in self.get_activities_keys(including_departure=False, including_comeback=True)
                        if j != k
                    ]) == 0
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
                    self.vars_T[j]
                    - pyo.quicksum([
                        self.vars_U[(j, k)]
                        for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                        if k != j
                    ]) * self.get_candidate_task_by_key(j).start_time_lb >= 0
                ))
            )
        # Add time windows upper bound constraints
        for j in self._get_candidate_tasks_keys():
            self._model.add_component(
                f"TimeWindowUBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] -
                    pyo.quicksum([
                        self.vars_U[(j, k)]
                        for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                        if k != j
                    ]) * (self.get_candidate_task_by_key(j).end_time_ub - self.get_candidate_task_by_key(j).duration)
                    <= 0
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
                    self.vars_T[k] -
                    (self.employee.start_time_lb + self.get_traveling_duration(LEAVING_HOME_KEY, k)) *
                    self.vars_U[(LEAVING_HOME_KEY, k)] >= 0
                ))
            )

        # Add last-task-to-comeback time sequence constraint
        for j in self._get_candidate_tasks_keys():
            self._model.add_component(
                f"SequenceTaskToComebackConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                    self.vars_U[(j, COMING_BACK_HOME_KEY)] *
                    (self.employee.end_time_ub - self.get_traveling_duration(j, COMING_BACK_HOME_KEY)) -
                    (1 - self.vars_U[(j, COMING_BACK_HOME_KEY)]) * self.get_candidate_task_by_key(j).end_time_ub <= 0
                ))
            )

        # Add task-to-task time sequence constraint
        for j in self._get_candidate_tasks_keys():
            for k in self._get_candidate_tasks_keys():
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

        # Add task-to-unavailability time sequence constraint
        for j in self._get_candidate_tasks_keys():
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

        # Add unavailability-to-task time sequence constraint
        for j in self.get_unavailabilities_keys():
            for k in self._get_candidate_tasks_keys():
                self._model.add_component(
                    f"SequenceUnavailabilityToTaskConstraint[{j, k}]",
                    pyo.Constraint(expr=(
                        self.get_unavailability_by_key(j).end_time_ub +
                        self.vars_U[(j, k)] * self.get_traveling_duration(j, k) -
                        self.vars_T[k] -
                        (1 - self.vars_U[(j, k)]) * self.get_unavailability_by_key(j).end_time_ub <= 0
                    ))
                )

        # Add unavailability-to-unavailability time sequence constraint
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

    ###########
    # Solving #
    ###########

    @property
    def solving_time_limit(self):
        """Solving time limit in seconds, or None for no limit."""
        return self._solving_time_limit

    @solving_time_limit.setter
    def solving_time_limit(self, solving_time_limit: int):
        """
        Set solving time limit.

        Args:
            solving_time_limit: solving time limit in seconds.
        """
        self._solving_time_limit = solving_time_limit

    def solve(self, mute=True, solver_name: str = SOLVER_NAME) -> Outcome:
        """
        Solve the model with the configured MILP backend.

        Whether a plain failure (infeasible/unbounded) is worth raising as an exception is left to
        the caller to decide, via OutcomeToExceptionMapper, since this model isn't in a position to
        know whether that's exceptional for its particular caller.

        Args:
            mute: if True, suppress the solver's own console output.
            solver_name: which MILP backend to use (SOLVER_HIGHS or SOLVER_GUROBI from
                src.optimization.milp.solver.solver), defaults to main_configuration.SOLVER_NAME.

        Returns:
            the Outcome describing the solving, with its solution set if a feasible solution
            (an incumbent) was found.

        Raises:
            TimeLimitReachedWithSolutionException: if the time limit is reached with a feasible solution found.
            TimeLimitReachedWithoutSolutionException: if the time limit is reached with no feasible solution found.
        """
        self._solve_outcome = self._solve(mute=mute, solver_name=solver_name)
        if self._solve_outcome.has_incumbent:
            self._extract_data_from_IP_solving()
            self._solve_outcome.solution = self.solution_sequence
        if self._solve_outcome.is_time_limit:
            if self._solve_outcome.has_incumbent:
                raise TimeLimitReachedWithSolutionException(self._solve_outcome)
            else:
                raise TimeLimitReachedWithoutSolutionException()
        return self._solve_outcome

    def _solve(self, mute: bool, solver_name: str):
        """
        Run the solver against the model and return its normalized outcome.

        Subclasses whose objective function is a lexicographic priority list (built via
        Solver.solve_lexicographically instead of a single pyo.Objective) override this method
        to call that instead.
        """
        solver = Solver(solver_name, mute=mute, time_limit=self._solving_time_limit)
        return solver.solve(self._model)

    ###########
    # Results #
    ###########

    def _extract_ordered_steps(self):
        """
        Build the ordered list of Steps making up the solution sequence, from decision variable values.

        Raises:
            Exception: if the extracted order doesn't start with a departure or end with a comeback.
        """
        start_times_and_steps = [
            (
                self.employee.start_time_lb,
                Step(activity=Departure(employee=self.employee), start_time=self.employee.start_time_lb)
            ), (
                self.employee.end_time_ub,
                Step(activity=ComeBack(employee=self.employee), start_time=self.employee.end_time_ub)
            )
        ]
        for j in self._get_candidate_tasks_keys():
            if round(np.sum(
                [pyo.value(self.vars_U[j, k])
                 for k in self.get_activities_keys(including_departure=False, including_comeback=True) if k != j]
            )) == 1:
                task = self.get_candidate_task_by_key(j)
                start_time = round(pyo.value(self.vars_T[j]))
                start_times_and_steps.append((start_time, Step(activity=task, start_time=start_time)))
        for j in self.get_unavailabilities_keys():
            unavailability = self.get_unavailability_by_key(j)
            start_times_and_steps.append(
                (unavailability.start_time_lb, Step(activity=unavailability, start_time=unavailability.start_time_lb))
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
