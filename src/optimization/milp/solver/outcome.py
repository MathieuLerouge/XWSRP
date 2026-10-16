# Standard library
from typing import Optional


###########
# Outcome #
###########

class Outcome:
    """
    Normalized outcome of a MILP solve, independent of which backend produced it.
    """

    def __init__(self, is_infeasible: bool, is_unbounded: bool, is_time_limit: bool, has_incumbent: bool,
                 objective_value: Optional[float], mip_gap: Optional[float], run_time: float):
        """
        Args:
            is_infeasible: whether the solver proved the model infeasible.
            is_unbounded: whether the solver proved the model unbounded.
            is_time_limit: whether the solver stopped because it reached the time limit.
            has_incumbent: whether a feasible solution was found (even if not proven optimal).
            objective_value: the incumbent's objective value, or None if has_incumbent is False.
            mip_gap: the relative optimality gap of the incumbent, or None if has_incumbent is False.
            run_time: wall-clock solving time in seconds.
        """
        self._is_infeasible = is_infeasible
        self._is_unbounded = is_unbounded
        self._is_time_limit = is_time_limit
        self._has_incumbent = has_incumbent
        self._objective_value = objective_value
        self._mip_gap = mip_gap
        self._run_time = run_time
        self._solution = None

    @property
    def is_infeasible(self):
        """Whether the solver proved the model infeasible."""
        return self._is_infeasible

    @property
    def is_unbounded(self):
        """Whether the solver proved the model unbounded."""
        return self._is_unbounded

    @property
    def is_time_limit(self):
        """Whether the solver stopped because it reached the time limit."""
        return self._is_time_limit

    @property
    def has_incumbent(self):
        """Whether a feasible solution was found, even if not proven optimal."""
        return self._has_incumbent

    @property
    def objective_value(self):
        """The incumbent's objective value, or None if has_incumbent is False."""
        return self._objective_value

    @property
    def mip_gap(self):
        """The incumbent's relative optimality gap, or None if has_incumbent is False."""
        return self._mip_gap

    @property
    def run_time(self):
        """Wall-clock solving time in seconds."""
        return self._run_time

    @property
    def solution(self):
        """
        The solution extracted from this outcome, or None if has_incumbent is False or it hasn't
        been extracted yet. Its concrete type depends on which model produced this outcome
        (e.g. a SolutionOpti for Model, a Sequence for a SequenceModel subclass).
        """
        return self._solution

    @solution.setter
    def solution(self, solution):
        self._solution = solution

    def as_string(self) -> str:
        """
        Return this outcome in short, as a progress or diagnostic line reports it.

        Returns:
            The objective value reached, or why there is none,
            followed by the status, the optimality gap when not proven optimal, and the run time
            (e.g. "125 (optimal, 0.120s)" or "512 (time limit reached, gap: 2.30%, 0.130s)").
        """
        if self._is_infeasible:
            status = "infeasible"
        elif self._is_unbounded:
            status = "unbounded"
        elif self._is_time_limit:
            status = "time limit reached"
        else:
            status = "optimal"
        details = [status]
        if self._mip_gap is not None and self._mip_gap > 0:
            details.append(f"gap: {self._mip_gap:.2%}")
        details.append(f"{self._run_time:.3f}s")
        value = f"{self._objective_value:g}" if self._has_incumbent else "no solution"
        return f"{value} ({', '.join(details)})"
