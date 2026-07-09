# LLM Review Contract

This contract defines how a host agent, API-backed model, or local/private model should use `llm_review_packet.json` to perform a defensive VibeSpec Gate review.

## Defensive Reviewer Instructions

The reviewer is a defensive security reviewer for user-owned vibe coding products. It should:

- use rule findings as evidence hints, not final truth;
- reason about launch risk, data exposure, and Agent/tool authority;
- explain risk in language a non-security user can understand;
- produce bounded Agent repair plans after human confirmation;
- avoid exploit payloads, bypass instructions, credential theft, destructive testing, or unauthorized scan plans;
- mark uncertainty and missing evidence explicitly.

## Input Packet

The expected input is `llm_review_packet.json`:

```json
{
  "schema_version": "1.0",
  "project_profile": {},
  "product_context": {},
  "sensitive_assets": [],
  "attack_surfaces": [],
  "auth_and_data_flow": {},
  "agent_tool_surfaces": [],
  "evidence_files": [],
  "rule_findings": [],
  "review_questions": [],
  "requested_outputs": [],
  "safety_boundaries": []
}
```

`rule_findings[*].evidence_role` must be `baseline_hint_not_final_judgment`.

## Host-Agent Workspace

Create a direct review workspace from a deterministic review output directory:

```powershell
py -3 scripts\build_llm_review_workspace.py "test output\phase4_review\personal-voice-light-agent"
```

The workspace contains the packet, `llm_review_prompt.md`, output templates, and a README. Workspace generation does not invoke any model/API provider and does not copy project source.

## Required Outputs

### `nontechnical_user_summary.md`

Plain-language launch risk summary for a non-security user:

- launch decision: `BLOCK`, `REVIEW`, `PASS_WITH_WARNINGS`, or `PASS`;
- top risks in nontechnical language;
- what could go wrong;
- what must be confirmed before fixing;
- what an Agent should not do automatically.

### `launch_risk_report.md`

Structured human-readable security report:

- risk ranking;
- affected files and evidence;
- confidence and missing evidence;
- launch impact;
- recommended next action.

### `security_review_findings.json`

Machine-readable findings:

```json
{
  "schema_version": "1.0",
  "findings": [
    {
      "finding_id": "string",
      "title": "string",
      "severity": "P0|P1|P2|P3|Info",
      "confidence": "high|medium|low",
      "launch_impact": "block|review|warning|none",
      "evidence_files": ["string"],
      "reasoning_summary": "string",
      "missing_evidence": ["string"],
      "recommended_action": "fix|verify_before_fix|downgrade|suppress_candidate|keep"
    }
  ]
}
```

### `agent_fix_plan.md`

Agent-ready repair plan:

- one bounded task per confirmed or likely true risk;
- files to inspect;
- prohibited changes;
- verification commands;
- confirmation required before editing real projects.

### `retest_checklist.md`

Retest plan after fixes:

- commands to rerun;
- evidence to inspect;
- expected change in gate decision;
- manual checks that cannot be proven from local evidence.

## Uncertainty Handling

When evidence is incomplete, the reviewer should use `REVIEW` rather than overclaiming. It should ask concrete questions such as where auth is enforced, whether user ownership is checked, or whether tool execution requires immediate user confirmation.

## Suppression Safety

False positives and suppression candidates are advisory. The reviewer must not write suppression files automatically and must keep `safe_to_auto_suppress=false`.

## Output Validation

Validate completed or stub outputs:

```powershell
py -3 scripts\validate_llm_review_outputs.py "<llm_review_workspace>"
vibesec llm-output-validate "<llm_review_workspace>"
```

The validator checks that all five required files exist, `security_review_findings.json` is valid, finding IDs come from the packet or are marked as new LLM findings, enums are valid, `safe_to_auto_suppress` is never true, repair plans include prohibited changes and verification commands, and obvious unsafe offensive wording is rejected.

`scripts\stub_llm_review_outputs.py` can produce contract stubs for testing only. Every stub output must state that it is not a completed LLM security review.

## Quality Evaluation

Completed host-agent outputs can be scored against golden fixtures:

```powershell
py -3 scripts\score_llm_review_outputs.py tests\evaluation_cases\llm_outputs\secret_runtime_block
py -3 scripts\build_llm_quality_matrix.py
```

Phase 8 validation proves workspace shape, output presence, schema shape, and safety guardrails. Phase 9 scoring adds deterministic quality evidence: launch decision consistency, finding/evidence citation, missing-evidence clarity, bounded Agent tasks, prohibited changes, retest commands, and absence of stub disclaimers.

Quality scoring does not replace human review, professional penetration testing, legal advice, compliance certification, or absolute-security proof. Provider/API-backed generation remains future work and must be explicit, never hidden.

Phase 10 adds paired bad-output fixtures under `tests\evaluation_cases\llm_outputs_bad`. These are expected to fail. The matrix schema is `1.1` and reports expectation semantics: golden cases should pass, bad cases should fail, and `expectations_failed` must remain `0`.

Hard-fail checks such as launch-decision contradiction, missing P1 cross-output coverage, missing evidence, unbounded Agent repair plans, and missing retest commands override soft score.
