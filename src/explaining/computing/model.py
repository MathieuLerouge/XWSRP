# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import (
    SequenceReordering, TaskDeletion, TaskInsertion, TaskRepositioning
)
from src.explaining.neighborhood.restriction import (
    ForbiddenBackwardSubsequence, ForbiddenSequence, ImmediatePrecedence, Precedence, PrecedenceChain
)
from src.modeling.task import Task
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
    Among the feasibility-shortfall operator's candidate employees and candidate tasks,
    the model searches for the (employee, task) pairing and insertion point minimizing, lexicographically:
    the feasibility shortfall, then working duration, then traveling duration.

    Regarding the feasibility shortfall: each feasibility-shortfall task gets its own pair of slack
    variables, so that candidate_start_time + slack_upstream[task] stands in for that task's start time
    wherever it is lower-bounded, and candidate_start_time - slack_downstream[task] stands in wherever it
    is upper-bounded. Whenever a feasibility-shortfall task genuinely fits, both its slacks are 0,
    and the model behaves exactly as if its start time were an ordinary decision variable.
    The feasibility-shortfall objective sums every such task's slacks: for whichever one ends up NOT
    performed, every constraint touching it is vacuous, so its slacks are unconstrained and minimization
    drives them to 0 for free - only the chosen task's slacks end up contributing to the sum.

    For TaskRepositioning and SequenceReordering, which have no candidate set of their own (a single
    already-performed target task, or none at all), feasibility_shortfall_employees/feasibility_shortfall_tasks
    instead mean: the operator's own employee, and either its target task (TaskRepositioning) or a pivot
    task chosen from the employee's own given-solution sequence (SequenceReordering, see _extract_scope).
    The same slack/feasibility-shortfall machinery then applies unchanged, since with singleton candidate
    sets _add_neighborhood_candidate_selection_constraints already reduces to exactly the constraint each
    of them needs (see their Comments in neighborhood/README.md section 3.2).

    A neighborhood may optionally also carry a TaskDeletion operator alongside its feasibility-shortfall
    operator (TaskInsertion/TaskRepositioning/SequenceReordering): deletion never has a "does it fit"
    question of its own (removing a task is always time-feasible in isolation), so it never gets slack
    variables or contributes to the feasibility-shortfall objective - it's handled entirely by
    _add_neighborhood_deletion_constraints.

    NB: In this part of the code, we assume that instance does not consider lunch breaks.

    WIP: This implementation supports a Neighborhood targeted by one feasibility-shortfall operator - a
    TaskInsertion, TaskRepositioning or SequenceReordering - optionally paired with one TaskDeletion (no
    TaskRelocation, no more than one operator of either kind, no TaskDeletion without a feasibility-shortfall
    operator alongside it). A TaskInsertion's candidate employees and candidate tasks may each be one or
    several (covering, respectively, the (Ins,1)/(Ins,2a)/(Ins,3)-style single-candidate shapes and the
    (Ins,2b)/(Ins,2c)-style candidate-set shapes); TaskRepositioning/SequenceReordering are always
    singleton. An ImmediatePrecedence restriction is only supported when both of the feasibility-shortfall
    operator's candidate sets are singletons, since it always pins one specific target task's insertion
    point, which must align with the operator's own (also singleton) candidates.
    """

    def __init__(self, neighborhood: Neighborhood):
        """
        Args:
            neighborhood: the neighborhood to search.

        Raises:
            NotImplementedError: if the neighborhood is not targeted by one feasibility-shortfall operator
                (TaskInsertion, TaskRepositioning or SequenceReordering) optionally paired with one
                TaskDeletion, if it carries an ImmediatePrecedence restriction while the feasibility-shortfall
                operator has more than one candidate employee or candidate task, or if the instance has a
                lunch break.
        """
        self._neighborhood = neighborhood
        (self._feasibility_shortfall_employees, self._feasibility_shortfall_operator,
         self._feasibility_shortfall_tasks, self._deletion_operator) = self._extract_scope(neighborhood)
        super().__init__(neighborhood.solution.instance)

    @staticmethod
    def _extract_scope(neighborhood: Neighborhood):
        """
        Return the (feasibility_shortfall_employees, feasibility_shortfall_operator,
        feasibility_shortfall_tasks, deletion_operator) this implementation supports, or raise.

        feasibility_shortfall_employees/feasibility_shortfall_operator/feasibility_shortfall_tasks
        describe the feasibility-shortfall operator: for a TaskInsertion, these are its own candidate employees/tasks.
        For a TaskRepositioning, its single employee/target_task. For a SequenceReordering, its single
        employee and a pivot task chosen from the employee's own given-solution sequence (the middle
        one - the tailored pipeline's IPModelForReordering3 makes the same arbitrary choice, and for the
        same reason: the feasibility-shortfall objective needs some task to attach slack variables to).
        deletion_operator is the neighborhood's TaskDeletion operator, or None if it doesn't have one.

        Raises:
            NotImplementedError: if the neighborhood is not targeted by one feasibility-shortfall operator
                (TaskInsertion, TaskRepositioning or SequenceReordering) optionally paired with one
                TaskDeletion, if it carries an ImmediatePrecedence restriction while the feasibility-shortfall
                operator has more than one candidate employee or candidate task, or if the instance has a
                lunch break.
        """
        if neighborhood.solution.instance.has_lunch_break:
            raise NotImplementedError(
                "NeighborhoodModel does not support instances with a lunch break"
            )
        if len(neighborhood.operators) not in (1, 2):
            raise NotImplementedError(
                "NeighborhoodModel currently only supports a neighborhood with one or two operators"
            )
        feasibility_shortfall_operator = None
        deletion_operator = None
        for candidate_operator in neighborhood.operators:
            if isinstance(candidate_operator, TaskDeletion):
                if deletion_operator is not None:
                    raise NotImplementedError(
                        "NeighborhoodModel does not support more than one TaskDeletion operator"
                    )
                deletion_operator = candidate_operator
            elif isinstance(candidate_operator, (TaskInsertion, TaskRepositioning, SequenceReordering)):
                if feasibility_shortfall_operator is not None:
                    raise NotImplementedError(
                        "NeighborhoodModel does not support more than one TaskInsertion, "
                        "TaskRepositioning or SequenceReordering operator"
                    )
                feasibility_shortfall_operator = candidate_operator
            else:
                raise NotImplementedError(
                    "NeighborhoodModel currently only supports TaskInsertion, TaskDeletion, "
                    "TaskRepositioning or SequenceReordering operators"
                )
        if feasibility_shortfall_operator is None:
            raise NotImplementedError(
                "NeighborhoodModel requires a TaskInsertion, TaskRepositioning or "
                "SequenceReordering operator alongside TaskDeletion"
            )
        if isinstance(feasibility_shortfall_operator, TaskInsertion):
            feasibility_shortfall_employees = feasibility_shortfall_operator.candidate_employees
            feasibility_shortfall_tasks = feasibility_shortfall_operator.candidate_tasks
        elif isinstance(feasibility_shortfall_operator, TaskRepositioning):
            feasibility_shortfall_employees = frozenset({feasibility_shortfall_operator.employee})
            feasibility_shortfall_tasks = frozenset({feasibility_shortfall_operator.target_task})
        else:
            employee_tasks = list(
                neighborhood.solution.get_sequence(feasibility_shortfall_operator.employee).get_contained_tasks()
            )
            pivot_task = employee_tasks[len(employee_tasks) // 2]
            feasibility_shortfall_employees = frozenset({feasibility_shortfall_operator.employee})
            feasibility_shortfall_tasks = frozenset({pivot_task})
        has_immediate_precedence = any(
            isinstance(restriction, ImmediatePrecedence) for restriction in neighborhood.restrictions
        )
        if has_immediate_precedence and (
                len(feasibility_shortfall_employees) > 1 or len(feasibility_shortfall_tasks) > 1):
            raise NotImplementedError(
                "NeighborhoodModel does not support an ImmediatePrecedence restriction together "
                "with more than one candidate employee or candidate task"
            )
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

    @property
    def feasibility_shortfall(self) -> int:
        """
        The minimized sum, across every feasibility-shortfall task, of the shortfall between its start
        time as constrained from upstream and from downstream: 0 if the task fits without conflict,
        strictly positive if it doesn't (the magnitude of the overlap that would need to be resolved for it to fit).

        Raises:
            AttributeError: if solve() hasn't been called yet, or found no feasible solution.
        """
        if not self.has_solution:
            raise AttributeError("There is no solution stored")
        return round(sum(
            pyo.value(self.var_slack_upstream[task_index]) + pyo.value(self.var_slack_downstream[task_index])
            for task_index in self._feasibility_shortfall_task_indices
        ))
