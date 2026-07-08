from __future__ import annotations

from collections import Counter
from typing import Any

from .review_packets import looks_placeholder_or_example, packet_text
from .risk_model import Finding, ProjectProfile


def select_findings(findings: list[Finding], include_p2: bool) -> tuple[list[Finding], int]:
    selected: list[Finding] = []
    skipped = 0
    for finding in findings:
        if finding.suppressed or not finding.gate_relevant:
            skipped += 1
            continue
        if finding.severity in {"P0", "P1"} or (include_p2 and finding.severity == "P2"):
            selected.append(finding)
        else:
            skipped += 1
    return selected, skipped


def human_queue_items(packets: list[dict[str, Any]], verdicts: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    return [(packet, verdict) for packet, verdict in zip(packets, verdicts) if _is_human_queue_item(verdict)]


def suppression_candidates(packets: list[dict[str, Any]], verdicts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for packet, verdict in zip(packets, verdicts):
        source_type = packet["finding"].get("source_type", "runtime")
        text = packet_text(packet)
        include = (
            verdict["verdict"] == "false_positive"
            or (verdict["verdict"] == "should_downgrade" and source_type != "runtime")
            or looks_placeholder_or_example(text)
        )
        if not include:
            continue
        candidates.append(
            {
                "finding_id": packet["finding"]["id"],
                "fingerprint": packet["finding"]["fingerprint"],
                "title": packet["finding"]["title"],
                "source_type": source_type,
                "reason": verdict["reason"],
                "suggested_expiry": "90 days",
                "requires_human_confirmation": packet["finding"]["severity"] in {"P0", "P1"},
                "safe_to_auto_suppress": False,
            }
        )
    return candidates


def human_queue_markdown(profile: ProjectProfile, packets: list[dict[str, Any]], verdicts: list[dict[str, Any]]) -> str:
    sections = [
        ("Must confirm before fix", _section_items(packets, verdicts, "needs_human_review")),
        ("Likely true, fix after confirmation", _fix_items(packets, verdicts)),
    ]
    lines = [
        "# Human Review Queue",
        "",
        "Agent guidance: this queue contains only high-value findings that need confirmation before fixing. Downgrade and suppression decisions are recorded in agent_review_decisions.md.",
    ]
    for title, items in sections:
        lines.extend(["", f"## {title}"])
        if not items:
            lines.append("No findings in this section.")
            continue
        for idx, (packet, verdict) in enumerate(items, start=1):
            lines.extend(_queue_item_lines(profile, idx, packet, verdict))
    lines.append("")
    return "\n".join(lines)


def agent_review_decisions_markdown(
    profile: ProjectProfile, packets: list[dict[str, Any]], verdicts: list[dict[str, Any]]
) -> str:
    sections = [
        ("Must-review / fix decisions", [(packet, verdict) for packet, verdict in zip(packets, verdicts) if _is_human_queue_item(verdict)]),
        ("Downgrade candidates", _action_items(packets, verdicts, "downgrade")),
        ("Suppression and false-positive candidates", _suppression_items(packets, verdicts)),
        ("Other agent decisions", _other_decision_items(packets, verdicts)),
    ]
    lines = [
        "# Agent Review Decisions",
        "",
        f"- Project: {profile.path}",
        f"- Reviewed findings: {len(verdicts)}",
        "- Safety: safe_to_auto_suppress is false; do not write suppressions or edit real projects without confirmation.",
    ]
    for title, items in sections:
        lines.extend(["", f"## {title}"])
        if not items:
            lines.append("No findings in this section.")
            continue
        for idx, (packet, verdict) in enumerate(items, start=1):
            lines.extend(_decision_item_lines(idx, packet, verdict))
    lines.append("")
    return "\n".join(lines)


def agent_review_decision_items(packets: list[dict[str, Any]], verdicts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decisions = []
    for packet, verdict in zip(packets, verdicts):
        finding = packet["finding"]
        must_review = _is_human_queue_item(verdict)
        decision_type = _decision_type(verdict, must_review)
        decisions.append(
            {
                "decision_id": f"{finding['id']}:{verdict['fingerprint']}",
                "source_output": "ai_review.json",
                "finding_id": finding["id"],
                "fingerprint": verdict["fingerprint"],
                "title": finding["title"],
                "rubric": verdict["rubric"],
                "verdict": verdict["verdict"],
                "recommended_action": verdict["recommended_action"],
                "recommended_final_severity": verdict["recommended_final_severity"],
                "agent_next_step": verdict["agent_next_step"],
                "must_review": must_review,
                "decision_type": decision_type,
                "blocks_launch": must_review and verdict["recommended_final_severity"] in {"P0", "P1"},
                "safe_for_agent_fix": decision_type == "fix_after_confirmation",
                "inspect_files": verdict["inspect_files"],
                "prohibited_changes": verdict["prohibited_changes"],
                "verification_commands": verdict["verification_commands"],
                "safe_to_auto_suppress": verdict["safe_to_auto_suppress"],
                "reason": verdict["reason"],
            }
        )
    return decisions


def agent_review_decisions_json(summary_data: dict[str, object], decisions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "reviewer": "rule-based",
        "generated_by": "vibesec review",
        "summary": {
            "project_type": summary_data["project_type"],
            "reviewed_findings": summary_data["reviewed_findings"],
            "must_review_count": summary_data["must_review_count"],
            "agent_decision_count": summary_data["agent_decision_count"],
            "downgrade_candidate_count": summary_data["downgrade_candidate_count"],
            "suppression_candidate_count": summary_data["suppression_candidate_count"],
        },
        "decisions": decisions,
    }


def summary(
    profile: ProjectProfile,
    findings: list[Finding],
    packets: list[dict[str, Any]],
    verdicts: list[dict[str, Any]],
    skipped: int,
    queue: list[tuple[dict[str, Any], dict[str, Any]]],
    candidates: list[dict[str, Any]],
) -> dict[str, object]:
    verdict_counts = Counter(v["verdict"] for v in verdicts)
    category_counts = Counter(p["finding"]["category"] for p in packets)
    action_counts = Counter(v["recommended_action"] for v in verdicts)
    top_reasons = Counter(v["reason"] for v in verdicts if v["verdict"] in {"false_positive", "should_downgrade", "needs_human_review"})
    next_step_counts = Counter(v["agent_next_step"] for v in verdicts)
    downgrade_count = sum(1 for v in verdicts if v["recommended_action"] == "downgrade")
    return {
        "project_type": profile.project_type,
        "total_findings": len(findings),
        "reviewed_findings": len(packets),
        "skipped_findings": skipped,
        "must_review_count": len(queue),
        "agent_decision_count": len(verdicts),
        "downgrade_candidate_count": downgrade_count,
        "suppression_candidate_count": len(candidates),
        "verdict_counts": dict(verdict_counts),
        "category_counts": dict(category_counts),
        "recommended_action_counts": dict(action_counts),
        "agent_next_step_counts": dict(next_step_counts),
        "human_queue_count": len(queue),
        "gate_impact_summary": gate_impact(verdicts),
        "top_reasons": dict(top_reasons.most_common(8)),
    }


def summary_markdown(data: dict[str, object]) -> str:
    lines = [
        "# AI Review Summary",
        "",
        f"- Project type: {data['project_type']}",
        f"- Total findings: {data['total_findings']}",
        f"- Reviewed findings: {data['reviewed_findings']}",
        f"- Skipped findings: {data['skipped_findings']}",
        f"- Must review count: {data['must_review_count']}",
        f"- Agent decision count: {data['agent_decision_count']}",
        f"- Downgrade candidate count: {data['downgrade_candidate_count']}",
        f"- Suppression candidate count: {data['suppression_candidate_count']}",
        f"- Gate impact summary: {data['gate_impact_summary']}",
        "",
        "## Verdict Counts",
        *_dict_lines(data["verdict_counts"]),
        "",
        "## Category Counts",
        *_dict_lines(data["category_counts"]),
        "",
        "## Recommended Action Counts",
        *_dict_lines(data["recommended_action_counts"]),
        "",
        "## Agent Next Step Counts",
        *_dict_lines(data["agent_next_step_counts"]),
        "",
        "## Top Reasons",
        *_dict_lines(data["top_reasons"]),
        "",
    ]
    return "\n".join(lines)


def gate_impact(verdicts: list[dict[str, Any]]) -> str:
    high_value = [
        v
        for v in verdicts
        if _is_human_queue_item(v)
    ]
    downgrades = [v for v in verdicts if v["recommended_action"] in {"downgrade", "suppress"}]
    return f"{len(high_value)} high-value review items remain in the human queue; {len(downgrades)} findings are recorded as agent decisions."


def _is_human_queue_item(verdict: dict[str, Any]) -> bool:
    return (
        verdict["recommended_action"] in {"fix", "manual_review"}
        and verdict["verdict"] in {"confirmed", "likely_true", "needs_human_review"}
        and verdict["recommended_final_severity"] in {"P0", "P1"}
    )


def _section_items(
    packets: list[dict[str, Any]], verdicts: list[dict[str, Any]], verdict_name: str
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    return [(packet, verdict) for packet, verdict in zip(packets, verdicts) if verdict["verdict"] == verdict_name]


def _fix_items(packets: list[dict[str, Any]], verdicts: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    return [(packet, verdict) for packet, verdict in zip(packets, verdicts) if verdict["recommended_action"] == "fix"]


def _action_items(
    packets: list[dict[str, Any]], verdicts: list[dict[str, Any]], action: str
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    return [(packet, verdict) for packet, verdict in zip(packets, verdicts) if verdict["recommended_action"] == action]


def _suppression_items(packets: list[dict[str, Any]], verdicts: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    return [
        (packet, verdict)
        for packet, verdict in zip(packets, verdicts)
        if verdict["recommended_action"] == "suppress" or verdict["verdict"] == "false_positive"
    ]


def _other_decision_items(packets: list[dict[str, Any]], verdicts: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    known = set()
    for items in (
        [(packet, verdict) for packet, verdict in zip(packets, verdicts) if _is_human_queue_item(verdict)],
        _action_items(packets, verdicts, "downgrade"),
        _suppression_items(packets, verdicts),
    ):
        for packet, verdict in items:
            known.add((packet["finding"]["id"], verdict["fingerprint"]))
    return [
        (packet, verdict)
        for packet, verdict in zip(packets, verdicts)
        if (packet["finding"]["id"], verdict["fingerprint"]) not in known
    ]


def _decision_type(verdict: dict[str, Any], must_review: bool) -> str:
    if verdict["verdict"] == "needs_human_review":
        return "must_confirm_before_fix"
    if must_review and verdict["recommended_action"] == "fix":
        return "fix_after_confirmation"
    if verdict["verdict"] == "false_positive":
        return "false_positive_candidate"
    if verdict["recommended_action"] == "suppress":
        return "suppression_candidate"
    if verdict["recommended_action"] == "downgrade":
        return "downgrade_candidate"
    return "informational_decision"


def _queue_item_lines(profile: ProjectProfile, idx: int, packet: dict[str, Any], verdict: dict[str, Any]) -> list[str]:
    finding = packet["finding"]
    questions = verdict["human_review_questions"] or ["Confirm whether the evidence is runtime-relevant and reachable."]
    lines = [
        "",
        f"### {idx}. {finding['title']}",
        f"- Project: {profile.path}",
        f"- Finding id: {finding['id']}",
        f"- Severity: {finding['severity']}",
        f"- AI verdict: {verdict['verdict']}",
        f"- Confidence: {verdict['confidence']}",
        f"- Recommended action: {verdict['recommended_action']}",
        f"- Agent next step: {verdict['agent_next_step']}",
        f"- Reason: {verdict['reason']}",
        f"- File: {packet['evidence_context']['primary_file'] or ', '.join(finding['affected_files']) or 'project'}",
        "- Inspect files:",
        *[f"  - {item}" for item in verdict["inspect_files"]],
        "- Human questions:",
        *[f"  - {question}" for question in questions],
        "- Prohibited changes:",
        *[f"  - {item}" for item in verdict["prohibited_changes"]],
        "- Verification suggestions:",
        *[f"  - {item}" for item in verdict["verification_commands"]],
    ]
    return lines


def _decision_item_lines(idx: int, packet: dict[str, Any], verdict: dict[str, Any]) -> list[str]:
    finding = packet["finding"]
    return [
        "",
        f"### {idx}. {finding['title']}",
        f"- Finding id: {finding['id']}",
        f"- Severity: {finding['severity']} -> {verdict['recommended_final_severity']}",
        f"- Verdict: {verdict['verdict']}",
        f"- Recommended action: {verdict['recommended_action']}",
        f"- Agent next step: {verdict['agent_next_step']}",
        f"- Safe to auto suppress: {str(verdict['safe_to_auto_suppress']).lower()}",
        f"- Reason: {verdict['reason']}",
        f"- File: {packet['evidence_context']['primary_file'] or ', '.join(finding['affected_files']) or 'project'}",
        "- Inspect files:",
        *[f"  - {item}" for item in verdict["inspect_files"]],
        "- Verification suggestions:",
        *[f"  - {item}" for item in verdict["verification_commands"]],
    ]


def _dict_lines(value: object) -> list[str]:
    data = value if isinstance(value, dict) else {}
    if not data:
        return ["- none"]
    return [f"- {key}: {count}" for key, count in data.items()]
