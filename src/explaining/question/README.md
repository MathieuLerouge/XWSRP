# Description of the `question` module

This module is the question layer: what an end user asks about a solution, before anything is computed to answer it.
It is split by the kind of question asked:
- a **predefined** one is picked from a fixed catalogue and parameterized by filling a template's fields in,
which is what lets `computing/templates` know which transformation answers it 
and `explanation/predefined` know which words to answer it with;
- a **free-text** one is phrased by the end user themselves, carries no template, 
and is turned into something computable by `neighborhood/llm`'s `Extractor` instead.


# 1. Overview

`question.py` contains the abstract `Question`, which is all the two kinds genuinely share: 
the `solution` asked about, the `text` the end user reads, and the `language` that text is phrased in. \
`text` and the language accessors are abstract, since that is exactly where the two kinds diverge: 
a predefined question derives its text from a template and rephrases itself when the language changes, 
whereas a free-text one is given its text once and only records which language it is in.

Nothing else is hoisted there on purpose. \
A template, its field values, and the `to_dict`/`from_dict` pair built on them 
belong to the predefined branch alone.


# 2. Description of the files

`question.py` contains `Question`, described above.

In `predefined` subpackage:

`constants.py` contains the sixteen question template ids (`WHY_NOT_INS_1`, …, `WHY_NOT_ORD_3`). \
These strings are the key everything else is indexed by: `QUESTIONS_TEMPLATES`, 
`explanation/predefined`'s `EXPLANATIONS_TEMPLATES`, `computing/templates`' dispatch tables, 
`neighborhood/templates`' `Mapper`/`Recognizer`, and the stored explanation JSON files under `data/`.

`template_field.py` contains `FieldAssumptions`, which parses the marker string declaring what a template field 
may refer to (an employee, a task, an activity, and the narrowing conditions on it), 
plus the consistency checks between a template's text and its declared fields.

`template.py` contains `QuestionTemplate`: a sentence per supported language with `{Field}` placeholders, 
the `FieldAssumptions` of each, and the machinery around them — 
`complete_text_with_fields_values` to fill the sentence in, 
`compute_field_valid_values`/`compute_all_fields_valid_values` to tell the UI what may go in each field, 
and `check_fields_values_validity` to reject a combination the assumptions forbid.

`bank.py` instantiates every template (in English and French) into the `QUESTIONS_TEMPLATES` dictionary, 
the "why not" question catalogue itself. \
It also holds the two category lists the rest of the code asks about: 
`MILP_BASED_COMPUTATION_QUESTIONS_TEMPLATES_IDS` and 
`BASED_ON_MOST_RELEVANT_NEIGHBORING_SOLUTION_QUESTIONS_TEMPLATES_IDS`. \
NB: the templates are module-level singletons, so setting a question's language mutates the shared template.

`question.py` contains `PredefinedQuestion` and its three subclasses: 
`ContrastiveQuestion` ("why not this instead?"), 
`ScenarioQuestion` (the same contrastive question asked again about an altered instance), 
and `CounterfactualQuestion` (the same one turned around: which alterations would make it possible?). \
The latter two wrap the contrastive question they derive from rather than subclassing it, 
so the three remain mutually exclusive under `isinstance` — which is what `explanation/predefined` relies on.

In `free` subpackage:

`question.py` contains `FreeTextQuestion`: the solution asked about, the text as typed, and its language. \
Setting its language only records which language the text is in — it does not translate it — 
so that the explanation answering it can be phrased in the same one. \
It is what `neighborhood/llm`'s `Extractor` takes as its input.


### Next steps:
`FreeTextQuestion` has no `to_dict`/`from_dict`: free-text explanations are not serialized yet, 
and there is nothing to store a format for until `explanation/free` exists.
