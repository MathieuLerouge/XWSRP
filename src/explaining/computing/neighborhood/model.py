# Standard library
from typing import cast

# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.explaining.computing.neighborhood.checker import ModelCompatibilityChecker
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import TaskDeletion, TaskInsertion, TaskRepositioning
from src.explaining.neighborhood.restriction import (
    ForbiddenBackwardSubsequence, ForbiddenSequence, ImmediatePrecedence, Precedence, PrecedenceChain
)
from src.modeling.activity import Activity
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.optimization.heuristics.solution import SolutionForHeuristics
from src.optimization.milp.index import COMING_BACK_HOME_INDEX, LEAVING_HOME_INDEX
from src.optimization.milp.model import Model
from src.optimization.milp.solver.outcome import Outcome
from src.optimization.milp.solver.solver import Solver


#####################
# NeighborhoodModel #
#####################

class NeighborhoodModel(Model):
    """
    MILP model exploring a Neighborhood.
    Every employee and task outside the neighborhood's scope is pinned to reproduce the given solution exactly.
    The model searches for the solution minimizing, lexicographically:
    the feasibility shortfall, then working duration, then traveling duration.

    Regarding the feasibility shortfall: each feasibility-shortfall task gets its own pair of slack variables, so that:
     • candidate_start_time + slack_upstream[task] stands in for that task's start time wherever it is lower-bounded;
     • and candidate_start_time - slack_downstream[task] stands in wherever it is upper-bounded.
    Whenever a feasibility-shortfall task genuinely fits, both its slacks are 0,
    and the model behaves exactly as if its start time were an ordinary decision variable.

    Once solved, this model reports:
     • the shortfall itself (feasibility_shortfall);
     • which employees and tasks it is about (conflicting_employee_and_task);
     • and the route each employee ended up with (get_solved_route).

    WIP: The direction this module is heading in is to handle Neighborhoods built from
    several operator and restriction primitives at once.
    Assuming that there is at most one conflicting (employee, task) pair is relevant only for
    the Neighborhood shapes handled today, which have exactly one feasibility-shortfall operator.
    """

    def __init__(self, neighborhood: Neighborhood):
        """
        Args:
            neighborhood: the neighborhood to search.

        Raises:
            NotImplementedError: if the neighborhood is not targeted by one feasibility-shortfall operator
                (TaskInsertion, TaskRepositioning or SequenceReordering) optionally paired with one
                TaskDeletion, if it carries an ImmediatePrecedence restriction while the feasibility-shortfall
                operator has more than one candidate employee or candidate task,
                or if the instance has a lunch break or must cover all its tasks.
        """
        self._neighborhood = neighborhood
        (self._feasibility_shortfall_employees, self._feasibility_shortfall_operator,
         self._feasibility_shortfall_tasks, self._deletion_operator) = self._extract_scope(neighborhood)
        super().__init__(neighborhood.solution.instance)

    @staticmethod
    def _extract_scope(neighborhood: Neighborhood):
        """
        Return a tuple of four elements:
         • feasibility_shortfall_employees;
         • feasibility_shortfall_operator;
         • feasibility_shortfall_tasks;
         • deletion_operator.

        Whether the neighborhood is one this model can be built for is ModelCompatibilityChecker's question,
        not this method's: it asks first and raises whatever answer it gets,
        so the loop below can take the shape for granted rather than re-checking it.

        Raises:
            NotImplementedError: if ModelCompatibilityChecker finds the neighborhood incompatible with this model.
        """
        reason_for_incompatibility = ModelCompatibilityChecker.unsupported_reason(neighborhood)
        if reason_for_incompatibility is not None:
            raise NotImplementedError(reason_for_incompatibility)
        feasibility_shortfall_operator = None
        deletion_operator = None
        for candidate_operator in neighborhood.operators:
            if isinstance(candidate_operator, TaskDeletion):
                deletion_operator = candidate_operator
            else:
                feasibility_shortfall_operator = candidate_operator
        if isinstance(feasibility_shortfall_operator, TaskInsertion):
            feasibility_shortfall_employees = feasibility_shortfall_operator.candidate_employees
            feasibility_shortfall_tasks = feasibility_shortfall_operator.candidate_tasks
        elif isinstance(feasibility_shortfall_operator, TaskRepositioning):
            feasibility_shortfall_employees = frozenset({feasibility_shortfall_operator.employee})
            feasibility_shortfall_tasks = frozenset({feasibility_shortfall_operator.target_task})
        else:
            # NB: A SequenceReordering, the only kind left once the checker has approved the neighborhood.
            employee_tasks = list(
                neighborhood.solution.get_sequence(feasibility_shortfall_operator.employee).get_contained_tasks()
            )
            pivot_task = employee_tasks[len(employee_tasks) // 2]
            feasibility_shortfall_employees = frozenset({feasibility_shortfall_operator.employee})
            feasibility_shortfall_tasks = frozenset({pivot_task})
        return (
            feasibility_shortfall_employees, feasibility_shortfall_operator, feasibility_shortfall_tasks,
            deletion_operator
        )

    ######################
    # Decision variables #
    ######################

    def _add_decision_variables(self):
        super()._add_decision_variables()
        self._feasibility_shortfall_employee_indices = frozenset(
            self._data.get_employee_index_by_employee(employee)
            for employee in self._feasibility_shortfall_employees
        )
        self._feasibility_shortfall_task_indices = frozenset(
            self._data.get_task_index_by_task(task) for task in self._feasibility_shortfall_tasks
        )
        self._model.slack_upstream = pyo.Var(
            self._feasibility_shortfall_task_indices, domain=pyo.NonNegativeIntegers
        )
        self._model.slack_downstream = pyo.Var(
            self._feasibility_shortfall_task_indices, domain=pyo.NonNegativeIntegers
        )
        self.var_slack_upstream = self._model.slack_upstream
        self.var_slack_downstream = self._model.slack_downstream

    ################################
    # Task time - Target overrides #
    ################################

    def _get_start_time_lb_linear_expression(self, task_index: int):
        if task_index in self._feasibility_shortfall_task_indices:
            return self.vars_T[task_index] + self.var_slack_upstream[task_index]
        return super()._get_start_time_lb_linear_expression(task_index)

    def _get_start_time_ub_linear_expression(self, task_index: int):
        if task_index in self._feasibility_shortfall_task_indices:
            return self.vars_T[task_index] - self.var_slack_downstream[task_index]
        return super()._get_start_time_ub_linear_expression(task_index)

    ######################
    # Objective function #
    ######################

    def _add_objective_function(self):
        """
        Build the objectives minimized lexicographically, highest priority first:
        - the feasibility shortfall;
        - then working duration;
        - then traveling duration.
        """
        feasibility_shortfall_expression = pyo.quicksum([
            self.var_slack_upstream[task_index] + self.var_slack_downstream[task_index]
            for task_index in self._feasibility_shortfall_task_indices
        ])
        if self._data.instance.must_cover_all_tasks:
            working_duration_expression = pyo.quicksum(
                [self._data.get_task_by_index(j).duration for j in self._data.tasks_indices]
            )
        else:
            working_duration_expression = pyo.quicksum([
                self.vars_X[j] * self._data.get_task_by_index(j).duration for j in self._data.tasks_indices
            ])
        traveling_duration_expression = pyo.quicksum([
            self.vars_U[indices] * self._data.get_traveling_duration(
                employee_index=indices[0], activity_index1=indices[1], activity_index2=indices[2]
            )
            for indices in self.vars_U.keys()
        ])
        self._objectives_in_priority_order = [
            feasibility_shortfall_expression, working_duration_expression, traveling_duration_expression
        ]

    ###############
    # Constraints #
    ###############

    def _add_constraints(self):
        super()._add_constraints()
        self._add_neighborhood_freeze_constraints()
        self._add_neighborhood_candidate_selection_constraints()
        self._add_neighborhood_deletion_constraints()
        self._add_neighborhood_immediate_precedence_constraints()
        self._add_neighborhood_precedence_constraints()
        self._add_neighborhood_precedence_chain_constraints()
        self._add_neighborhood_forbidden_sequence_constraints()
        self._add_neighborhood_forbidden_backward_subsequence_constraints()

    def _add_neighborhood_freeze_constraints(self):
        """
        Pin every task outside the neighborhood's scope to reproduce the given solution exactly:
        its performance status, its assignee (via a same-assignee constraint), and,
        for tasks whose assignee is outside the neighborhood's scope, its exact start time too
        (tasks belonging to an in-scope employee are left free in time so PrecedenceChain's pairwise constraints,
        added separately, can shift them to make room for whichever candidate task ends up inserted).
        """
        solution = self._neighborhood.solution
        scope = self._neighborhood.scope
        for task in self._data.instance.tasks:
            if task in scope:
                continue
            task_index = self._data.get_task_index_by_task(task)
            performed = solution.get_task_performance_status(task)
            if not self._data.instance.must_cover_all_tasks:
                self.vars_X[task_index].fix(1 if performed else 0)
            if performed:
                assignee = solution.get_task_assignee(task)
                assignee_index = self._data.get_employee_index_by_employee(assignee)
                self._model.add_component(
                    f"NeighborhoodSameAssigneeConstraint[{task_index}]",
                    pyo.Constraint(expr=(
                        pyo.quicksum([
                            self.vars_U[indices] for indices in self.vars_U.keys()
                            if indices[0] == assignee_index and indices[1] == task_index
                        ]) == 1
                    ))
                )
                if assignee not in scope:
                    self.vars_T[task_index].fix(solution.get_task_start_time(task))

    def _add_neighborhood_candidate_selection_constraints(self):
        """
        Force exactly one of the feasibility-shortfall tasks to be performed, and, for each one,
        tie its assignee to one of the feasibility-shortfall employees exactly when it is the one performed.
        Both reduce to the original mandatory-coverage-by-one-fixed-employee behavior
        when there is exactly one feasibility-shortfall task and one feasibility-shortfall employee.
        """
        if not self._data.instance.must_cover_all_tasks:
            self._model.add_component(
                "NeighborhoodCandidateTaskSelectionConstraint",
                pyo.Constraint(expr=(
                    pyo.quicksum(
                        [self.vars_X[task_index] for task_index in self._feasibility_shortfall_task_indices]
                    ) == 1
                ))
            )
        for task_index in self._feasibility_shortfall_task_indices:
            is_performed_expression = (
                self.vars_X[task_index] if not self._data.instance.must_cover_all_tasks else 1
            )
            self._model.add_component(
                f"NeighborhoodCandidateAssigneeConstraint[{task_index}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([
                        self.vars_U[indices] for indices in self.vars_U.keys()
                        if indices[0] in self._feasibility_shortfall_employee_indices and indices[1] == task_index
                    ]) == is_performed_expression
                ))
            )

    def _add_neighborhood_deletion_constraints(self):
        """
        For the neighborhood's TaskDeletion operator, if any, bound how many of its candidate tasks stop
        being performed, and tie whichever candidates remain performed to their original given-solution
        assignee (deletion never reassigns a survivor to a different employee - that's what pairing it
        with a ForbiddenBackwardSubsequence, rather than freeing survivors' assignee outright, is for).
        """
        if self._deletion_operator is None:
            return
        solution = self._neighborhood.solution
        candidate_task_indices = [
            self._data.get_task_index_by_task(task) for task in self._deletion_operator.candidate_tasks
        ]
        nb_candidates = len(candidate_task_indices)
        performed_sum = pyo.quicksum([self.vars_X[task_index] for task_index in candidate_task_indices])
        self._model.add_component(
            "NeighborhoodDeletionCountConstraint",
            pyo.Constraint(expr=(
                self._deletion_operator.min_nb_removals, nb_candidates - performed_sum,
                self._deletion_operator.max_nb_removals
            ))
        )
        for task in self._deletion_operator.candidate_tasks:
            task_index = self._data.get_task_index_by_task(task)
            assignee_index = self._data.get_employee_index_by_employee(solution.get_task_assignee(task))
            self._model.add_component(
                f"NeighborhoodDeletionAssigneeConstraint[{task_index}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([
                        self.vars_U[indices] for indices in self.vars_U.keys()
                        if indices[0] == assignee_index and indices[1] == task_index
                    ]) == self.vars_X[task_index]
                ))
            )

    def _add_neighborhood_immediate_precedence_constraints(self):
        """
        For every ImmediatePrecedence restriction, pin its successor's performance immediately after its predecessor.
        Whichever employee ends up performing both that's constrained, not a specific one
        (other neighborhood constraints - typically the operator's own singleton candidates -
        are what actually pin down which employee that is).
        Only reachable with singleton candidate sets (_extract_scope rejects any other combination).
        """
        immediate_precedence_restrictions = [
            restriction for restriction in self._neighborhood.restrictions
            if isinstance(restriction, ImmediatePrecedence)
        ]
        any_employee_index = next(iter(self._data.employees_indices))
        for restriction in immediate_precedence_restrictions:
            predecessor_index = self._data.get_hyp_activity_index_by_activity(
                any_employee_index, restriction.predecessor
            )
            successor_index = self._data.get_hyp_activity_index_by_activity(
                any_employee_index, restriction.successor
            )
            self._model.add_component(
                f"NeighborhoodImmediatePrecedenceConstraint[{predecessor_index},{successor_index}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([
                        self.vars_U[indices] for indices in self.vars_U.keys()
                        if indices[1] == predecessor_index and indices[2] == successor_index
                    ]) == 1
                ))
            )

    def _add_precedence_constraint(self, component_name_prefix: str, earlier_task: Task, later_task: Task):
        """
        Add a single T[earlier] + duration <= T[later] constraint, named component_name_prefix[...].

        Args:
            component_name_prefix: The prefix used to name the added pyomo constraint component.
            earlier_task: The task that must finish no later than later_task starts.
            later_task: The task that must start no earlier than earlier_task finishes.
        """
        earlier_index = self._data.get_task_index_by_task(earlier_task)
        later_index = self._data.get_task_index_by_task(later_task)
        self._model.add_component(
            f"{component_name_prefix}[{earlier_index},{later_index}]",
            pyo.Constraint(expr=(
                self.vars_T[earlier_index] + earlier_task.duration <= self.vars_T[later_index]
            ))
        )

    def _add_neighborhood_precedence_constraints(self):
        """
        For every Precedence restriction, force its predecessor to finish no later than its successor starts
        (T[predecessor] + duration <= T[successor]), while leaving both tasks' exact start times free to shift.
        """
        precedence_restrictions = [
            restriction for restriction in self._neighborhood.restrictions
            if isinstance(restriction, Precedence)
        ]
        for restriction in precedence_restrictions:
            self._add_precedence_constraint(
                "NeighborhoodPrecedenceConstraint", restriction.predecessor, restriction.successor
            )

    def _add_neighborhood_precedence_chain_constraints(self):
        """
        For every PrecedenceChain restriction, force each consecutive pair of its own declared,
        ordered tasks to keep that order (T[earlier] + duration <= T[later]),
        while leaving each task's exact start time free to shift.
        Only consecutive pairs are needed: with non-negative durations,
        locking each one transitively implies the same bound for every non-consecutive pair down the chain.
        The task list is the restriction's own, self-contained definition of what it locks
        - no lookup into the given solution is needed here at all.
        """
        precedence_chain_restrictions = [
            restriction for restriction in self._neighborhood.restrictions
            if isinstance(restriction, PrecedenceChain)
        ]
        for restriction in precedence_chain_restrictions:
            tasks = restriction.tasks
            for earlier_task, later_task in zip(tasks, tasks[1:]):
                self._add_precedence_constraint("NeighborhoodPrecedenceChainConstraint", earlier_task, later_task)

    def _add_neighborhood_forbidden_sequence_constraints(self):
        """
        For every ForbiddenSequence restriction, forbid its employee's route from containing its chain of
        activities as a contiguous run: not all of the chain's consecutive arcs may hold at once.
        """
        forbidden_sequence_restrictions = [
            restriction for restriction in self._neighborhood.restrictions
            if isinstance(restriction, ForbiddenSequence)
        ]
        for restriction in forbidden_sequence_restrictions:
            employee_index = self._data.get_employee_index_by_employee(restriction.employee)
            activity_indices = [
                self._data.get_hyp_activity_index_by_activity(employee_index, activity)
                for activity in restriction.activities
            ]
            forbidden_arcs = set(zip(activity_indices, activity_indices[1:]))
            arc_sum = pyo.quicksum([
                self.vars_U[indices] for indices in self.vars_U.keys()
                if indices[0] == employee_index and (indices[1], indices[2]) in forbidden_arcs
            ])
            self._model.add_component(
                f"NeighborhoodForbiddenSequenceConstraint[{employee_index},{activity_indices}]",
                pyo.Constraint(expr=(arc_sum <= len(activity_indices) - 2))
            )

    def _add_neighborhood_forbidden_backward_subsequence_constraints(self):
        """
        For every ForbiddenBackwardSubsequence restriction, forbid its employee's route from ever
        traveling directly from a later listed task to an earlier one. Whichever of them remain performed
        keep their original relative order this way; any that become unperformed simply have no arcs at
        all, so the base routing constraints bridge over them for free, with no extra constraint needed.
        """
        forbidden_backward_subsequence_restrictions = [
            restriction for restriction in self._neighborhood.restrictions
            if isinstance(restriction, ForbiddenBackwardSubsequence)
        ]
        for restriction in forbidden_backward_subsequence_restrictions:
            employee_index = self._data.get_employee_index_by_employee(restriction.employee)
            task_indices = [self._data.get_task_index_by_task(task) for task in restriction.tasks]
            backward_pairs = {
                (task_indices[j], task_indices[i])
                for i in range(len(task_indices)) for j in range(i + 1, len(task_indices))
            }
            for later_index, earlier_index in backward_pairs:
                self._model.add_component(
                    f"NeighborhoodForbiddenBackwardSubsequenceConstraint[{employee_index},"
                    f"{later_index},{earlier_index}]",
                    pyo.Constraint(expr=(
                        pyo.quicksum([
                            self.vars_U[indices] for indices in self.vars_U.keys()
                            if indices[0] == employee_index and indices[1] == later_index
                            and indices[2] == earlier_index
                        ]) == 0
                    ))
                )

    ###########
    # Solving #
    ###########

    def _solve(self, mute: bool, solver_name: str) -> Outcome:
        solver = Solver(solver_name, mute=mute, time_limit=self._solving_time_limit)
        return solver.solve_lexicographically(self._model, self._objectives_in_priority_order)

    ###########
    # Results #
    ###########

    def _initialize_solution(self):
        """
        Build this model's solution as a SolutionForHeuristics rather than the base SolutionOpti,
        so that its sequences are SequenceForHeuristics whose steps carry the BTS/FTS time slacks.
        """
        self._solution = SolutionForHeuristics(self._data.instance, heuristic_id=self._solving_method_id)

    @property
    def solution(self) -> SolutionForHeuristics:
        """
        This model's solution as a SolutionForHeuristics.

        Raises:
            AttributeError: if solve() hasn't been called yet, or found no feasible solution.
        """
        return cast(SolutionForHeuristics, super().solution)

    @property
    def feasibility_shortfall(self) -> int:
        """
        The minimized sum, across every feasibility-shortfall task, of the shortfall between
        its start time as constrained from upstream and from downstream:
        0 if the task fits without conflict, strictly positive if it doesn't
        (the magnitude of the overlap that would need to be resolved for it to fit).

        Raises:
            AttributeError: if solve() hasn't been called yet, or found no feasible solution.
        """
        if not self.has_solution:
            raise AttributeError("There is no solution stored")
        return round(sum(
            pyo.value(self.var_slack_upstream[task_index]) + pyo.value(self.var_slack_downstream[task_index])
            for task_index in self._feasibility_shortfall_task_indices
        ))

    @property
    def conflicting_employee_and_task(self) -> tuple[Employee, Task]:
        """
        The (employee, task) pair this model's feasibility shortfall is about:
        whichever feasibility-shortfall task the solution ends up performing, and whoever performs it.

        WIP: The direction this module is heading in is to handle Neighborhoods built from
        several operator and restriction primitives at once.
        This method is relevant only for the Neighborhood handled today,
        which have exactly one feasibility-shortfall operator.

        Raises:
            AttributeError: if solve() hasn't been called yet, or found no feasible solution.
        """
        performed_tasks = [
            task for task in self._feasibility_shortfall_tasks if self.solution.get_task_performance_status(task)
        ]
        assert len(performed_tasks) == 1, (
            f"Expected exactly one performed feasibility-shortfall task, got {len(performed_tasks)}"
        )
        conflicting_task = performed_tasks[0]
        return self.solution.get_task_assignee(conflicting_task), conflicting_task

    def get_solved_route(self, employee: Employee) -> list[Activity]:
        """
        Return the activities the given employee performs between leaving home and coming back home,
        in the order this model's solved routing variables put them.

        The solution's own sequence can't be relied on for this ordering. It orders steps by start time,
        and a feasibility-shortfall task's reported start time is the one its upstream constraints alone
        imply (see Model._extract_solution), whereas the steps after it in the route are timed against the
        looser value its downstream constraints see. As soon as the shortfall is strictly positive those
        two can cross, sorting steps into an order the route never had.

        Args:
            employee: The employee whose solved route is read.

        Returns:
            The employee's activities in route order, empty if they perform nothing. Note that this only
            covers the route out of leaving home: with the sequencing relaxed at a feasibility-shortfall
            task, the solver can leave a cycle of tasks disconnected from that route, and those are not
            reported here (see UnattributableFeasibilityShortfallException).

        Raises:
            AttributeError: if solve() hasn't been called yet, or found no feasible solution.
        """
        if not self.has_solution:
            raise AttributeError("There is no solution stored")
        employee_index = self._data.get_employee_index_by_employee(employee)
        successor_index_by_activity_index = {
            indices[1]: indices[2] for indices in self.vars_U.keys()
            if indices[0] == employee_index and pyo.value(self.vars_U[indices]) > 0.99
        }
        activities: list[Activity] = []
        activity_index = successor_index_by_activity_index.get(LEAVING_HOME_INDEX, COMING_BACK_HOME_INDEX)
        while activity_index != COMING_BACK_HOME_INDEX:
            activities.append(self._data.get_hyp_activity_by_indices(employee_index, activity_index))
            assert len(activities) <= len(successor_index_by_activity_index), \
                f"{employee.name}'s solved route cycles back on itself"
            activity_index = successor_index_by_activity_index[activity_index]
        return activities
