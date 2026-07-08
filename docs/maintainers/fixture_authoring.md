# Fixture Authoring

This page is for maintainers adding deterministic review or LLM-output fixtures.

## Review Fixtures

Review fixtures live under:

```text
tests/evaluation_cases/review/
```

Each fixture should document:

- the risk domain;
- the expected verdict;
- the expected action;
- whether human review is required;
- any expected decision type or Agent next step.

After editing review fixtures, rebuild or verify the evaluation matrix:

```powershell
py -3 scripts\build_evaluation_matrix.py
py -3 scripts\verify_release.py
```

## LLM Output Fixtures

Golden completed-output fixtures live under:

```text
tests/evaluation_cases/llm_outputs/
```

Bad-output fixtures live under:

```text
tests/evaluation_cases/llm_outputs_bad/
```

Every LLM output fixture should include:

```text
llm_review_packet.json
expected_quality.json
outputs/
  nontechnical_user_summary.md
  launch_risk_report.md
  security_review_findings.json
  agent_fix_plan.md
  retest_checklist.md
```

Use focused scoring before relying on a fixture in release verification:

```powershell
py -3 scripts\score_llm_review_outputs.py <fixture>
py -3 scripts\build_llm_quality_matrix.py
```

## Boundary

Fixtures should be deterministic and reviewable. Do not add provider-generated output unless its source, packet, and calibration status are explicit.
