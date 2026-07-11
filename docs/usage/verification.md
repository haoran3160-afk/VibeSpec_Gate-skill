# Verification

Run commands from the repository root:

```bash
cd VibeSpec_Gate-skill
```

Use `py -3` on Windows when available and `python3` on macOS/Linux. The examples below use PowerShell where environment-variable syntax differs.

Set these variables for verification commands that import the local source tree directly:

```powershell
$env:PYTHONPATH = "src"
$env:PYTHONDONTWRITEBYTECODE = "1"
```

`PYTHONPATH=src` runs the source tree without installing the package. `PYTHONDONTWRITEBYTECODE=1` avoids creating new `__pycache__` files during verification.

## What Verification Means

VibeSpec Gate is an LLM-native security review Skill. These commands verify the repository's supporting infrastructure: evidence extraction, deterministic review baseline, schema contracts, decision ledgers, tests, and release hygiene. Passing verification does not mean a target product is absolutely secure; it means the Skill infrastructure is internally consistent and ready to support review work.

## Smoke Verification

This repository smoke check uses only the Python standard library and does not require pytest:

```powershell
py -3 scripts\verify_phase4_5_smoke.py
```

The smoke script inserts the local `src` directory into `sys.path`, so it can run even when `PYTHONPATH` is not already set. It verifies CLI import, `vibespec-gate review --help`, one review evaluation fixture, existing Phase 4 review JSON and markdown outputs, `llm_review_packet.json`, schema shape, snippet limits, JSON/Markdown agent decision coverage, and provider-secret redaction through the official review schema validator.

On macOS/Linux, the equivalent command is:

```bash
python3 scripts/verify_phase4_5_smoke.py
```

## Pytest Verification

When pytest is available:

```powershell
py -3 -m pytest -q -p no:cacheprovider
py -3 -m pytest tests\test_evaluation_cases.py -q -p no:cacheprovider
```

Do not install dependencies or run fix commands inside real reviewed projects unless the user explicitly asks for a repair implementation. Real-project review and scan outputs used for regression must be written only under this repository, for example `./test output`.

## Review Schema Validation

Validate a Phase 4 review output directory:

```powershell
py -3 -m vibespec_gate.cli review-validate ".\test output\phase4_review\example-project"
```

The validator checks JSON structure, enum values, packet/verdict matching, `llm_review_packet.json`, snippet length, secret redaction, `reviewer=rule-based`, `safe_to_auto_suppress=false`, summary counts, and that both `agent_review_decisions.json` and `agent_review_decisions.md` cover every reviewed finding. This validates the deterministic baseline and LLM handoff contract, not the full ceiling of LLM-assisted review quality.

## LLM Output Workspace Validation

Build, stub, and validate a host-agent review workspace:

```powershell
py -3 scripts\build_llm_review_workspace.py ".\test output\phase4_review\example-project"
py -3 scripts\stub_llm_review_outputs.py ".\test output\phase4_review\example-project\llm_review_workspace"
py -3 scripts\validate_llm_review_outputs.py ".\test output\phase4_review\example-project\llm_review_workspace"
vibespec-gate llm-output-validate ".\test output\phase4_review\example-project\llm_review_workspace"
```

The workspace builder does not call external model/API providers and does not copy project source. The stub generator exists only for contract testing; stub files are not completed LLM security reviews.

The LLM output validator checks required output presence, `security_review_findings.json` shape, enum values, packet finding ID references, `safe_to_auto_suppress=false`, repair-plan prohibited changes, verification commands, and narrow unsafe-wording guardrails.

## LLM Output Quality Scoring

Phase 9 fixtures under `tests\evaluation_cases\llm_outputs` contain completed golden host-agent outputs. They are not contract stubs.

Score one fixture:

```powershell
py -3 scripts\score_llm_review_outputs.py tests\evaluation_cases\llm_outputs\secret_runtime_block
```

Build the quality matrix:

```powershell
py -3 scripts\build_llm_quality_matrix.py
```

Score a bad fixture; this command is expected to exit `1` and report `passed=false`:

```powershell
py -3 scripts\score_llm_review_outputs.py tests\evaluation_cases\llm_outputs_bad\secret_runtime_overoptimistic
```

Compare manually supplied host-agent samples:

```powershell
py -3 scripts\compare_host_agent_samples.py "test output\phase10_host_agent_quality_expansion\host_agent_samples"
```

Validate final outputs without allowing stubs:

```powershell
py -3 scripts\validate_llm_review_outputs.py tests\evaluation_cases\llm_outputs\secret_runtime_block\outputs --final
```

Quality scoring checks deterministic regression evidence such as launch decision consistency, finding/evidence citation, missing-evidence clarity, bounded Agent repair tasks, prohibited changes, retest commands, `safe_to_auto_suppress=false`, and absence of the Phase 8 stub disclaimer. Phase 10 hard-fail checks override high soft scores. It does not replace human judgment or professional security testing.

## Release Verification

Run the full release gate before a baseline commit:

```powershell
py -3 scripts\verify_release.py
```

The release verifier runs:

- Phase 4/5 smoke verification.
- Full pytest suite.
- `compileall` over `src`, `tests`, and `scripts`.
- `review-validate` for the three Phase 4 review outputs.
- Evaluation matrix coverage checks.
- LLM output quality matrix expectation checks.
- Git hygiene checks for cache, env, and generated output ignores.

## Evaluation Matrix

The release matrix lives under:

```text
test output\phase7_release_hardening\evaluation_matrix.json
test output\phase7_release_hardening\evaluation_matrix.md
```

It maps review fixtures to domains, expected verdicts, expected actions, `agent_next_step`, `decision_type`, and `must_review`. Use it to explain why review counts change after rubric edits.

## Decision Schema Versioning

`agent_review_decisions.json` uses a versioned object:

```json
{
  "schema_version": "1.0",
  "reviewer": "rule-based",
  "generated_by": "vibespec-gate review",
  "summary": {},
  "decisions": []
}
```

`review-validate` requires `schema_version=1.0`, verifies decision count coverage, and checks summary counts against the decision ledger.
