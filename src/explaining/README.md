# Description of the `explaining` module

This module implements the generation of explanations about WSRP solutions. \
Given a solution and a question about it,
it builds a support solution answering that question and turns it into a human-readable explanation,
either through a web interface or a terminal interface.


# 1. Overview of the explanation pipeline

## 1.1. Tailored computation pipeline

A `Solution` is wrapped into an `Explainer` (from `interacting`), 
which orchestrates the pipeline for each question asked about it:
- a `Question` is built from `questioning`'s template bank;
- `computing/templates` applies the tailored transformation corresponding to that question to the solution/instance, 
and returns a support solution together with feasibility information;
- `answering` turns that result into a typed `Explanation`;
- `exporting`/`importing` (de)serialize `Explanation` objects to/from JSON, 
so that previously computed explanations can be reused instead of recomputed;
- `interacting` (terminal or web UI) presents the final explanation, and any supporting figures, to the user.

NB: Before applying its transformation, `computing/templates` wraps the `Solution`/`Instance` being questioned 
into `modeling`'s editable mirror classes (`EditableSolution.from_Solution`, `EditableInstance.from_Instance`, 
and so on down to `EditableSequence`/`EditableEmployee`/`EditableTask`). \
The transformation is then applied to that editable copy rather than to the original. \
For a counterfactual question, where the transformation also alters instance parameters, 
each alteration is also recorded in an `InstanceChanges`.

## 1.2. Neighborhood-based computation pipeline

An alternative to the tailored pipeline, covering the `(Ins,*)`, `(Swp,*)` and `(Ord,*)` contrastive question families.
For a `ContrastiveQuestion`, `neighborhood/templates`'s `Mapper` maps it to a `Neighborhood`.
Then, if `computing/neighborhood/extractor.py`'s `ConflictExtractor` 
identifies a `SkillConflict` from the `Neighborhood`,
this conflict will be used as a basis for explanations;
Otherwise, `computing/neighborhood/model.py`'s `NeighborhoodModel` turns the `Neighborhood` into a solvable MILP
(in place of `computing/templates`' per-template transformation function),
whose solve results are used by the `ConflictExtractor` to identify a `TimeConflict` (if any).

NB: The neighborhood pipeline is able to accept inputs the tailored one doesn't handle 
(e.g. a candidate task that happens to already be performed by someone else). 
What parity tests check is that every question the tailored pipeline can answer, 
the neighborhood pipeline can also answer it and gets the same (or a strictly better-fitting) support solution.

### Next steps: 
`TaskRelocation` still exists only as vocabulary, with no MILP formulation.


# 2. Description of the subdirectories

`instances` contains the Excel files defining the demo WSRP instances. \
`solutions` contains the corresponding pre-computed solutions, as `.txt` files.

`modeling` contains editable mirror classes of the core domain model
(`EditableInstance`, `EditableSolution`, `EditableEmployee`, `EditableSequence`, `EditableTask`),
along with `InstanceChanges`, which tracks the alterations applied to an instance.

`questioning` contains the question layer: 
the `Question` base class and its subclasses (`ContrastiveQuestion`, `ScenarioQuestion`, `CounterfactualQuestion`), 
each parameterized by a `QuestionTemplate`. \
`questions_templates_bank.py` instantiates every template (in English and French) 
into the `QUESTIONS_TEMPLATES` dictionary, 
which is the "why not" question catalogue used by `interacting`
and mapped to transformation functions in `computing/templates`.

`neighborhood` contains a vocabulary for describing a search space around a solution: 
`Neighborhood` i.e. the employees and tasks in scope, together with 
the `Operator`s that may transform their sequences 
and the `Restriction`s that narrow how (scope restrictions). \
Its `templates` subdirectory's `Mapper` translates a `ContrastiveQuestion` into the `Neighborhood` it induces, 
and its `TemplateComplianceChecker` recognizes the shapes that translation produces.

`computing` contains the computational core that answers a question by attempting to modify the solution. 
Its `templates` subdirectory dispatches each question template to a dedicated transformation function, 
implemented in one of two subpackages: 
- `contrastive_and_scenario` (local-search-based insertions/swaps/reorderings, 
with an ILP-based fallback for harder cases);
- and `counterfactual` (MILP-based search for minimal instance alterations making the requested action feasible). \
`model.py`'s `NeighborhoodModel` offers a generic alternative, 
turning a `Neighborhood` into a solvable MILP instead of a per-template transformation function, 
with `checker.py`'s `ModelCompatibilityChecker` saying which `Neighborhood`s it can be built for 
and `conflict`'s `ConflictExtractor` turning a solved one into the same `Conflict` the tailored pipeline returns. \
Its outputs (support solution, conflict, instance alterations) feed directly into `answering`.

`answering` turns a `Question` and the result of `computing/templates` into a human-facing `Explanation`. \
`create_explanation(...)` selects the appropriate subclass (`PositiveExplanation`, `NonImprovingNegativeExplanation`, 
`InfeasibleNegativeExplanation`, `SkillNegativeExplanation`, `TimeNegativeExplanation`) 
depending on whether the support solution improves on the original solution
and whether a conflict was found, and builds its text from `explanations_templates_bank.py`.

`exporting` contains the scripts used for serializing `Explanation` objects to JSON files,
both for caching purposes and for the batch analysis triggered from `__main__.py`. \
`importing` contains the scripts used for the inverse operation, 
reconstructing `Explanation` objects from previously exported JSON files.

`interacting` contains the orchestration and user interface layer, centered on the `Explainer` class. \
`Explainer` owns the root `EditableSolution`, an optional `History` of visited instances/solutions,
and the methods (`get_contrastive_explanation`, `compute_scenario_explanation`, `compute_counterfactual_explanation`) 
tying `questioning`, `computing/templates` and `answering` together, 
optionally short-circuiting via the `importing`/`exporting` caches. \
`explainer_terminal.py` provides a terminal interaction mode, 
while `interface` implements the Dash-based `ExplainerWebGUI` used by end users.
