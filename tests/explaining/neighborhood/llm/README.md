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


# About `test_extractor_compliance.py`

This file holds 16 real-model checks — one per contrastive question template — asking a different question
than `test_extractor_quality.py` does: not "did the extraction contain the right kinds and entities?",
but "is the extracted `Neighborhood` one the tailored pipeline's question catalogue produces, *for this
template's own family*?", per `TemplateComplianceChecker.match`.

The backend defaults to the same free, local `ollama/qwen2.5:7b`. Point `XWSRP_EXTRACTOR_TEST_MODEL` at any
instructor `"provider/model-name"` string to compare another one — a plain `pytest -m llm` stays free and
offline, so nothing starts billing a provider by accident:

```
XWSRP_EXTRACTOR_TEST_MODEL=mistral/mistral-small-latest pytest -m llm
```

(`Mode.MD_JSON` is forced only for `ollama/...`, whose tool calling isn't reliable enough for instructor's
default; hosted providers keep their own per-provider default. Mistral needs `requirements_mistral.txt`
installed and `MISTRAL_API_KEY` set — see the root README.)

Each test renders its template's *own* wording at up to 3 valid field-value combinations
(`_MAX_SAMPLES_PER_TEMPLATE`, seeded shuffle with `_RANDOM_SEED = 42`) of the `tests/data` reference
solution, and fails on the first sample that either can't be extracted or comes back non-compliant.
Every one of those questions is compliant by construction on the tailored side — `Mapper` answers all
2222 of that solution's valid combinations with a compliant neighborhood, which
`tests/explaining/neighborhood/templates/test_checker_exhaustive.py` checks exhaustively — so a failure
here is always the LLM pipeline, never an unanswerable question.

This is a **stricter bar** than `test_extractor_quality.py`: it constrains the whole shape rather than
spot-checking membership, it pins the family the question was worded in, it must get 3 samples right in a
row, and its solution is much larger (5 employees / 31 tasks against 2 / 14), so a longer prompt. A lower
pass rate here is therefore not in contradiction with the ~9-11/17 recorded above.


## Analysis so far

Two full runs per model, same seed and therefore the same 48 sampled questions:

| model | run 1 | run 2 | time |
|---|---|---|---|
| `ollama/qwen2.5:7b` (local, free) | 3/16 | 3/16 | ~2 min |
| `mistral/mistral-small-latest` | 8/16 | 9/16 | 1m41s, then 39s |
| `mistral/mistral-medium-latest` | 12/16 | 12/16 | 1m10s both |
| `mistral/magistral-medium-latest` (reasoning) | **12/16** | **13/16** | ~1m05s both |

This is the first end-to-end check of the expectation recorded above, that a hosted model would do
substantially better than a local one. It does, and the gain is monotone in model size: 3 → ~8.5 → 12-13 of
16, all faster in wall clock than the local 7B despite the network round trip. The reasoning model
(`magistral-medium`) edges out the plain one at the same tier, but by one test on one run — not a margin
this sample size can really resolve.

`mistral-large-latest` could not be tried: it returns `403 tier_not_allowed` (code 1910, "This model is not
available in your subscription tier") on every call, and does not appear in `GET /v1/models` for the key
used here. Note that failure mode is indistinguishable from a quality result at the test's level — all 16
tests fail with `NeighborhoodExtractionError`, because `Extractor.extract` funnels transport errors and
genuine "not coverable" answers into the same exception. The tell is the clock: 16 failures in 3 seconds
cannot be 48 model calls. **Always check the run time before reading a bad batch as a bad model.**

`mistral-medium-latest` was the only model tried that is fully *stable*: both runs passed the same 12 and
failed the same 4. `magistral-medium` differed by one template between runs, the small tiers by several.

The failure profiles differ qualitatively by size. `qwen2.5:7b` gets the *operator* wrong or gives up
outright. Every Mistral tier nearly always picks the right operator and then attaches the wrong
*restriction*; going up the tiers fixed `(Ins,2b)`, `(Ins,3)` and eventually `(Swp,2a)`, converging on the
same hard residue — extracted shape against `Mapper`'s for the same fields:

- `(Swp,2b)` — **failed on every hosted model tried, always as an outright `coverable=False` refusal**, and
  always on the same question ("any non-performed task rather than any of their already-performed tasks").
  The single hardest item in the catalogue for this prompt.
- `(Swp,3)` — right operator pair, but adds a `PrecedenceChain` where the template leaves the order free.
- `(Ord,2c)` — `Precedence` instead of the `ForbiddenSequence` that is what actually forces the task to
  move. Two of three samples were still valid `(Ord,*)`; the third emitted **six** `Precedence` restrictions
  at once, pinning the task rather than freeing it.
- `(Swp,2a)` — `PrecedenceChain` instead of `ForbiddenBackwardSubsequence`. Fixed by `magistral-medium` on
  one of its two runs, so this one is on the edge of being solved by model quality alone.

So the remaining gap is almost entirely the `(Swp,2*)`/`(Swp,3)` cluster plus `(Ord,2c)`, and specifically
the `ForbiddenBackwardSubsequence` vs `PrecedenceChain` distinction — which no worked example in
`prompt.py` currently demonstrates. That is the one concrete prompt change these runs point at, though note
the warning above about overfitting the prompt. Scaling the model has now visibly plateaued on it: three
tiers of improvement did not shift `(Swp,2b)` at all.

Conversely, both Mistral tiers cleared the `(Ord,*)` family that the local model fails almost entirely —
medium passes 5 of 6 in both runs — so the "`(Ord,*)` tends to pick `task_insertion`" weakness above looks
specific to small local models rather than inherent to the prompt.

Everything below describes `qwen2.5:7b`.

Which three differed between runs — `(Ins,1)`/`(Ins,3)`/`(Ord,3)` on one, `(Ins,3)`/`(Ord,2b)`/`(Ord,3)` on
the next — and so did the split of the 13 failures between extraction refusals (5, then 6) and wrong shapes
(8, then 7). Run-to-run variance dominates at this sample size: treat 3/16 as the order of magnitude and the
failure *kinds* below as the real content, not the per-template verdicts.

Only `(Ord,3)` and `(Ins,3)` passed in both runs, and both are the easy cases — `(Ord,3)` maps to a bare
`SequenceReordering` + `ForbiddenSequence`, and `(Ins,3)` to a `TaskInsertion` with no restriction at all.

What the failures actually are, comparing the extracted shape against `Mapper`'s for the same fields:

- **`ForbiddenSequence` used where a `PrecedenceChain` belongs.** The most common miss, and one the
  analysis above doesn't record. `(Ins,2b)`/`(Ins,2c)` come back with the right `TaskInsertion` but every
  `PrecedenceChain` replaced by a `ForbiddenSequence`; `(Swp,2a)` likewise swaps `ForbiddenBackwardSubsequence`
  for `ForbiddenSequence`. The operator is right and the intent is close, but no template produces that pairing.
- **The `(Swp,*)` family self-reporting "not coverable".** `(Swp,1)`, `(Swp,2b)`, `(Swp,2c)` and `(Swp,3)` all
  failed by `coverable=False` rather than by producing a wrong shape — the sharpest version of the
  "incorrectly self-reporting a coverable question as not coverable" failure noted above.
- **`Precedence` where `ImmediatePrecedence` is required**, on `(Ord,1a)`/`(Ord,1b)`: the "just after / just
  before" anchoring is weakened into a plain ordering constraint.
- **Right kinds, wrong members.** On `(Ord,2a)` the extraction matched `Mapper`'s shape exactly at the type
  level (`TaskRepositioning` + `Precedence` + `PrecedenceChain`) and was still rejected, because the checker
  also requires the repositioned task to be *absent* from the chain and *named* by the further restriction.
  Kind-level assertions of the sort `test_extractor_quality.py` makes cannot see this class of error.
- **Family confusion in both directions**, which is what pinning the family (rather than only asking for
  compliance) is there to catch. `(Ord,2c)` comes back as a `TaskInsertion` — the miss already recorded
  above — and `(Ins,1)` comes back as a `TaskRepositioning` + `Precedence`, reading "not performing T13 just
  after T2" as moving a task the employee already has. Both produce a perfectly *compliant* neighborhood of
  the wrong family, so `is_compliant` alone waves them through; an earlier version of this file checked only
  compliance and scored both as passes.
