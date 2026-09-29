# Description of the `explanation` module

This module is the last stage of the explaining chain: 
it turns a `Question` and the `TransformationResult` computed to answer it into text the end user reads. \
It mirrors `question`'s split by the kind of question answered, 
since how an answer is worded depends entirely on what was asked.


# 1. Overview

`explanation.py` contains the abstract `Explanation`, which holds what every explanation has, 
whichever pipeline produced it: the `question` answered, the `support_solution` found while answering it, 
the instance alterations that solution needed, and the resulting `text`. \
It also implements the parts of the wording that read none of those templates — 
the language accessors, how to name a route's steps (`_activity`/`_activities`, which widen from "task" to "activity" 
on an instance with employee unavailabilities), the clause introducing instance alterations, 
and the two KPI comparison sentences. \
`is_positive`, `is_negative`, `support_solution_is_feasible`, `_compute_text` and `to_dict` are abstract.

Note that `Explanation.__init__` ends by computing the text. \
A subclass adding state the wording reads must therefore set it *before* delegating upwards — 
which is what `PredefinedExplanation` does with its typical expressions, 
and `InfeasibleNegativeExplanation` with its conflict.

`predefined` holds the template-based branch. `free` is the slot for the free-text one, and is still empty.


# 2. Description of the files

`explanation.py` contains `Explanation`, described above.

In `predefined` subpackage:

`template.py` contains `ExplanationTemplate`: the typical expressions answering one question template, 
per supported language. \
The expression ids are `the_fact` (what the current solution does), `the_foil` (what the end user expected), 
`having_the_foil`, and then either `applying_the_foil_transformation` for the single-target `*,1` templates 
or `neighbors` for the `*,2`/`*,3` families, which range over a set of neighboring solutions instead.

`bank.py` instantiates one `ExplanationTemplate` per question template into `EXPLANATIONS_TEMPLATES`, 
keyed by the **question** template's id — that shared key is the whole link between the two banks.

`explanation.py` contains `PredefinedExplanation` and the subclass tree below it. \
Its `__init__` splices the question's field values into the matching `ExplanationTemplate`'s expressions, 
which every sentence the subclasses build is then assembled from. \
`create_explanation(question, result)` picks the subclass the result calls for:
- `PositiveExplanation` when no conflict was found and the support solution improves on the current one;
- `NonImprovingNegativeExplanation` when no conflict was found but it does not improve on it;
- `SkillNegativeExplanation` / `TimeNegativeExplanation` when a `SkillConflict` / `TimeConflict` was found. \

`InfeasibleNegativeExplanation` is their common abstract parent, holding the conflict, 
and `NegativeExplanation` is the abstract parent of every negative one. \
`create_explanation_from_dict(dictionary, solution)` rebuilds one from a previously exported JSON payload.

In `free` subpackage:

Still empty. \
Answering a free-text question in words is not implemented: 
the neighborhood pipeline reaches the wording above by having `neighborhood/templates`' `Recognizer` 
recover a `ContrastiveQuestion` from the `Neighborhood`, 
so a neighborhood outside the question catalogue gets a support solution and a conflict but no text.


# 3. Serialization

`Explanation.to_dict` and `create_explanation_from_dict` write and read four literal keys: 
`'question'`, `'support solution'`, `'transformation'` and `'infeasibility'`. \
They are the keys of the explanation files already stored under `data/*/explanations/`, 
so renaming the classes must never change them — 
which is why `'infeasibility'` survived `Infeasibility` being renamed to `Conflict`.


### Next steps:
`'transformation'` exists in two incompatible shapes across the stored files: 
a plain already-resolved string in `data/demo/`, and the language-keyed dictionary `to_dict` writes today 
in `data/evaluation/`. Importing an old-format file builds an explanation whose descriptions are a `str`, 
which then raises `TypeError` on any read of `applying_support_solution_transformation`.
