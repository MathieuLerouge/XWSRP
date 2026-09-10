# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.explaining.neighborhood.constraint import SequenceOrderFixed
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import POSITION_SIDE_AFTER, TaskInsertion
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

    NB: In this part of the code, we assume that instance does not consider lunch breaks.

    WIP: This implementation only supports a Neighborhood with exactly one operator, a TaskInsertion
    (no TaskDeletion/TaskRelocation, no multi-operator neighborhoods yet).
    Its candidate employees and candidate tasks may each be one or several
    (covering, respectively, the (Ins,1)/(Ins,2a)/(Ins,3)-style single-candidate shapes
    and the (Ins,2b)/(Ins,2c)-style candidate-set shapes),
    except that a pinned anchor position is only supported when both candidate sets are singletons,
    since an anchor is always relative to one specific employee's sequence and one specific target task.
    """

    def __init__(self, neighborhood: Neighborhood):
        """
        Args:
            neighborhood: the neighborhood to search.

        Raises:
            NotImplementedError: if the neighborhood is not targeted by a single TaskInsertion operator,
                if the operator pins an anchor position while having more than one candidate employee or
                candidate task, or if the instance has a lunch break.
        """
        self._neighborhood = neighborhood
        self._candidate_employees, self._operator, self._candidate_tasks = self._extract_scope(neighborhood)
        super().__init__(neighborhood.solution.instance)

    @staticmethod
    def _extract_scope(neighborhood: Neighborhood):
        """
        Return the (candidate_employees, operator, candidate_tasks) this implementation supports, or raise.

        Raises:
            NotImplementedError: if the neighborhood is not targeted by a single TaskInsertion operator,
                if the operator pins an anchor position while having more than one candidate employee or
                candidate task, or if the instance has a lunch break.
        """
        if neighborhood.solution.instance.has_lunch_break:
            raise NotImplementedError(
                "NeighborhoodFeasibilityMILP does not support instances with a lunch break"
            )
        if len(neighborhood.operators) != 1 or not isinstance(neighborhood.operators[0], TaskInsertion):
            raise NotImplementedError(
                "NeighborhoodFeasibilityMILP currently only supports a neighborhood with a single "
                "TaskInsertion operator"
            )
        operator = neighborhood.operators[0]
        if operator.anchor_activity is not None and (
                len(operator.candidate_employees) > 1 or len(operator.candidate_tasks) > 1):
            raise NotImplementedError(
                "NeighborhoodFeasibilityMILP does not support a pinned anchor position together with "
                "more than one candidate employee or candidate task"
            )
        return operator.candidate_employees, operator, operator.candidate_tasks

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
        self._add_neighborhood_anchor_constraint()
        self._add_neighborhood_order_fixed_constraints()

    def _add_neighborhood_freeze_constraints(self):
        """
        Pin every task other than the operator's candidate tasks to reproduce the given solution exactly:
        its performance status, its assignee (via a same-assignee constraint, since MILPModel's own
        covering constraints only guarantee someone covers a task, not that it stays with its current
        employee), and, for tasks not assigned to one of the operator's candidate employees, its exact
        start time too (tasks belonging to a candidate employee are left free in time so
        SequenceOrderFixed's pairwise precedence constraints, added separately, can shift them to make
        room for whichever candidate task ends up inserted).
        """
        solution = self._neighborhood.solution
        for task in self._data.instance.tasks:
            if task in self._candidate_tasks:
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
                if assignee not in self._candidate_employees:
                    self.vars_T[task_index].fix(solution.get_task_start_time(task))

    def _add_neighborhood_candidate_selection_constraints(self):
        """
        Force exactly one of the operator's candidate tasks to be performed, and, for each candidate
        task, tie its assignee to one of the operator's candidate employees exactly when it is the one
        performed. Both reduce to the original mandatory-coverage-by-one-fixed-employee behavior when the
        operator has exactly one candidate task and one candidate employee.
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

    def _add_neighborhood_anchor_constraint(self):
        """
        Pin the target task's insertion point immediately before/after the operator's anchor activity.
        Only reachable with singleton candidate sets (_extract_scope rejects any other combination).
        """
        if self._operator.anchor_activity is None:
            return
        employee_index = self._data.get_employee_index_by_employee(next(iter(self._candidate_employees)))
        target_index = self._data.get_task_index_by_task(next(iter(self._candidate_tasks)))
        anchor_index = self._data.get_hyp_activity_index_by_activity(employee_index, self._operator.anchor_activity)
        if self._operator.anchor_side == POSITION_SIDE_AFTER:
            from_index, to_index = anchor_index, target_index
        else:
            from_index, to_index = target_index, anchor_index
        self._model.add_component(
            "NeighborhoodAnchorConstraint",
            pyo.Constraint(expr=(
                pyo.quicksum([
                    self.vars_U[indices] for indices in self.vars_U.keys()
                    if indices[0] == employee_index and indices[1] == from_index and indices[2] == to_index
                ]) == 1
            ))
        )

    def _add_neighborhood_order_fixed_constraints(self):
        """
        For every employee carrying a SequenceOrderFixed constraint,
        force every pair of their already-performed tasks to keep their current relative order
        (T[earlier] + duration <= T[later]), while leaving each task's exact start time free to shift
        to make room for whichever candidate task ends up inserted into their sequence.
        None of these tasks is ever a candidate task (candidate tasks aren't performed yet in the given solution),
        so this never needs the lb/ub hooks.
        """
        order_fixed_employees = [
            constraint.employee for constraint in self._neighborhood.constraints
            if isinstance(constraint, SequenceOrderFixed)
        ]
        for employee in order_fixed_employees:
            sequence = self._neighborhood.solution.get_sequence(employee)
            original_tasks = sequence.get_contained_tasks()
            for earlier_position in range(len(original_tasks)):
                for later_position in range(earlier_position + 1, len(original_tasks)):
                    earlier_task = original_tasks[earlier_position]
                    later_task = original_tasks[later_position]
                    earlier_index = self._data.get_task_index_by_task(earlier_task)
                    later_index = self._data.get_task_index_by_task(later_task)
                    self._model.add_component(
                        f"NeighborhoodOrderFixedConstraint[{earlier_index},{later_index}]",
                        pyo.Constraint(expr=(
                            self.vars_T[earlier_index] + earlier_task.duration <= self.vars_T[later_index]
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
