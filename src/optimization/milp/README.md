# Description of the `milp` module

This module implements the MILP-based formulation and solving of the WSRP: assigning tasks to employees,
sequencing each employee's activities, and respecting skill, time-window, unavailability and lunch-break
constraints, through the solver-agnostic Pyomo layer defined here.


# 1. Overview of the MILP layer

`MILPModel` (`milpmodel.py`) is the entry point: given an `Instance`, it builds the whole-workforce MILP
— one set of decision variables, constraints and a weighted objective covering every employee/task pair at
once — and solves it. \
It relies on `MILPModelIndex` (`milpmodelindex.py`) to translate domain objects (`Employee`, `Task`,
`Unavailability`, ...) into the small integer indices that the model's variables and constraints are built
around. \
Solving itself is delegated to the `solver` subpackage: `Solver` wraps a configured Pyomo backend —
`SOLVER_HIGHS` (free, open-source, the default) or `SOLVER_GUROBI` (optional, requires a license) — and
returns a backend-independent `Outcome`. \
`MILPModel.solve(...)` reads that outcome and, when a feasible solution was found, extracts it into a
`SolutionOpti`, stored on the outcome's `solution` attribute; it then returns the outcome itself.

Deciding whether a failure (infeasible/unbounded/time limit) is worth raising as an exception is left to
whichever code calls `solve(...)`, not to the model itself — different callers want different things from
the same outcome, and neither `MILPModel.solve(...)` nor `SequenceModel.solve(...)` (see
`subproblems/README.md`) ever raises on one. `solver.exceptions` defines the `SolveException` hierarchy, and
`OutcomeToExceptionMapper` (`solver.outcometoexceptionmapper`) turns a failing outcome — infeasible,
unbounded, or a reached time limit (with or without a solution) — into the exception it warrants, for
callers that want one.

The `subproblems` subpackage (see its own README) contains a separate family of MILP models, each scoped to
a single employee's sequence of activities rather than the whole workforce.


# 2. Description of the files

`milpmodelindex.py` contains `MILPModelIndex`, the index-translation layer used by `MILPModel`: it assigns
integer indices to employees, tasks and each employee's "hypothetical activities" (departure, tasks,
unavailabilities, comeback, in that order), and exposes lookups (`get_task_by_index`,
`get_hyp_activities_indices`, `get_traveling_duration`, ...) so the rest of the model can be written purely
in terms of indices.

`milpmodel.py` contains `MILPModel`, which builds the decision variables (`X` task-performed indicators,
`T` start times, `L` lunch-break times, `U` employee/activity/activity/time-window assignment indicators,
`V` lunch-break placement indicators), the weighted objective (traveling duration, working duration, number
of performed tasks), and the covering/flow/time-window/time-sequence/skill-level constraints, then solves the
model and extracts the result into a `SolutionOpti`.

`solver` is the subpackage grouping everything about running a MILP solve and interpreting its result,
independently of which model built it (`__init__.py` is just the package marker, empty):

- `solver.py` contains `Solver` and the `SOLVER_HIGHS`/`SOLVER_GUROBI` backend-name constants. `Solver`
  wraps a configured Pyomo `SolverFactory` object for either backend, exposes `solve(model)` for a
  single-objective model and `solve_lexicographically(model, objective_expressions)` for hierarchical
  multi-objective solving (re-solving once per objective, freezing each achieved value in turn — Pyomo/HiGHS
  have no equivalent to Gurobi's `setObjectiveN`), and proactively checks that a valid Gurobi license is
  available before attempting to use that backend.
- `outcome.py` contains `Outcome`, an object normalizing a solve's status (`is_infeasible`, `is_unbounded`,
  `is_time_limit`, `has_incumbent`) and results (`objective_value`, `mip_gap`, `run_time`) independently of
  which backend produced them, plus a `solution` attribute that the calling model fills in after extracting
  its own result (a `SolutionOpti`, a `Sequence`, ..., depending on which model solved it).
- `exceptions.py` contains the `SolveException` hierarchy: `SolveException` (base),
  `InfeasibleModelException`, `UnboundedModelException`, `TimeLimitReachedWithSolutionException` (carries
  the timed-out `Outcome`), and `TimeLimitReachedWithoutSolutionException`.
- `outcometoexceptionmapper.py` contains `OutcomeToExceptionMapper`, whose `map(outcome)` static method
  turns a failing `Outcome` — infeasible, unbounded, or a reached time limit (with or without a solution) —
  into the matching exception instance (or returns `None` for a successful outcome), for callers of
  `solve(...)` that want to raise on a failure without duplicating that mapping logic themselves.

`subproblems` contains the single-employee sequence sub-models; see `subproblems/README.md`.
