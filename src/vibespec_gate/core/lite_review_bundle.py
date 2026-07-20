from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .coverage import EvidenceCoverage, coverage_from_dict
from .path_safety import require_disjoint_paths
from .review_schema import validate_review_output_dir

EVIDENCE_FILES = (
    "llm_review_packet.json",
    "agent_review_decisions.json",
    "human_review_queue.md",
    "suppression_candidates.json",
    "ai_review.json",
    "ai_review_summary.md",
    "review_packets.json",
)


def build_lite_review_bundle(review_output: Path, bundle_dir: Path | None = None) -> dict[str, object]:
    review_output = review_output.resolve()
    default_bundle = review_output.with_name(f"{review_output.name}-lite-review")
    review_output, bundle_dir = require_disjoint_paths(
        review_output,
        bundle_dir or default_bundle,
        first_label="review input",
        second_label="bundle output",
    )
    validate_review_output_dir(review_output)
    if bundle_dir.exists():
        raise ValueError(f"bundle output already exists: {bundle_dir}")
    decisions_path = review_output / "agent_review_decisions.json"
    decisions_payload = _load_json(decisions_path)
    decisions = _decisions(decisions_payload)
    summary = decisions_payload.get("summary", {}) if isinstance(decisions_payload, dict) else {}
    coverage = coverage_from_dict(summary.get("coverage"))
    invalid_severity_count = _required_nonnegative_int(
        summary.get("invalid_severity_count"),
        "agent_review_decisions.summary.invalid_severity_count",
    )
    launch_decision = _launch_decision(decisions, coverage, invalid_severity_count=invalid_severity_count)
    bundle_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vibespec-gate-bundle-", dir=bundle_dir.parent) as temporary:
        staging = Path(temporary) / "bundle"
        staging.mkdir()
        evidence_dir = staging / "evidence"
        evidence_dir.mkdir()
        _write(
            staging / "launch_decision.md",
            render_launch_decision(launch_decision, summary, decisions, coverage, invalid_severity_count),
        )
        _write(staging / "top_security_risks.md", render_top_security_risks(decisions))
        _write(staging / "agent_fix_plan.md", render_agent_fix_plan(decisions))
        _write(staging / "retest_checklist.md", render_retest_checklist(decisions))
        copied = _copy_evidence(review_output, evidence_dir)
        staging.rename(bundle_dir)
    return {
        "schema_version": "1.0",
        "review_output": str(review_output),
        "bundle_dir": str(bundle_dir),
        "launch_decision": launch_decision,
        "coverage": coverage.to_dict(),
        "primary_outputs": [
            str(bundle_dir / "launch_decision.md"),
            str(bundle_dir / "top_security_risks.md"),
            str(bundle_dir / "agent_fix_plan.md"),
            str(bundle_dir / "retest_checklist.md"),
        ],
        "evidence_files": [str(bundle_dir / "evidence" / name) for name in copied],
    }


def render_launch_decision(
    launch_decision: str,
    summary: dict[str, Any],
    decisions: list[dict[str, Any]],
    coverage: EvidenceCoverage,
    invalid_severity_count: int = 0,
) -> str:
    blocking = [item for item in decisions if item.get("blocks_launch")]
    must_review = [item for item in decisions if item.get("must_review")]
    lines = [
        "# Launch Decision",
        "",
        f"Decision: {launch_decision}",
        "",
        "## Can I launch?",
        "",
        _decision_explanation(
            launch_decision,
            len(blocking),
            len(must_review),
            coverage,
            invalid_severity_count,
        ),
        "",
        "## Review Snapshot",
        "",
        f"- Project type: {summary.get('project_type', 'unknown')}",
        f"- Reviewed findings: {summary.get('reviewed_findings', len(decisions))}",
        f"- Launch-blocking findings: {len(blocking)}",
        f"- Human confirmation items: {len(must_review)}",
        f"- Findings with unknown severity: {invalid_severity_count}",
        "",
        "## Evidence Coverage",
        "",
        f"- Coverage status: {coverage.coverage_status}",
        f"- Files inspected: {coverage.files_inspected} of {coverage.files_discovered}",
    ]
    for item in coverage.surfaces:
        detail = ", ".join(item.source_refs) if item.source_refs else item.reason
        lines.append(f"- {item.surface}: {item.status} - {detail}")
    missing = coverage.missing_evidence()
    if missing:
        lines.extend(["", "### Missing evidence", "", *[f"- {item}" for item in missing]])
    lines.extend(
        [
        "",
        "## Human Confirmation Required",
        "",
        ]
    )
    if must_review:
        lines.append("A human should confirm the listed evidence before any coding Agent edits the project.")
    else:
        lines.append("No high-value human confirmation items are present in the review output.")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "Do not auto-fix, auto-suppress, broaden permissions, or mutate the reviewed project without explicit human confirmation.",
            "",
            "This Lite review is not a professional security certification, penetration test, legal review, or compliance attestation.",
            "",
        ]
    )
    return "\n".join(lines)


def render_top_security_risks(decisions: list[dict[str, Any]]) -> str:
    risks = _risk_decisions(decisions)
    lines = [
        "# Top Security Risks",
        "",
        "These are the highest-impact review items from the existing VibeSpec Gate review output.",
        "",
    ]
    if not risks:
        lines.extend(["No launch-blocking or human-confirmation risks were found.", ""])
        return "\n".join(lines)
    for index, item in enumerate(risks, start=1):
        files = ", ".join(item.get("inspect_files") or ["unknown"])
        lines.extend(
            [
                f"## {index}. {item.get('title', 'Untitled finding')}",
                "",
                f"- Finding id: {item.get('finding_id', 'unknown')}",
                f"- Severity: {item.get('recommended_final_severity', 'unknown')}",
                f"- Launch impact: {'blocks launch' if item.get('blocks_launch') else 'needs review'}",
                f"- Why it matters: {item.get('reason', 'No reason recorded.')}",
                f"- Files or areas: {files}",
                "",
            ]
        )
    return "\n".join(lines)


def render_agent_fix_plan(decisions: list[dict[str, Any]]) -> str:
    fix_items = [
        item
        for item in decisions
        if item.get("safe_for_agent_fix") and item.get("recommended_action") == "fix"
    ]
    lines = [
        "# Agent Fix Plan",
        "",
        "## Human Confirmation Gate",
        "",
        "Confirm each item is real and in scope before asking a coding Agent to edit the reviewed project.",
        "",
    ]
    if not fix_items:
        lines.extend(["No Agent-ready fix tasks are present in the review output.", ""])
        return "\n".join(lines)
    for index, item in enumerate(fix_items, start=1):
        lines.extend(
            [
                f"## Task {index}: {item.get('title', 'Untitled finding')}",
                "",
                f"- Finding id: {item.get('finding_id', 'unknown')}",
                f"- Allowed change scope: inspect and fix only the files listed below for this finding.",
                "- Files to inspect:",
            ]
        )
        for file_path in item.get("inspect_files") or ["unknown"]:
            lines.append(f"  - {file_path}")
        lines.extend(["- Prohibited changes:"])
        for rule in item.get("prohibited_changes") or ["Do not broaden scope without human approval."]:
            lines.append(f"  - {rule}")
        lines.extend(["- Verification commands:"])
        for command in item.get("verification_commands") or ["Rerun VibeSpec Gate review after the fix."]:
            lines.append(f"  - {command}")
        lines.append("")
    return "\n".join(lines)


def render_retest_checklist(decisions: list[dict[str, Any]]) -> str:
    commands = []
    for item in _risk_decisions(decisions):
        for command in item.get("verification_commands") or []:
            if command not in commands:
                commands.append(command)
    lines = [
        "# Retest Checklist",
        "",
        "Use this after confirmed fixes are prepared.",
        "",
        "## Commands Or Checks To Rerun",
        "",
    ]
    if commands:
        for command in commands:
            lines.append(f"- {command}")
    else:
        lines.append("- Rerun the VibeSpec Gate review for the same findings.")
    lines.extend(
        [
            "",
            "## Expected Result",
            "",
            "- Launch-blocking findings should move out of the human review queue only after evidence confirms the fix.",
            "- `safe_to_auto_suppress` must remain false unless a human explicitly creates a suppression record.",
            "- Keep the full evidence bundle under `evidence/` for auditability.",
            "",
        ]
    )
    return "\n".join(lines)


def _copy_evidence(review_output: Path, evidence_dir: Path) -> list[str]:
    copied = []
    for name in EVIDENCE_FILES:
        source = review_output / name
        if source.exists():
            destination = evidence_dir / name
            shutil.copy2(source, destination)
            copied.append(destination.name)
    raw = evidence_dir / "raw_findings.json"
    ai_review = review_output / "ai_review.json"
    if ai_review.exists():
        shutil.copy2(ai_review, raw)
        copied.append(raw.name)
    return copied


def _launch_decision(
    decisions: list[dict[str, Any]],
    coverage: EvidenceCoverage,
    *,
    invalid_severity_count: int = 0,
) -> str:
    if any(item.get("blocks_launch") for item in decisions):
        return "BLOCK"
    if invalid_severity_count:
        return "REVIEW"
    if any(item.get("must_review") for item in decisions):
        return "REVIEW"
    if not coverage.allows_pass():
        return "REVIEW"
    if any(item.get("recommended_action") in {"downgrade", "suppress"} for item in decisions):
        return "PASS_WITH_WARNINGS"
    return "PASS"


def _decision_explanation(
    decision: str,
    blocking_count: int,
    must_review_count: int,
    coverage: EvidenceCoverage,
    invalid_severity_count: int = 0,
) -> str:
    if decision == "BLOCK":
        return f"Do not launch yet. {blocking_count} finding(s) currently block launch and need human confirmation before fixes."
    if decision == "REVIEW":
        if invalid_severity_count:
            return f"Do not treat this as launch-ready yet. {invalid_severity_count} finding(s) have unknown severity metadata."
        if not coverage.allows_pass():
            return "Do not treat this as launch-ready yet. Evidence coverage is incomplete and must be reviewed."
        return f"Do not treat this as launch-ready yet. {must_review_count} finding(s) need human review."
    if decision == "PASS_WITH_WARNINGS":
        return "No launch-blocking findings are present, but warning/downgrade/suppression candidates should be reviewed."
    return "No launch-blocking findings are present in this review output."


def _risk_decisions(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    risks = [
        item
        for item in decisions
        if item.get("blocks_launch") or item.get("must_review")
    ]
    return sorted(risks, key=lambda item: (not item.get("blocks_launch"), str(item.get("finding_id", ""))))[:10]


def _decisions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    decisions = payload.get("decisions")
    if not isinstance(decisions, list):
        raise ValueError("agent_review_decisions.json must contain a decisions list")
    return decisions


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _required_nonnegative_int(value: object, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
