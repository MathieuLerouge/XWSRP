# About `test_extractor_quality.py`

This file holds 17 real-model quality checks for `Extractor`: 
one free-text question per `(Ins,*)`/`(Swp,*)`/`(Ord,*)` questions, plus one deliberately uncoverable question 
(asking to relocate a task between two employees). 
Unlike the rest of the suite, these call a real LLM and are marked `llm` (see the root README and `pytest.ini`) 
— they need a running LLM backend and are non-deterministic by nature, 
so don't expect a clean stable pass rate the way you would from the rest of the suite.

Assertions check the operator/restriction *kinds* present and specific named entities, not full object equality, 
since the LLM may reasonably phrase equivalent candidate sets differently.


## Analysis so far

No provider API key has been available in this environment, 
so every run so far has used free local models via [Ollama](https://ollama.com/):
- **`llama3.2` (3B)**: low and unstable pass rate, around 4-5/17 across repeated runs. 
  Individual failures were genuine model misses (e.g. dropping a required restriction, 
  or incorrectly self-reporting a coverable question as not coverable), not test-authoring bugs.
- **`qwen2.5:7b`**: meaningfully better, but still only around 9-11/17, fluctuating run to run.

Possible failures:
- The neighborhood extraction of `(Ord,*)` questions tends to pick `task_insertion` instead of `task_repositioning`.
- Not distinguishing `Precedence` from `PrecedenceChain` for `(Ord,2a)`/`(Ord,2b)`:
  — the model sometimes freezes the whole order (`PrecedenceChain`) instead of also adding the `Precedence`
  that actually allows the task to shift.
- With `(Ord,2c)`'s "at any other stage" phrasing, the model may not use `ForbiddenSequence`, 
  but a precedence-based restriction.
- The `(Swp,*)` family (the `task_deletion` pairing) shows above-average variability too.

Possible reasons to failure:
- The prompt does not provide a worked example with each operator/restriction.
- There can be confusion between the tasks (inserted one, deleted one, moving one, candidate, anchor, etc.).

However, we must avoid overfitting the prompt.

**If you re-run this file and see a different pass rate than described here**: 
It is probably ot a regression. 
Check again a few individual failures before concluding anything about prompt/schema quality. 
A stronger, hosted model (Anthropic, OpenAI, Groq, ...) is expected to do substantially better than 
either local model tried so far, but hasn't been verified end to end here. 
Keep this file's analysis updated if you materially change the prompt or schema and re-run the batch.
