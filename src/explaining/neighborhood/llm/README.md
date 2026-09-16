# Description of the `llm` module

This module is the free-text alternative to the `templates` subpackage: 
it turns a free-text contrastive question into the `Neighborhood` it induces, via a model-agnostic LLM,
by freely composing primitives rather than dispatching on the fixed `QuestionTemplate` catalogue.

`Extractor` (`extractor.py`) is the entry point: 
`Extractor(solution, model).extract(question_text)` returns the induced `Neighborhood`, 
or raises `NeighborhoodExtractionError` if the question can't be turned into one `NeighborhoodModel` can solve. 
It relies on the parent `neighborhood` package's `Assembler`/`NeighborhoodError` 
for the final assemble-and-capability-check step, shared with whatever else might build a `Neighborhood`.


# Description of the files

`primitive.py` contains `EmployeeName`/`TaskName`/`ActivityName` (raw-string name aliases) and `ExtractedPrimitive`, 
the common base for every extracted operator/restriction below 
— the raw-string counterpart of `neighborhood.primitive.Primitive`.

`operator.py` contains the raw-string counterparts of the `Operator` subclasses an extraction may pick: 
`ExtractedTaskInsertion`, `ExtractedTaskDeletion`, `ExtractedTaskRepositioning`, `ExtractedSequenceReordering` 
(no `ExtractedTaskRelocation` — `TaskRelocation` has no MILP formulation yet), 
plus `ExtractedFeasibilityShortfallOperator`, the union of the three an extraction's `operator` field may hold.

`restriction.py` contains the raw-string counterparts of the `Restriction` subclasses:
`ExtractedPrecedenceChain`, `ExtractedImmediatePrecedence`, `ExtractedPrecedence`, `ExtractedForbiddenSequence`, 
`ExtractedForbiddenBackwardSubsequence`, plus `ExtractedRestriction`, their union.

`neighborhood.py` contains `ExtractedNeighborhood`, the raw-string counterpart of `Neighborhood`:
one `operator`, an optional paired `deletion` (an `ExtractedTaskDeletion`), and zero or more `restrictions`.

`extraction_outcome.py` contains `ExtractionOutcome`, the actual top-level object an extraction returns: 
either a coverable question's `ExtractedNeighborhood`, or an explicit `coverable=False` admission with a `reason`, 
so the LLM has a way to say "this can't be expressed" instead of guessing.

`prompt.py` contains `SYSTEM_PROMPT` (the primitive vocabulary and worked examples the LLM is taught) 
and `build_user_prompt(solution, question_text)` (the prompt embedding the solution's own employee/task vocabulary).

`grounder.py` contains `Grounder`, which resolves an `ExtractedNeighborhood`'s raw names against a `Solution`
into actual `Operator`/`Restriction` domain objects.

`exceptions.py` contains `NeighborhoodExtractionError`, raised whenever a question can't be turned into a `Neighborhood`
that `NeighborhoodModel` can solve — a specialization of the parent package's `NeighborhoodError`.

`extractor.py` contains `Extractor`, tying the above together: builds the prompt, calls the LLM,
then grounds and assembles its output, turning every failure into `NeighborhoodExtractionError`.
