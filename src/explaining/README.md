# Description of the `explaining` module

This module implements the generation of explanations about WSRP solutions. \
Given a solution and a question about it,
it builds a support solution answering that question and turns it into a human-readable explanation,
either through a web interface or a terminal interface.


# 1. Overview of the explanation pipeline

## 1.1. Tailored computation pipeline

A `Solution` is wrapped into an `Explainer` (from `interacting`), 
which orchestrates the pipeline for each question asked about it:
- a `PredefinedQuestion` is built from `question`'s template bank;
- `computing/templates` applies the tailored transformation corresponding to that question to the solution/instance, 
and returns a support solution together with feasibility information;
- `explanation` turns that result into a typed `Explanation`;
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

`question` contains the question layer, split by the kind of question asked. \
`question.py`'s abstract `Question` is what both kinds have in common: 
the solution asked about, the text read by the end user, and the language that text is phrased in. \
Its `predefined` subdirectory holds the template-based kind: 
the `PredefinedQuestion` class and its subclasses 
(`ContrastiveQuestion`, `ScenarioQuestion`, `CounterfactualQuestion`), 
each parameterized by a `QuestionTemplate`, 
with `predefined/bank.py` instantiating every template (in English and French) 
into the `QUESTIONS_TEMPLATES` dictionary — the "why not" question catalogue. \
Its `free` subdirectory holds the other kind, `FreeTextQuestion`: 
a question the end user phrased themselves, which `neighborhood/llm`'s `Extractor` takes as its input. \
(see its own [`README.md`](question/README.md) for a description of its files.)

`neighborhood` contains a vocabulary for describing a search space around a solution: 
`Neighborhood` i.e. the employees and tasks in scope, together with 
the `Operator`s that may transform their sequences 
and the `Restriction`s that narrow how (scope restrictions). \
Its `templates` subdirectory's `Mapper` translates a `ContrastiveQuestion` into the `Neighborhood` it induces, 
and its `TemplateComplianceChecker` recognizes the shapes that translation produces. \
(see its own [`README.md`](neighborhood/README.md) for a description of its files.)

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
Its outputs (support solution, conflict, instance alterations) feed directly into `explanation`. \
(see its own [`README.md`](computing/README.md) for a description of its files.)

`explanation` turns a `Question` and the result of `computing/templates` into a human-facing `Explanation`, 
mirroring `question`'s split by the kind of question answered. \
`explanation.py`'s abstract `Explanation` is what both kinds have in common: 
the question answered, the support solution backing the answer, the alterations it needed, and the resulting text. \
Its `predefined` subdirectory holds the template-based kind, `PredefinedExplanation`, 
which words every sentence from the `ExplanationTemplate` matching the question's own template: 
`create_explanation(...)` selects the appropriate subclass (`PositiveExplanation`, `NonImprovingNegativeExplanation`, 
`SkillNegativeExplanation`, `TimeNegativeExplanation`) 
depending on whether the support solution improves on the original solution
and whether a conflict was found. \
Its `free` subdirectory is the still-empty slot for answering a `FreeTextQuestion`: 
the neighborhood pipeline currently gets there by having `Recognizer` recover a `ContrastiveQuestion` 
from the `Neighborhood`, so that the template-based wording above still applies. \
(see its own [`README.md`](explanation/README.md) for a description of its files.)

`exporting` contains the scripts used for serializing `Explanation` objects to JSON files,
both for caching purposes and for the batch analysis triggered from `__main__.py`. \
`importing` contains the scripts used for the inverse operation, 
reconstructing `Explanation` objects from previously exported JSON files.

`interacting` contains the orchestration and user interface layer, centered on the `Explainer` class. \
`Explainer` owns the root `EditableSolution`, an optional `History` of visited instances/solutions,
and the methods tying `question`, `computing` and `explanation` together, 
optionally short-circuiting via the `importing`/`exporting` caches. \
`get_explanation` takes a question of either kind and picks the pipeline answering it: 
a `ContrastiveQuestion` goes to `computing/templates`, 
a `FreeTextQuestion` to `neighborhood/llm`'s `Extractor` and then `computing/neighborhood`, 
while `compute_scenario_explanation` and `compute_counterfactual_explanation` ask the two kinds of follow-up. \
`interface` holds the ways an end user reaches that `Explainer`. \
WIP: Today the Dash-based `ExplainerWebGUI` alone, with a terminal one planned beside it. \
(see its own [`README.md`](interacting/README.md) for a description of its files.)
