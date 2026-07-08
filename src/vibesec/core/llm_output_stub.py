from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .review_llm_packet import REQUESTED_OUTPUTS
from .review_schema import SchemaValidationError


STUB_DISCLAIMER = "This is a contract stub, not a completed LLM security review."


def write_stub_llm_review_outputs(workspace_dir: str | Path) -> dict[str, Any]:
    workspace = Path(workspace_dir)
    packet = _load_packet(workspace / "llm_review_packet.json")
    rule_findings = [item for item in packet.get("rule_findings", []) if isinstance(item, dict)]
    stub_findings = [_stub_finding(item) for item in rule_findings[:3]]

    files = {
        "nontechnical_user_summary.md": _nontechnical_summary(packet),
        "launch_risk_report.md": _launch_risk_report(packet, stub_findings),
        "security_review_findings.json": json.dumps(
            {
                "schema_version": "1.0",
                "stub_status": STUB_DISCLAIMER,
                "launch_decision": "REVIEW",
                "findings": stub_findings,
            },
            ensure_ascii=False,
            indent=2,
        ),
        "agent_fix_plan.md": _agent_fix_plan(stub_findings),
        "retest_checklist.md": _retest_checklist(stub_findings),
    }
    for output_name in REQUESTED_OUTPUTS:
        (workspace / output_name).write_text(files[output_name], encoding="utf-8")
    return {
        "workspace": str(workspace),
        "outputs": REQUESTED_OUTPUTS,
        "stub": True,
        "model_api_called": False,
        "launch_readiness_claimed": False,
    }


def _stub_finding(rule_finding: dict[str, Any]) -> dict[str, Any]:
    severity = rule_finding.get("severity")
    if severity not in {"P0", "P1", "P2", "P3", "Info"}:
        severity = "P2"
    return {
        "finding_id": str(rule_finding.get("finding_id", "VSG-STUB-FINDING")),
        "new_llm_finding": False,
        "title": "Contract stub for " + str(rule_finding.get("title", "baseline finding")),
        "severity": severity,
        "confidence": "low",
        "launch_impact": "review",
        "evidence_files": _evidence_files(rule_finding),
        "reasoning_summary": STUB_DISCLAIMER + " A host Agent must review the packet before making final claims.",
        "missing_evidence": ["Completed host-agent security reasoning is missing."],
        "recommended_action": "verify_before_fix",
        "human_confirmation_required": True,
        "safe_to_auto_suppress": False,
    }


def _nontechnical_summary(packet: dict[str, Any]) -> str:
    project_type = packet.get("project_profile", {}).get("project_type", "unknown")
    return f"""# Nontechnical User Summary

Stub status: {STUB_DISCLAIMER}

Launch decision: REVIEW

## Plain-Language Answer

This stub does not decide whether the product is safe to launch. A host Agent must inspect `llm_review_packet.json`, cited evidence files, and missing context before making a launch-risk judgment.

## Top Risks

- Project type: {project_type}
- Baseline rule findings: {len(packet.get("rule_findings", []))}
- Evidence role: baseline hints, not final judgment

## Human Confirmation Needed

- Confirm auth, data access, and Agent/tool boundaries before any risky fix.

## Agent Boundaries

- Human confirmation required before risky edits: yes
- `safe_to_auto_suppress`: false
- Prohibited changes: do not write suppressions, mutate production data, or edit real projects without explicit user approval.
"""


def _launch_risk_report(packet: dict[str, Any], findings: list[dict[str, Any]]) -> str:
    lines = [
        "# Launch Risk Report",
        "",
        f"Stub status: {STUB_DISCLAIMER}",
        "",
        "Launch decision: REVIEW",
        "",
        "## Review Scope",
        "",
        "- Input packet: `llm_review_packet.json`",
        "- Rule findings role: baseline hints, not final judgment",
        "- External model/API called: no",
        "",
        "## Findings",
        "",
    ]
    for finding in findings:
        lines.extend(
            [
                f"### {finding['finding_id']}: {finding['title']}",
                "",
                f"- Severity: {finding['severity']}",
                "- Launch impact: review",
                "- Confidence: low",
                "- Evidence files: " + ", ".join(finding["evidence_files"]),
                "- Confirmed risk: not assessed in stub",
                "- Likely true risk: not assessed in stub",
                "- Needs review: yes",
                "- Downgrade candidate: not assessed in stub",
                "- Suppression candidate: not assessed in stub",
                "- Missing evidence: completed host-agent review",
                "- Recommended action: verify_before_fix",
                "",
            ]
        )
    lines.extend(["## Safety Notes", "", "- `safe_to_auto_suppress`: false", "- Do not include offensive instructions.", ""])
    return "\n".join(lines)


def _agent_fix_plan(findings: list[dict[str, Any]]) -> str:
    ids = ", ".join(item["finding_id"] for item in findings) or "none"
    return f"""# Agent Fix Plan

Stub status: {STUB_DISCLAIMER}

## Human Confirmation Gate

- Confirmation required before editing real projects: yes
- `safe_to_auto_suppress`: false

## Bounded Tasks

### Task: Complete host-agent review before repair

- Finding IDs: {ids}
- Files to inspect: use `llm_review_packet.json` evidence references
- Allowed change scope: none in this stub
- Missing evidence to confirm first: completed LLM security reasoning

## Prohibited Changes

- Do not edit real projects from this stub.
- Do not write suppression files automatically.
- Do not claim launch readiness from this stub.

## Verification Commands

```powershell
py -3 scripts\\validate_llm_review_outputs.py "<workspace>"
```

## Retest Notes

After real fixes, rerun VibeSec scan/review and validate the completed LLM outputs.
"""


def _retest_checklist(findings: list[dict[str, Any]]) -> str:
    ids = ", ".join(item["finding_id"] for item in findings) or "none"
    evidence = sorted({path for item in findings for path in item["evidence_files"]})
    return f"""# Retest Checklist

Stub status: {STUB_DISCLAIMER}

## Commands To Rerun

```powershell
py -3 scripts\\verify_release.py
py -3 scripts\\validate_llm_review_outputs.py "<workspace>"
```

## Evidence To Inspect

- Finding IDs: {ids}
- Evidence files: {", ".join(evidence) if evidence else "packet evidence references"}
- Expected gate change: not assessed in stub

## Manual Checks

- Confirm whether host-agent review has produced final user summary, launch-risk report, findings, fix plan, and retest checklist.

## Safety

- Do not mark a product launch-ready from this checklist alone.
- `safe_to_auto_suppress`: false
"""


def _evidence_files(rule_finding: dict[str, Any]) -> list[str]:
    affected = rule_finding.get("affected_files")
    if isinstance(affected, list) and all(isinstance(item, str) for item in affected):
        return affected[:5] or ["llm_review_packet.json"]
    return ["llm_review_packet.json"]


def _load_packet(path: Path) -> dict[str, Any]:
    try:
        packet = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SchemaValidationError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SchemaValidationError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(packet, dict):
        raise SchemaValidationError("llm_review_packet.json must be an object")
    return packet

