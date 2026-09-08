# Description of the `explaining` module

This module implements the generation of explanations about WSRP solutions. \
Given a solution and a question about it (e.g. "why was task X not assigned to employee Y?"),
it builds a support solution answering that question and turns it into a human-readable explanation,
either through a web interface, a terminal interface, or as part of a batch analysis.


# 1. Overview of the explanation pipeline

The `__main__.py` script is the entry point of the module. \
Depending on the value of `MAIN_PROCESS`/`MAIN_PROCESS_AMONG_EXPLAINER_ONES` in `main_configuration.py`,
it either launches the `ExplainerWebGUI` on a demo or a default solution,
or runs a batch analysis computing the computation time of explanations
over every solution found in the default inputs directory.

In both cases, a `Solution` (read from the `instances`/`solutions` data) is wrapped into an `Explainer`
(from `interacting`), which orchestrates the rest of the pipeline for each question asked of it:
- a `Question` is built from `questioning`'s template bank;
- `transforming` applies the transformation induced by that question to an editable copy
of the solution/instance (defined in `modeling`), and returns a support solution together
with feasibility information;
- `answering` turns that result into a typed `Explanation`;
- `writing`/`reading` (de)serialize `Explanation` objects to/from JSON, so that previously
computed explanations can be reused instead of recomputed;
- `interacting` (terminal or web UI) presents the final explanation, and any supporting figures, to the user.


# 2. Description of the subdirectories

The directory `instances` contains the Excel files (`InstanceAustria.xlsx`, `InstanceBordeaux.xlsx`,
`InstanceUkraine.xlsx`, `instancePoland.xlsx`) defining the demo WSRP instances. \
The directory `solutions` contains the corresponding pre-computed solutions, as `.txt` files.

The directory `modeling` contains editable mirror classes of the core domain model
(`EditableInstance`, `EditableSolution`, `EditableEmployee`, `EditableSequence`, `EditableTask`),
along with `InstanceChanges`, which tracks the alterations applied to an instance. \
These classes let transformations be applied to a hypothetical copy of a solution/instance
without mutating the original one, and are used throughout `transforming`, `answering` and `interacting`.

The directory `questioning` contains the question layer: the `Question` base class and its subclasses
(`ContrastiveQuestion`, `ScenarioQuestion`, `CounterfactualQuestion`), each parameterized by a
`QuestionTemplate`. \
`questions_templates_bank.py` instantiates every template (in English and French) into the
`QUESTIONS_TEMPLATES` dictionary, which is the "why not" question catalogue used by `interacting`
and mapped to transformation functions in `transforming`.

The directory `transforming` contains the computational core that answers a question by attempting
to modify the solution. \
`transformation.py` dispatches each question template to a dedicated transformation function,
implemented in one of two subpackages: `contrastive_and_scenario` (local-search-based single-move
insertions/swaps/reorderings, with an ILP-based fallback for harder cases) and `counterfactual`
(ILP-based search for minimal instance alterations that would make the requested action feasible,
gated behind Gurobi availability). \
Its outputs (support solution, infeasibility, instance alterations) feed directly into `answering`.

The directory `answering` turns a `Question` and the result of `transforming` into a human-facing
`Explanation`. \
`create_explanation(...)` selects the appropriate subclass (`PositiveExplanation`,
`NonImprovingNegativeExplanation`, `InfeasibleNegativeExplanation`, `SkillNegativeExplanation`,
`TimeNegativeExplanation`) depending on whether the support solution improves on the original solution
and whether an infeasibility was raised, and builds its text from `explanations_templates_bank.py`.

The directory `writing` contains the scripts used for serializing `Explanation` objects to JSON files,
both for caching purposes and for the batch analysis triggered from `__main__.py`. \
The directory `reading` contains the scripts used for the inverse operation, reconstructing
`Explanation` objects from previously exported JSON files.

The directory `interacting` contains the orchestration and user interface layer, centered on the
`Explainer` class. \
`Explainer` owns the root `EditableSolution`, an optional `History` of visited instances/solutions,
and the methods (`get_contrastive_explanation`, `compute_scenario_explanation`,
`compute_counterfactual_explanation`) tying `questioning`, `transforming` and `answering` together,
optionally short-circuiting via the `reading`/`writing` caches. \
`explainer_terminal.py` provides a terminal interaction mode, while `interface` implements the
Dash-based `ExplainerWebGUI` used by end users.
