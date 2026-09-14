# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import SequenceReordering, TaskInsertion, TaskRepositioning
from src.explaining.neighborhood.restriction import (
    ForbiddenSequence, ImmediatePrecedence, Precedence, SequenceOrderFixed
)
from src.modeling.task import Task
from src.optimization.milp.milpmodel import MILPModel
from src.optimization.milp.solver.outcome import Outcome
from src.optimization.milp.solver.solver import Solver


###############################
# NeighborhoodFeasibilityMILP #
###############################

class NeighborhoodFeasibilityMILP(MILPModel):
    """
    MILP model exploring a Neighborhood.
    Every employee and task outside the neighborhood's scope is pinned to reproduce the given solution exactly.
    Among the operator's candidate employees and candidate tasks,
    the model searches for the (employee, task) pairing and insertion point minimizing, lexicographically:
    the target feasibility gap, then working duration, then traveling duration.

    Regarding the target feasibility gap: each candidate task gets its own pair of slack variables, so that
    candidate_start_time + slack_upstream[task] stands in for that candidate's start time wherever it is lower-bounded,
    and candidate_start_time - slack_downstream[task] stands in wherever it is upper-bounded.
    Whenever a candidate genuinely fits, both its slacks are 0,
    and the model behaves exactly as if its start time were an ordinary decision variable.
    The gap objective sums every candidate's slacks: for whichever candidate ends up NOT performed,
    every constraint touching it is vacuous, so its slacks are unconstrained and minimization drives them to 0 for free
    - only the chosen candidate's slacks end up contributing to the sum.

    For TaskRepositioning and SequenceReordering, which have no candidate set of their own (a single
    already-performed target task, or none at all), "candidate employees/tasks" instead means: the
    operator's own employee, and either its target task (TaskRepositioning) or a pivot task chosen from
    the employee's own given-solution sequence (SequenceReordering, see _extract_scope). The same
    slack/gap machinery then applies unchanged, since with singleton candidate sets
    _add_neighborhood_candidate_selection_constraints already reduces to exactly the constraint each of
    them needs (see their Comments in neighborhood/README.md section 3.2).

    NB: In this part of the code, we assume that instance does not consider lunch breaks.

    WIP: This implementation only supports a Neighborhood with exactly one operator - a TaskInsertion,
    TaskRepositioning or SequenceReordering (no TaskDeletion/TaskRelocation, no multi-operator
    neighborhoods yet). A TaskInsertion's candidate employees and candidate tasks may each be one or
    several (covering, respectively, the (Ins,1)/(Ins,2a)/(Ins,3)-style single-candidate shapes and the
    (Ins,2b)/(Ins,2c)-style candidate-set shapes); TaskRepositioning/SequenceReordering are always
    singleton. An ImmediatePrecedence restriction is only supported when both candidate sets are
    singletons, since it always pins one specific target task's insertion point, which must align with
    the operator's own (also singleton) candidates.
    """

    def __init__(self, neighborhood: Neighborhood):
        """
        Args:
            neighborhood: the neighborhood to search.

        Raises:
            NotImplementedError: if the neighborhood is not targeted by a single TaskInsertion,
                TaskRepositioning or SequenceReordering operator, if it carries an ImmediatePrecedence
                restriction while having more than one candidate employee or candidate task, or if the
                instance has a lunch break.
        """
        self._neighborhood = neighborhood
        self._candidate_employees, self._operator, self._candidate_tasks = self._extract_scope(neighborhood)
        super().__init__(neighborhood.solution.instance)

    @staticmethod
    def _extract_scope(neighborhood: Neighborhood):
        """
        Return the (candidate_employees, operator, candidate_tasks) this implementation supports, or raise.

        For a TaskInsertion, these are its own candidate employees/tasks. For a TaskRepositioning, its
        single employee/target_task. For a SequenceReordering, its single employee and a pivot task chosen
        from the employee's own given-solution sequence (the middle one - the tailored pipeline's
        IPModelForReordering3 makes the same arbitrary choice, and for the same reason: the
        feasibility-gap objective needs some candidate task to attach slack variables to).

        Raises:
            NotImplementedError: if the neighborhood is not targeted by a single TaskInsertion,
                TaskRepositioning or SequenceReordering operator, if it carries an ImmediatePrecedence
                restriction while having more than one candidate employee or candidate task, or if the
                instance has a lunch break.
        """
        if neighborhood.solution.instance.has_lunch_break:
            raise NotImplementedError(
                "NeighborhoodFeasibilityMILP does not support instances with a lunch break"
            )
        if len(neighborhood.operators) != 1:
            raise NotImplementedError(
                "NeighborhoodFeasibilityMILP currently only supports a neighborhood with a single operator"
            )
        operator = neighborhood.operators[0]
        if isinstance(operator, TaskInsertion):
            candidate_employees = operator.candidate_employees
            candidate_tasks = operator.candidate_tasks
        elif isinstance(operator, TaskRepositioning):
            candidate_employees = frozenset({operator.employee})
            candidate_tasks = frozenset({operator.target_task})
        elif isinstance(operator, SequenceReordering):
            employee_tasks = list(neighborhood.solution.get_sequence(operator.employee).get_contained_tasks())
            pivot_task = employee_tasks[len(employee_tasks) // 2]
            candidate_employees = frozenset({operator.employee})
            candidate_tasks = frozenset({pivot_task})
        else:
            raise NotImplementedError(
                "NeighborhoodFeasibilityMILP currently only supports a TaskInsertion, TaskRepositioning "
                "or SequenceReordering operator"
            )
        has_immediate_precedence = any(
            isinstance(restriction, ImmediatePrecedence) for restriction in neighborhood.restrictions
        )
        if has_immediate_precedence and (len(candidate_employees) > 1 or len(candidate_tasks) > 1):
            raise NotImplementedError(
                "NeighborhoodFeasibilityMILP does not support an ImmediatePrecedence restriction together "
                "with more than one candidate employee or candidate task"
            )
        return candidate_employees, operator, candidate_tasks

    ######################
    # Decision variables #
    ######################

    def _add_decision_variables(self):
        super()._add_decision_variables()
        self._candidate_employee_indices = frozenset(
            self._data.get_employee_index_by_employee(employee) for employee in self._candidate_employees
        )
        self._candidate_task_indices = frozenset(
            self._data.get_task_index_by_task(task) for task in self._candidate_tasks
        )
        self._model.slack_upstream = pyo.Var(self._candidate_task_indices, domain=pyo.NonNegativeIntegers)
        self._model.slack_downstream = pyo.Var(self._candidate_task_indices, domain=pyo.NonNegativeIntegers)
        self.var_slack_upstream = self._model.slack_upstream
        self.var_slack_downstream = self._model.slack_downstream

    ################################
    # Task time - Target overrides #
    ################################

    def _get_start_time_lb_linear_expression(self, task_index: int):
        if task_index in self._candidate_task_indices:
            return self.vars_T[task_index] + self.var_slack_upstream[task_index]
        return super()._get_start_time_lb_linear_expression(task_index)

    def _get_start_time_ub_linear_expression(self, task_index: int):
        if task_index in self._candidate_task_indices:
            return self.vars_T[task_index] - self.var_slack_downstream[task_index]
        return super()._get_start_time_ub_linear_expression(task_index)

    ######################
    # Objective function #
    ######################

    def _add_objective_function(self):
        """
        Build the objectives minimized lexicographically, highest priority first:
        - the target feasibility gap;
        - then working duration;
        - then traveling duration.
        """
        gap_expression = pyo.quicksum([
            self.var_slack_upstream[task_index] + self.var_slack_downstream[task_index]
            for task_index in self._candidate_task_indices
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
            gap_expression, working_duration_expression, traveling_duration_expression
        ]

    ###############
    # Constraints #
    ###############

    def _add_constraints(self):
        super()._add_constraints()
        self._add_neighborhood_freeze_constraints()
        self._add_neighborhood_candidate_selection_constraints()
        self._add_neighborhood_immediate_precedence_constraints()
        self._add_neighborhood_precedence_constraints()
        self._add_neighborhood_order_fixed_constraints()
        self._add_neighborhood_forbidden_sequence_constraints()

    def _add_neighborhood_freeze_constraints(self):
        """
        Pin every task outside the neighborhood's scope to reproduce the given solution exactly:
        its performance status, its assignee (via a same-assignee constraint), and,
        for tasks whose assignee is outside the neighborhood's scope, its exact start time too
        (tasks belonging to an in-scope employee are left free in time so SequenceOrderFixed's pairwise constraints,
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
        Force exactly one of the operator's candidate tasks to be performed, and, for each candidate task,
        tie its assignee to one of the operator's candidate employees exactly when it is the one performed.
        Both reduce to the original mandatory-coverage-by-one-fixed-employee behavior
        when the operator has exactly one candidate task and one candidate employee.
        """
        if not self._data.instance.must_cover_all_tasks:
            self._model.add_component(
                "NeighborhoodCandidateTaskSelectionConstraint",
                pyo.Constraint(expr=(
                    pyo.quicksum([self.vars_X[task_index] for task_index in self._candidate_task_indices]) == 1
                ))
            )
        for task_index in self._candidate_task_indices:
            is_performed_expression = (
                self.vars_X[task_index] if not self._data.instance.must_cover_all_tasks else 1
            )
            self._model.add_component(
                f"NeighborhoodCandidateAssigneeConstraint[{task_index}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([
                        self.vars_U[indices] for indices in self.vars_U.keys()
                        if indices[0] in self._candidate_employee_indices and indices[1] == task_index
                    ]) == is_performed_expression
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

    def _add_neighborhood_order_fixed_constraints(self):
        """
        For every SequenceOrderFixed restriction, force each consecutive pair of its own declared,
        ordered tasks to keep that order (T[earlier] + duration <= T[later]),
        while leaving each task's exact start time free to shift.
        Only consecutive pairs are needed: with non-negative durations,
        locking each one transitively implies the same bound for every non-consecutive pair down the chain.
        The task list is the restriction's own, self-contained definition of what it locks
        - no lookup into the given solution is needed here at all.
        """
        order_fixed_restrictions = [
            restriction for restriction in self._neighborhood.restrictions
            if isinstance(restriction, SequenceOrderFixed)
        ]
        for restriction in order_fixed_restrictions:
            tasks = restriction.tasks
            for earlier_task, later_task in zip(tasks, tasks[1:]):
                self._add_precedence_constraint("NeighborhoodOrderFixedConstraint", earlier_task, later_task)

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
    def target_feasibility_gap(self) -> int:
        """
        The minimized sum, across every candidate task, of the gap between its start time as constrained
        from upstream and from downstream: 0 if the chosen candidate fits without conflict,
        strictly positive if it doesn't (the magnitude of the overlap that would need to be resolved for it to fit).

        Raises:
            AttributeError: if solve() hasn't been called yet, or found no feasible solution.
        """
        if not self.has_solution:
            raise AttributeError("There is no solution stored")
        return round(sum(
            pyo.value(self.var_slack_upstream[task_index]) + pyo.value(self.var_slack_downstream[task_index])
            for task_index in self._candidate_task_indices
        ))
