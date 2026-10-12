# Description of the `interacting` module

This module holds the orchestrator every question goes through, `Explainer`, and the interfaces that drive it.


# 1. Overview

`Explainer` (`explainer.py`) wraps one solution and answers questions asked about it. \
It owns the root `EditableSolution`, an optional `History` of the instances and solutions visited while questioning it, 
and the catalogue of question templates it accepts. \
Around the actual computation it adds the things a session needs and a pipeline does not:
which templates are activated, what language to answer in, how many times each question was asked,
a cache of explanations, and the last explanation of each kind so that a follow-up question can build on it.

It answers through either of the project's two pipelines, picking by the kind of question it is given:

- a **`ContrastiveQuestion`** goes to the tailored pipeline 
  — `computing/templates`' `TransformationDispatcher` dispatches on its template id;
- a **`FreeTextQuestion`** goes to the llm-neighborhood one 
  — `neighborhood/llm`'s `Extractor` turns the text into the `Neighborhood` it induces, 
  `computing/neighborhood`'s `solve_neighborhood` solves it, 
  and `explanation/free`'s `ExplanationWriter` has an LLM word the facts of the solution found (see section 3.2).

A contrastive question comes back as an `explanation/predefined` `Explanation`, 
a free-text one as an `explanation/free` `FreeTextExplanation` (or, in templated mode, as a predefined one too).


# 2. Description of the files

`explainer.py` contains `Explainer`, described above and detailed in section 3.

`configuration.py` contains `ExplainerConfiguration`, 
the construction-time settings `Explainer` is built from, detailed in section 3.4.

`history.py` contains `History`, a store of the instances and the solutions of each, keyed by name. \
It is what lets an end user alter an instance, keep the solution that came out of it, and navigate back. \
`Explainer` is its only user, and exposes it directly through `explainer.history` (e.g.
`explainer.history.solutions_names`) rather than re-exposing its methods one by one.

In `interface` subpackage:

`web` contains the Dash application: `app.py`'s `ExplainerWebGUI` builds the layout and every callback,
`figures.py` the map, route and schedule plots, `panels.py` the panels assembling those into the page,
`tables.py` the employees and tasks data tables, `tools.py` a text-to-html helper, 
and `assets` the stylesheets, logos and the `styles.py` module holding the colours the figures and tables share. \
NB: `ExplainerWebGUI` resolves `assets` relative to `app.py`'s own location, so the two move together;
a lost `assets` directory does not raise, it just serves an unstyled page.

WIP: A terminal interface is planned beside `web`, and is not implemented yet.


# 3. `Explainer`

## 3.1. Asking

`get_explanation(question)` is the entry point taking a question object, of either kind. \
`get_contrastive_explanation(question_template_id, fields_values)` builds the predefined question first,
and `get_free_text_explanation(question_text)` the free-text one, both then delegating to it.

A `ScenarioQuestion` and a `CounterfactualQuestion` are follow-ups rather than questions asked from scratch: 
each derives from the last contrastive question and needs its own kind of explanation enabled,
so each has its own entry point, `compute_scenario_explanation` and `compute_counterfactual_explanation`. \
`get_explanation` refuses them, naming the method that does ask them.

## 3.2. Answering a free-text question

The free-text route needs two LLM backends, which may be the same model: 
an `extractor_model` turning the question into a neighborhood (`main_configuration.EXTRACTOR_MODEL`) 
and a `writer_model` wording the explanation (`main_configuration.WRITER_MODEL`), 
both in the format `instructor.from_provider` expects and held in its `ExplainerConfiguration`. They default to None: 
both the `Extractor` and the `ExplanationWriter` are built on first use rather than in the constructor, 
so that asking predefined questions needs neither the `instructor` package nor any backend running. \
Both are checked before any LLM is called, so a missing model fails before anything is spent. \
The `Extractor` grounds names against one solution and refuses a question asked about another, 
so it is rebuilt whenever the solution being questioned changes; the writer is bound to no solution.

How the explanation is worded depends on the configuration's `free_text_explanation_mode`:
- `written` (the default): `ExplanationFactsBuilder` reads the facts off the solved neighborhood 
  and the `ExplanationWriter` has the LLM word them into a `FreeTextExplanation`, 
  whatever the neighborhood, in or out of the question template catalogue;
- `templated`: for when free-text questions are known to be the equivalents of question templates. 
  `computing/bridge`'s `solve_neighborhood_into_transformation_result` recognizes the template from the neighborhood, 
  and the predefined explanation of that template is phrased, not the end user's own words. 
  A question whose neighborhood no template matches then cannot be answered at all, and `Explainer` raises.

## 3.3. Caching and export

A predefined explanation can be served from memory, or imported from a JSON file in the inputs directory,
before being computed. 
Both are keyed by template id and field values, which is also how `exporting/explanation.py` names the files. \
A free-text explanation has neither, so free-text answers are not cached.

A templated one carries the `ContrastiveQuestion` recognized from it, 
so scenario and counterfactual follow-ups can build on it; 
a written one carries no question template, so they are refused, saying so.

## 3.4. Configuration

`configuration.py`'s `ExplainerConfiguration` holds every construction-time setting `Explainer` is built from: 
language, extractor and writer models, the free-text explanation mode, which question templates are activated, 
the history/scenario/counterfactual/reuse-cached/auto-export toggles, 
the contrastive explanation input/output directories, and the two MILP time limits. \
Two `@classmethod` presets cover the two configurations every construction site actually needs:
`ExplainerConfiguration.batch(...)` (history, scenario, counterfactual and automatic export all off) 
and `ExplainerConfiguration.web_ui(...)` (those three on by default).


# 4. Launching an interface

`ExplainerWebGUI(explainer).launch()` serves the Dash application, from four places:

- `processes.py`'s `launch_explainer_UI_on_demo_solution` and `launch_explainer_UI_on_default_solution`,
  reached from `__main__.py` through `main_configuration.py`, and from `processes.py`'s own `__main__` block;
- `evaluation/processes.py` and `evaluation/user_interface_with_prepared_data.py`, for an evaluation experiment.

Deployment does not call `launch()`. `evaluation/deployed_application.py` reaches through
`ExplainerWebGUI.application.server` for gunicorn to serve, as the `Procfile` at the root spells out —
so `application` is as much a part of the public contract as `launch()` is.
