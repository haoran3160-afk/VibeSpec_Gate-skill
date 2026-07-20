# Evidence Coverage

Record coverage before assigning a launch decision.

## Coverage Schema

```text
coverage_status: complete | partial | insufficient | truncated
surfaces:
  - surface: auth | authorization | secrets | data_rules | deployment | agent_tools | desktop_ipc
    status: reviewed | not_applicable | missing | truncated
    source_refs: [path:line | configuration reference]
    reason: required for not_applicable, missing, or truncated
files_discovered: integer
files_inspected: integer
files_skipped: integer
```

Include all seven surfaces. Do not omit a surface to obtain `complete`.

## Status Rules

- `complete`: every surface is `reviewed` with source references or `not_applicable` with a concrete project-specific reason; no relevant evidence was skipped or unreadable.
- `partial`: some relevant evidence was inspected, but at least one required surface or file remains missing.
- `insufficient`: the review lacks enough evidence to assess launch readiness, including an absent coverage record or empty project.
- `truncated`: an inspection limit excluded discovered evidence, such as reading only the first 200 files of a larger inventory.

Use `reviewed` only when the surface was actually inspected. Use `not_applicable` only after project evidence supports that conclusion. Use `missing` for unavailable required evidence and `truncated` when a review limit skipped relevant evidence.

## Decision Qualification

| Coverage | Allowed decisions |
| --- | --- |
| `insufficient` | `REVIEW`, or `BLOCK` with confirmed blocking evidence |
| `partial` | `REVIEW`, or `BLOCK` with confirmed blocking evidence |
| `truncated` | `REVIEW`, or `BLOCK` with confirmed blocking evidence |
| `complete` | `BLOCK`, `REVIEW`, `PASS_WITH_WARNINGS`, or `PASS` according to findings |

Never assign `PASS` or `PASS_WITH_WARNINGS` when a surface is missing or truncated. Never infer complete coverage from zero findings. Do not show a numeric security score for incomplete coverage.

## Missing Evidence

List each missing or truncated surface and the evidence needed next. Examples include production identity-provider settings, database policies, deployment environment values, Agent tool allowlists, Electron preload code, or the uninspected remainder of a large repository.
