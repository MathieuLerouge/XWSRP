# Description of the `computing` module

This module is the computational core that answers a question by attempting to modify the solution. \
Whatever the route taken, it produces the same `TransformationResult`: 
a support `Solution` (the arrangement the question asked about, whether or not it works), 
a `Conflict` saying why when it doesn't work, and the sentence describing what was done. \
That result feeds directly into `explanation`.


# 1. Overview

There are two independent pipelines: the tailored and the neighborhood pipelines.
They are implemented in their respective packages: `templates` and `neighborhood`.
A third package, `bridge`, connects them: 
it lets the template-based explanation layer phrase what the neighborhood pipeline computed.

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

The **neighborhood pipeline** (`neighborhood`) is the generic alternative. 
`NeighborhoodModel` turns any `Neighborhood` into one MILP, rather than having a handwritten function per template. 
It reports a feasibility shortfall: 0 when the requested arrangement fits, 
otherwise how much the conflicting task's start time has to be stretched for it to. \
Once solved, the `ExplanationFactsBuilder` reads off it the `ExplanationFacts`.
These `ExplanationFacts` will be then worded into text by `ExplanationWriter` (in `explanation.free`), 
whatever the neighborhood and whether or not it belongs to the question catalogue.

The **bridge** (`bridge`) is what lets the neighborhood pipeline reach `explanation` the way the tailored one does, 
through `result.py`'s `build_transformation_result_from_neighborhood`. \
The step that costs it something the tailored pipeline gets for free is the question: 
a predefined explanation is phrased from a question template's typical expressions, 
and a `Neighborhood` on its own carries no template. \
`explaining.neighborhood.templates`' `Recognizer` recovers one by reading the neighborhood's own primitives, 
and `description.py` words what the solved model settled on in that template's terms. \
It is not only there to compare the two pipelines (see section 4): 
`Explainer` goes through it whenever templated questions are computed in neighborhood mode, 
and for free-text questions until they are answered through `ExplanationWriter`.

Only the tailored pipeline handles counterfactual questions today; 
`NeighborhoodModel` covers the contrastive/scenario ones.


# 2. Description of the files

The module is laid out by which pipeline a file serves: 
`templates` for the tailored one, 
`neighborhood` for the generic one, 
`bridge` for what connects the latter to the former's explanation layer, 
and at the top level the three files both of them need.

Shared by both pipelines:
- `conflict.py` contains `Conflict` and its two subclasses, `SkillConflict` and `TimeConflict`. 
  It is what either pipeline hands to `explanation`.
- `solver.py` contains `TransformationModelSolver`, which solves either pipeline's MILP models 
  and turns an outcome holding no usable solution into the matching exception.
- `exceptions.py` contains `ImpossibleTransformationException`, 
  raised when a question asks for something the given solution makes meaningless 
  (e.g. inserting a non-performed task when every task is already performed). 
  Both pipelines raise it: the tailored one from `templates/common/preconditions.py`, 
  the generic one from `explaining.neighborhood`'s own question mappers.

In `neighborhood` subpackage:
- `model.py` contains `NeighborhoodModel`, described above.
- `checker.py` contains `ModelCompatibilityChecker`, which tells 
  which neighborhoods can be built for `NeighborhoodModel`  and why not when it can't.
- `extractor.py` contains `ConflictExtractor`, which maps a `Neighborhood` to a `SkillConflict`
  and a solved `NeighborhoodModel` to a `TimeConflict`.
- `solving.py` contains `solve_neighborhood`, the template-free run up to the solved model 
  (or the skill conflict blocking it before any model is built), 
  and `reorder_support_sequences_to_solved_routes`.
- `facts.py` contains `ExplanationFactsBuilder`, which reads off a solved neighborhood, without any template, 
  the `ExplanationFacts` an explanation may state: the `ExplanationOutcomes` (decided here, never by an LLM, 
  with "positive" meaning a feasible support solution better than the current one, as in the predefined branch), 
  the conflict with its step indices resolved into named activities and times, the route changes and the KPIs. 
  They name things rather than hold them, so they serialize as is.
- `exceptions.py` contains `UnattributableFeasibilityShortfallException`.

In `bridge` subpackage:
- `result.py` contains `solve_neighborhood_into_transformation_result` 
  and `build_transformation_result_from_neighborhood`, 
  the bridge's counterpart to `templates`' `build_transformation_result_from_milp_model`: 
  it recognizes the question template a neighborhood stands for, and builds its `TransformationResult`.
- `description.py` contains `NeighborhoodDescriptionBuilder`, which words what the solved model settled on, 
  reusing `templates/common/description.py`'s `TransformationDescriptionBuilder` sentences.

In `templates` subpackage:
- `dispatch.py` contains `TransformationDispatcher`, 
  which hands a `PredefinedQuestion` to the transformation its template calls for. 
  Three tables hold that mapping: the contrastive ones are split by how they are computed, 
  since only the MILP-based three take a solving time limit, and the counterfactual ones share a single table.
- `common` holds what both kinds share: `TransformationPreconditionChecker`, `TransformationDescriptionBuilder`,
  `TransformationResult` (the support solution, the conflict if any, the per-language descriptions, and
  the instance alterations for counterfactual questions), and `TailoredConflictBuilder`.
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

`tests/explaining/computing/bridge/test_parity.py` (one curated case per template) and `test_parity_random.py`
(random samples per template) run both pipelines on the same question and compare them.

The neighborhood pipeline's feasibility gap is asserted at or below the tailored pipeline's, not equal to it: 
the tailored pipeline's local search bounds each candidate position using the original sequence's precomputed slack, 
which goes stale once the relative order actually changes, 
whereas the MILP jointly re-optimizes every affected task's time. 
The two `Conflict`s are compared field for field only once the two gaps are known to be equal 
— a strictly smaller neighborhood gap means the pipelines landed on different arrangements, 
which have no reason to agree beyond neither of them fitting.

`test_explanation_parity.py` carries the same comparison one step further, 
to the `descriptions` and to the `Explanation.text` built from them. \
It asserts them equal for the `(Ins,*)` and `(Ord,*)` templates only 
— the ones `test_parity.py` asserts identical KPIs for. \
The `(Swp,*)` family is left out on purpose: its two pipelines legitimately swap different tasks. \
For that family the test only asserts that both pipelines do produce a description and a text.

One shape the neighborhood pipeline reaches and the tailored one cannot:
`(Swp,2c)` offers every employee's performed tasks for removal and every employee as a destination, 
so the solver may take the outgoing task from one employee while handing the incoming one to another. 
No single-employee sentence covers that, 
which is what `TransformationDescriptionBuilder.for_replacing_task_of_another_employee` is for 
— the one description method the tailored pipeline never calls.

TODO: This last case should not occur.