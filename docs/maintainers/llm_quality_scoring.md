# LLM Quality Scoring

This page is for maintainers working on deterministic scoring of completed host-agent outputs.

## Golden And Bad Fixtures

Golden fixtures live under:

```text
tests/evaluation_cases/llm_outputs/
```

Bad-output fixtures live under:

```text
tests/evaluation_cases/llm_outputs_bad/
```

Golden outputs should pass. Bad outputs should fail for declared reasons. Hard-fail checks override high soft scores.

## Commands

Score a golden fixture:

```powershell
py -3 scripts\score_llm_review_outputs.py tests\evaluation_cases\llm_outputs\secret_runtime_block
```

Score a bad fixture; this is expected to exit `1`:

```powershell
py -3 scripts\score_llm_review_outputs.py tests\evaluation_cases\llm_outputs_bad\secret_runtime_overoptimistic
```

Build the matrix:

```powershell
py -3 scripts\build_llm_quality_matrix.py
```

## What Scoring Checks

- Launch decision correctness.
- Finding and evidence citation.
- Missing-evidence clarity.
- Bounded Agent repair tasks.
- Prohibited changes.
- Retest commands.
- `safe_to_auto_suppress=false`.
- Absence of stub disclaimers.

Scoring is regression evidence. It does not replace human judgment or professional security review.
