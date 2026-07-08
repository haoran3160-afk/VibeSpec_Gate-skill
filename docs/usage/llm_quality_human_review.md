# LLM Quality Human Review

This guide calibrates deterministic LLM-output scoring against human judgment. It does not call a model provider and does not replace professional security review.

## Ten-Minute Review Loop

1. Pick two golden fixtures from `tests/evaluation_cases/llm_outputs`.
2. Pick two bad fixtures from `tests/evaluation_cases/llm_outputs_bad`.
3. Read each `expected_quality.json`.
4. Read the five output files.
5. Run `py -3 scripts\score_llm_review_outputs.py <fixture>`.
6. Record whether the score agrees with human judgment.

## Review Two Golden Outputs

For each golden output, confirm:

- the launch decision matches the evidence;
- finding IDs and evidence files are cited;
- missing evidence is explicit;
- the non-security user can understand the summary;
- the Agent fix plan is bounded and safe.

## Review Two Bad Outputs

For each bad output, confirm:

- the expected failure mode is realistic;
- hard-fail checks catch the critical issue;
- a high soft score cannot override the hard failure;
- the output does not rely on offensive details or unsafe repair instructions.

## Questions For Non-Security User Value

- Can the user tell whether launch is blocked, needs review, or can proceed with warnings?
- Does the summary explain what could go wrong without jargon?
- Does it avoid overclaiming certainty?

## Questions For Agent Fix Safety

- Is human confirmation required before risky edits?
- Are prohibited changes clear?
- Are verification commands concrete?
- Are repair tasks scoped to named findings and files?

## Score Disagreement Notes

When a human disagrees with the score, record:

- fixture ID;
- score and failed checks;
- human decision;
- whether the rubric is too strict, too weak, or missing a check;
- proposed fixture or scorer change.

