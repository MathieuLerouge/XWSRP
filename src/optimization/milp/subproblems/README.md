# Description of the `subproblems` module

This module implements a family of MILP models that each optimize a single employee's sequence of
activities — as opposed to `MILPModel` (one level up), which optimizes every employee at once. \
Each subproblem answers a narrower question about that one sequence: can a task be added to it, what
would need to change to fit it, is a given task set at least feasible, can a fixed subset of tasks be
combined with optional ones, or can the same tasks be reordered to do better.


# 1. Overview of the sequence sub-models

`SequenceModel` (`sequencemodel.py`) is the base class: given an `Instance`, an `Employee` and a list of
candidate tasks, it builds the MILP deciding which of those candidate tasks the employee performs and in
what order (`T` start-time and `U` sequencing decision variables, covering/flow/time-window/sequence-time
constraints), maximizing working duration net of traveling duration.

Every other file in this module defines one subclass of `SequenceModel`, overriding whichever of the
decision-variables/objective/constraints hooks its specific question requires. \
`SequenceInsertingModel`, `SequencePrescribingModel` and `SequenceReorderingModel` can be used as 
repair/improvement moves during heuristic search.

`SequenceModel` itself can also be subclassed to compute the support solutions
behind counterfactual and contrastive explanations.


# 2. Description of the files

`sequencemodel.py` contains `SequenceModel`, described above.

`sequenceaddingmodel.py` contains `SequenceAddingModel(SequenceModel)`, which fits one new task into an
existing sequence at its best position. \
It replaces the new task's single start-time variable with a split backward/forward pair
(`var_T_backward`/`var_T_forward`) bracketing the insertion point, and minimizes the resulting time gap
between them plus the traveling duration.

`sequencealteringmodel.py` contains `SequenceAlteringModel(SequenceModel)`, which extends the same idea
with the ability to relax instance parameters — task and employee time windows, task durations — when the
new task doesn't fit otherwise. \
Each relaxable bound has an activation/magnitude variable pair (e.g. `vars_X_at`/`vars_Delta_at` for a
task's lower time-window bound), and the objective minimizes first the number of alterations used, then
their total magnitude.

`sequenceinsertingmodel.py` contains `SequenceInsertingModel(SequenceModel)`, which only tests whether one
new task can *optionally* be inserted into an existing sequence: the new task's covering constraint is
relaxed from `== 1` to `<= 1`, so the model stays feasible whether or not the task ends up covered — a
feasibility probe rather than a forced insertion.

`sequenceprescribingmodel.py` contains `SequencePrescribingModel(SequenceModel)`, which builds a sequence
out of two kinds of candidate tasks: a `prescribed_tasks` subset that must be covered (`== 1`), and the
remaining candidate tasks, which stay optional (`<= 1`).

`sequencereorderingmodel.py` contains `SequenceReorderingModel(SequenceModel)`, which keeps the exact same
set of tasks as a given `initial_sequence` and only looks for a better order for them, forced to differ
from that initial order by at least one arc via `_add_sequence_order_constraint`.
