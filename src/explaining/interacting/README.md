# Description of the `interacting` module

This module holds the orchestrator every question goes through, `Explainer`, and the interfaces that drive it.


# 1. Overview

`Explainer` (`explainer.py`) wraps one solution and answers questions asked about it. \
It owns the root `EditableSolution`, an optional `History` of the instances and solutions visited while questioning it, 
and the catalogue of question templates it accepts. \
Around the actual computation it adds the things a session needs and a pipeline does not:
which templates are activated, what language to answer in, how many times each question was asked,
a cache of already-computed explanations, and the last explanation of each kind 
so that a follow-up question can build on it.

It answers through either of the project's two pipelines, picking by the kind of question it is given:

- a **`ContrastiveQuestion`** goes to the tailored pipeline 
  — `computing/templates`' `TransformationDispatcher` dispatches on its template id;
- a **`FreeTextQuestion`** goes to the llm-neighborhood one 
  — `neighborhood/llm`'s `Extractor` turns the text into the `Neighborhood` it induces, 
  and `computing/neighborhood`'s `solve_neighborhood_into_transformation_result` solves and describes it.

Either way the result reaches the same `explanation/predefined`'s `create_explanation`, 
so both kinds of question come back as the same kind of `Explanation`.


# 2. Description of the files

`explainer.py` contains `Explainer`, described above and detailed in section 3.

`history.py` contains `History`, a store of the instances and the solutions of each, keyed by name. \
It is what lets an end user alter an instance, keep the solution that came out of it, and navigate back. \
`Explainer` is its only user, and re-exposes most of it by delegation.

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

The free-text route needs an LLM backend, so `Explainer` takes an `extractor_model` string
(`main_configuration.EXTRACTOR_MODEL`, in the format `instructor.from_provider` expects). \
It defaults to None, and the `Extractor` is built on first use rather than in the constructor, 
so that asking predefined questions needs neither the `instructor` package nor any backend running. \
The `Extractor` grounds names against one solution and refuses a question asked about another, 
so it is rebuilt whenever the solution being questioned changes.

WIP: Two limits are worth knowing before relying on this route.

- The explanation is phrased from the template of the question the neighborhood is recognized as, 
  not from the end user's own words.
  `neighborhood/templates`' `Recognizer` recovers a `ContrastiveQuestion` from the neighborhood, 
  and that question's template supplies the wording. 
  The user's phrasing is not reproduced.
- And a question whose neighborhood no template matches cannot be answered at all.
  It is understood, its search space is solved, and a support solution and a conflict do exist 
  — but there is no template to phrase them from, so `Explainer` raises rather than returning a wordless explanation. Lifting this needs
  `explanation/free`, which is still an empty slot.

## 3.3. Caching and export

A predefined explanation can be served from memory, or imported from a JSON file in the inputs directory,
before being computed. 
Both are keyed by template id and field values, which is also how `exporting/explanation.py` names the files. \
A free-text explanation has neither, and `FreeTextQuestion` has no `to_dict`, 
so free-text answers are neither cached nor exported. 
They do become the last contrastive explanation, so scenario and counterfactual follow-ups can still build on them.


# 4. Launching an interface

`ExplainerWebGUI(explainer).launch()` serves the Dash application, from four places:

- `processes.py`'s `launch_explainer_UI_on_demo_solution` and `launch_explainer_UI_on_default_solution`,
  reached from `__main__.py` through `main_configuration.py`, and from `processes.py`'s own `__main__` block;
- `evaluation/processes.py` and `evaluation/user_interface_with_prepared_data.py`, for an evaluation experiment.

Deployment does not call `launch()`. `evaluation/deployed_application.py` reaches through
`ExplainerWebGUI.application.server` for gunicorn to serve, as the `Procfile` at the root spells out —
so `application` is as much a part of the public contract as `launch()` is.


### Next steps:
`Explainer` is configured by a long series of `enable_*`/`disable_*` calls made in much the same order by
each of its eight construction sites, which a configuration object would express better.
