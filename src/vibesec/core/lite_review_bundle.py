from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


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
    bundle_dir = (bundle_dir or review_output / "lite_review").resolve()
    if review_output == bundle_dir:
        raise ValueError("bundle_dir must be separate from review_output")
    decisions_path = review_output / "agent_review_decisions.json"
    if not decisions_path.exists():
        raise FileNotFoundError(decisions_path)
    decisions_payload = _load_json(decisions_path)
    decisions = _decisions(decisions_payload)
    summary = decisions_payload.get("summary", {}) if isinstance(decisions_payload, dict) else {}
    launch_decision = _launch_decision(decisions)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir = bundle_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write(bundle_dir / "launch_decision.md", render_launch_decision(launch_decision, summary, decisions))
    _write(bundle_dir / "top_security_risks.md", render_top_security_risks(decisions))
    _write(bundle_dir / "agent_fix_plan.md", render_agent_fix_plan(decisions))
    _write(bundle_dir / "retest_checklist.md", render_retest_checklist(decisions))
    copied = _copy_evidence(review_output, evidence_dir)
    return {
        "schema_version": "1.0",
        "review_output": str(review_output),
        "bundle_dir": str(bundle_dir),
        "launch_decision": launch_decision,
        "primary_outputs": [
            str(bundle_dir / "launch_decision.md"),
            str(bundle_dir / "top_security_risks.md"),
            str(bundle_dir / "agent_fix_plan.md"),
            str(bundle_dir / "retest_checklist.md"),
        ],
        "evidence_files": copied,
    }


def render_launch_decision(launch_decision: str, summary: dict[str, Any], decisions: list[dict[str, Any]]) -> str:
    blocking = [item for item in decisions if item.get("blocks_launch")]
    must_review = [item for item in decisions if item.get("must_review")]
    lines = [
        "# Launch Decision",
        "",
        f"Decision: {launch_decision}",
        "",
        "## Can I launch?",
        "",
        _decision_explanation(launch_decision, len(blocking), len(must_review)),
        "",
        "## Review Snapshot",
        "",
        f"- Project type: {summary.get('project_type', 'unknown')}",
        f"- Reviewed findings: {summary.get('reviewed_findings', len(decisions))}",
        f"- Launch-blocking findings: {len(blocking)}",
        f"- Human confirmation items: {len(must_review)}",
        "",
        "## Human Confirmation Required",
        "",
    ]
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
        "These are the highest-impact review items from the existing VibeSec Gate review output.",
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
        for command in item.get("verification_commands") or ["Rerun VibeSec Gate review after the fix."]:
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
        lines.append("- Rerun the VibeSec Gate review for the same findings.")
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
            copied.append(str(destination))
    raw = evidence_dir / "raw_findings.json"
    ai_review = review_output / "ai_review.json"
    if ai_review.exists():
        shutil.copy2(ai_review, raw)
        copied.append(str(raw))
    return copied


def _launch_decision(decisions: list[dict[str, Any]]) -> str:
    if any(item.get("blocks_launch") for item in decisions):
        return "BLOCK"
    if any(item.get("must_review") for item in decisions):
        return "REVIEW"
    if any(item.get("recommended_action") in {"downgrade", "suppress"} for item in decisions):
        return "PASS_WITH_WARNINGS"
    return "PASS"


def _decision_explanation(decision: str, blocking_count: int, must_review_count: int) -> str:
    if decision == "BLOCK":
        return f"Do not launch yet. {blocking_count} finding(s) currently block launch and need human confirmation before fixes."
    if decision == "REVIEW":
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
    return [item for item in decisions if isinstance(item, dict)]


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
