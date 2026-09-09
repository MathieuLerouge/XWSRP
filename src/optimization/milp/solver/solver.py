# Standard library
import time
from typing import cast, Optional

# Third-party libraries
import pyomo.environ as pyo
from pyomo.opt import TerminationCondition

# Local library
from src.optimization.milp.solver.outcome import Outcome

# Global variables
SOLVER_HIGHS = 'highs'
SOLVER_GUROBI = 'gurobi'


##########
# Solver #
##########

class Solver:
    """
    A configured MILP backend able to solve Pyomo models.
    It allows to choose which MILP backend to use: Highs or Gurobi.
    """

    def __init__(self, solver_name: str, mute: bool = True, time_limit: Optional[int] = None):
        """
        Args:
            solver_name: which MILP backend to use, SOLVER_HIGHS or SOLVER_GUROBI.
            mute: if True, suppress the solver's own console output.
            time_limit: solving time limit in seconds, or None for no limit.

        Raises:
            ValueError: if solver_name is neither SOLVER_HIGHS nor SOLVER_GUROBI.
        """
        if solver_name not in (SOLVER_HIGHS, SOLVER_GUROBI):
            raise ValueError(f"Unknown solver name '{solver_name}', expected '{SOLVER_HIGHS}' or '{SOLVER_GUROBI}'.")
        self._solver_name = solver_name
        self._mute = mute
        self._time_limit = time_limit

    @property
    def solver_name(self):
        """Which MILP backend this solver uses, SOLVER_HIGHS or SOLVER_GUROBI."""
        return self._solver_name

    @property
    def mute(self):
        """Whether the solver's own console output is suppressed."""
        return self._mute

    @property
    def time_limit(self):
        """Solving time limit in seconds, or None for no limit."""
        return self._time_limit

    def solve(self, model: pyo.ConcreteModel) -> Outcome:
        """
        Solve a Pyomo model and return a normalized outcome.

        Args:
            model: the Pyomo model to solve, with exactly one active Objective declared.

        Returns:
            an Outcome describing the solve's status, gap, run time and objective value
            (variable values, if any, are loaded onto the model itself).
        """
        return self._solve_once(model, self._time_limit)

    def solve_lexicographically(self, model: pyo.ConcreteModel, objective_expressions: list) -> Outcome:
        """
        Solve a Pyomo model with several objectives in strict priority order (lexicographic optimization).

        Each objective is minimized in turn,
        subject to every higher-priority objective being held at its already-achieved optimal value.
        This replicates Gurobi's ``setObjectiveN`` hierarchical multi-objective feature,
        which has no equivalent in Pyomo, by re-solving the model once per objective and
        freezing each objective's value before moving to the next one
        — the standard solver-agnostic technique for lexicographic optimization.

        Args:
            model: the Pyomo model to solve, with no Objective declared yet
                (this method declares and replaces it once per priority level).
            objective_expressions: the objectives, highest priority first, all implicitly minimized
                (pass a negated expression for an objective that should be maximized).

        Returns:
            the Outcome of the last priority level reached.
            Its objective_value refers to the lowest-priority objective solved for;
            read pyo.value(expr) on higher-priority expressions in
            objective_expressions afterward to recover their (frozen) achieved values.
        """
        outcome = None
        remaining_time = self._time_limit
        for index, expression in enumerate(objective_expressions):
            model.objective = pyo.Objective(expr=expression, sense=pyo.minimize)
            outcome = self._solve_once(model, remaining_time)
            del model.objective
            if not outcome.has_incumbent:
                return outcome
            if remaining_time is not None:
                remaining_time -= outcome.run_time
                if remaining_time <= 0:
                    return outcome
            if index < len(objective_expressions) - 1:
                achieved_value = round(pyo.value(expression))
                model.add_component(
                    f'_lexicographic_freeze_{index}', pyo.Constraint(expr=(expression <= achieved_value))
                )
        return cast(Outcome, outcome)

    def _solve_once(self, model: pyo.ConcreteModel, time_limit: Optional[int]) -> Outcome:
        """Run the underlying Pyomo solver once against the model and return a normalized outcome."""
        pyomo_solver = self._build_pyomo_solver(time_limit)
        start_time = time.perf_counter()
        results = pyomo_solver.solve(model, load_solutions=False)
        run_time = time.perf_counter() - start_time

        termination_condition = results.solver.termination_condition
        is_infeasible = termination_condition in {
            TerminationCondition.infeasible, TerminationCondition.infeasibleOrUnbounded
        }
        is_unbounded = termination_condition == TerminationCondition.unbounded
        is_time_limit = termination_condition == TerminationCondition.maxTimeLimit

        has_incumbent = False
        objective_value = None
        mip_gap = None
        if not (is_infeasible or is_unbounded):
            try:
                model.solutions.load_from(results)
                has_incumbent = True
            except ValueError:
                # NB: raised by Model.solutions.load_from when the time limit is reached with no incumbent found
                has_incumbent = False
        if has_incumbent:
            objective_component = next(model.component_objects(pyo.Objective, active=True))
            objective_value = float(pyo.value(objective_component))
            if termination_condition == TerminationCondition.optimal:
                mip_gap = 0.0
            else:
                problem_info = results.problem[0]
                lower_bound = getattr(problem_info, 'lower_bound', None)
                upper_bound = getattr(problem_info, 'upper_bound', None)
                if objective_component.sense == pyo.minimize:
                    dual_bound = lower_bound if lower_bound is not None else objective_value
                else:
                    dual_bound = upper_bound if upper_bound is not None else objective_value
                mip_gap = abs(objective_value - dual_bound) / max(abs(objective_value), 1e-10)

        return Outcome(
            is_infeasible=is_infeasible, is_unbounded=is_unbounded, is_time_limit=is_time_limit,
            has_incumbent=has_incumbent, objective_value=objective_value, mip_gap=mip_gap, run_time=run_time
        )

    def _build_pyomo_solver(self, time_limit: Optional[int]):
        """Build and configure the underlying Pyomo solver object for this backend."""
        if self._solver_name == SOLVER_HIGHS:
            pyomo_solver = pyo.SolverFactory('appsi_highs')
            pyomo_solver.options['output_flag'] = not self._mute
            if time_limit is not None:
                pyomo_solver.options['time_limit'] = time_limit
        else:
            self._ensure_gurobi_is_usable()
            pyomo_solver = pyo.SolverFactory(SOLVER_GUROBI)
            pyomo_solver.options['OutputFlag'] = 0 if self._mute else 1
            if time_limit is not None:
                pyomo_solver.options['TimeLimit'] = time_limit
        return pyomo_solver

    @staticmethod
    def _ensure_gurobi_is_usable():
        """
        Check that gurobipy is installed and that a valid Gurobi license is available,
        raising a clear error otherwise instead of letting a failure surface later, mid-solve.

        Raises:
            ImportError: if gurobipy is not installed.
            RuntimeError: if gurobipy is installed but no valid Gurobi license is available.
        """
        try:
            import gurobipy
        except ImportError as error:
            raise ImportError(
                f"SOLVER_NAME is set to '{SOLVER_GUROBI}' but gurobipy is not installed. Install it "
                f"(`uv pip install gurobipy`) and make sure a valid Gurobi license is configured, or set "
                f"SOLVER_NAME to '{SOLVER_HIGHS}' in main_configuration.py."
            ) from error
        try:
            with gurobipy.Env():
                pass
        except gurobipy.GurobiError as error:
            raise RuntimeError(
                f"SOLVER_NAME is set to '{SOLVER_GUROBI}' but no valid Gurobi license is available: {error}. "
                f"Fix your Gurobi license setup, or set SOLVER_NAME to '{SOLVER_HIGHS}' in main_configuration.py."
            ) from error
