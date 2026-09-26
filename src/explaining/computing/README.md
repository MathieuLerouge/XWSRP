# Description of the `computing` module

This module is the computational core that answers a question by attempting to modify the solution. \
Whatever the route taken, it produces the same two things: 
a support `Solution` (the arrangement the question asked about, whether or not it works) and, 
when it doesn't work, a **`Conflict`** saying why. \
Both feed directly into `answering`.


# 1. Overview

There are two independent pipelines, and they answer the same questions.

The **tailored pipeline** (`templates`) dispatches each question template to its own transformation
method. \
`dispatch.py` routes a `ContrastiveQuestion`/`ScenarioQuestion` to `contrastive_and_scenario` 
and a `CounterfactualQuestion` to `counterfactual`, through lookup tables keyed by template id. \
Either way the transformations are grouped by family (insertion, swap, reordering) one file and one `*Applier` each, 
whose `apply_<template>` static methods all return a `TransformationResult`. \
Inside `contrastive_and_scenario`, most templates are answered by polynomial algorithms 
(built on `optimization.heuristics`' `Evaluator` and `SlackTimeComputer`); 
the three order-free `*,3` templates need a joint re-optimization instead and get their own small MILPs (`milp`). \
`counterfactual` is MILP-based throughout: it searches for the minimal instance alterations 
that would make the requested action feasible.

The **neighborhood pipeline** (`model.py`) is the generic alternative. 
`NeighborhoodModel` turns any `Neighborhood` into one MILP, rather than having a handwritten function per template. 
It reports a **feasibility shortfall**: 0 when the requested arrangement fits, 
otherwise how much the conflicting task's start time has to be stretched for it to. \
`ConflictExtractor` then turns that shortfall into the same `Conflict` the tailored pipeline would return.

Only the tailored pipeline handles counterfactual questions today; `NeighborhoodModel` covers the
contrastive/scenario ones.


# 2. Description of the files

`model.py` contains `NeighborhoodModel`, described above.

`checker.py` contains `ModelCompatibilityChecker`, the one place saying 
which neighborhoods `NeighborhoodModel` can be built for and why not when it can't. 
Both `NeighborhoodModel` and `neighborhood`'s `Assembler` consult it rather than restating its rules, 
so there is a single place to widen.

`exceptions.py` contains `ImpossibleTransformationException`, 
raised when a question asks for something the given solution makes meaningless 
(e.g. inserting a non-performed task when every task is already performed),
and `UnattributableFeasibilityShortfallException`, described in section 3.

In `conflict` subpackage:
- `conflict.py` contains `Conflict` and its two subclasses, `SkillConflict` and `TimeConflict`, described in section 3.
- `extractor.py` contains `ConflictExtractor`, which maps a `Neighborhood` to a `SkillConflict`
  and a solved `NeighborhoodModel` to a `TimeConflict`.

In `templates` subpackage:
- `dispatch.py` contains `TransformationDispatcher`, 
  which hands a `Question` to the transformation its template calls for. 
  Three tables hold that mapping: the contrastive ones are split by how they are computed, 
  since only the MILP-based three take a solving time limit, and the counterfactual ones share a single table.
- `common` holds what both kinds share: `TransformationPreconditionChecker`, `TransformationDescriptionBuilder`,
  `TransformationResult` (the support solution, the conflict if any, the per-language descriptions, 
  and the instance alterations for counterfactual questions), `TailoredConflictBuilder`, and `MILPTransformationRunner`.
- `contrastive_and_scenario/{insertion,swap,reordering}.py` contain: 
  `InsertionApplier`, `SwapApplier` and `ReorderingApplier`. 
  Each gathers its family's templates, polynomial and MILP-based alike, 
  and its `milp` subpackage holds the models the `*,3` template needs.
- `counterfactual/{insertion,swap,reordering}.py` contain: 
  `InsertionWithAlterationsApplier`, `SwapWithAlterationsApplier` and `ReorderingWithAlterationsApplier`, 
  laid out the same way, their `milp` subpackage carrying one model per template 
  since every counterfactual template needs one.
- Each kind has a `result.py` with a `build_transformation_result_from_milp_model` function, 
  shared by its family appliers. It reads the support solution, the conflict and the route off a solved model, 
  and takes from its caller the function wording that route into a sentence — the one thing the families do differently.

The `*,3` models give the task the question is about — the pivot task — two start times rather than one:
a backward one, pushed later by everything the route does before it, 
and a forward one, pulled earlier by everything it does after. 
An arrangement fits when the two meet. 
The gap between them is minimized ahead of anything else, 
so a route that cannot fit the task still comes back with the arrangement that misses by the least, 
which is what the `TimeConflict` then reports.


# 3. `Conflict`

A `Conflict` is local to the one hypothetical arrangement a question asked about. 
It names the `conflicting_employee` and `conflicting_task` that clash, and comes in two kinds:

- `SkillConflict` carries nothing further:
  the employee's skill level either reaches what the task requires or it doesn't. 
  It is reported only when *every* pairing an operator offers is blocked: 
  one skill-feasible pairing left open is an arrangement the model can still search.
- `TimeConflict` carries the squeeze. 
  The route upstream of the conflicting task cannot get the employee there before
  `earliest_upstream_feasible_start_time_of_conflicting_task`, 
  while the route downstream has to be left by `latest_downstream_feasible_start_time_of_conflicting_task`; 
  the conflict is what separates the two. 
  `is_upstream_feasible`/`is_downstream_feasible` say whether each side could accommodate the task on its own, 
  and each binding step index points at the step, on its own side.

`ConflictExtractor` raises `UnattributableFeasibilityShortfallException` when a solved shortfall isn't one
any single position accounts for. That happens because the conflicting task's slack variables relax the
time-sequence constraints on either side of it, and those constraints are also what keeps the rest of the
formulation honest about ordering: the solver can then pay shortfall to satisfy a restriction the route
order contradicts, or leave the conflicting task on a cycle disconnected from the route. The shortfall is
real, but it measures the contradiction rather than a gap the task has to be squeezed into.


# 4. Parity between the two pipelines

`tests/explaining/computing/test_parity.py` (one curated case per template) and `test_parity_random.py`
(random samples per template) run both pipelines on the same question and compare them.

The neighborhood pipeline's feasibility gap is asserted at or below the tailored pipeline's, not equal to it: 
the tailored pipeline's local search bounds each candidate position using the original sequence's precomputed slack, 
which goes stale once the relative order actually changes, 
whereas the MILP jointly re-optimizes every affected task's time. 
The two `Conflict`s are compared field for field only once the two gaps are known to be equal 
— a strictly smaller neighborhood gap means the pipelines landed on different arrangements, 
which have no reason to agree beyond neither of them fitting.
