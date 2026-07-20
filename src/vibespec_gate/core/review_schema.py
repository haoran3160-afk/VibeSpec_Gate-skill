from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .coverage import coverage_from_dict


SEVERITIES = {"P0", "P1", "P2", "P3", "Info"}
SOURCE_TYPES = {"runtime", "test", "docs", "example", "generated", "vendor", "cache", "unknown"}
RUBRICS = {"secret", "auth", "desktop", "mcp", "llm", "deployment", "dependency", "config", "generic"}
VERDICTS = {"confirmed", "likely_true", "needs_human_review", "should_downgrade", "false_positive"}
CONFIDENCES = {"high", "medium", "low"}
ACTIONS = {"fix", "manual_review", "downgrade", "suppress", "keep"}
DECISION_TYPES = {
    "must_confirm_before_fix",
    "fix_after_confirmation",
    "downgrade_candidate",
    "suppression_candidate",
    "false_positive_candidate",
    "informational_decision",
}
AGENT_NEXT_STEPS = {
    "confirm_and_prepare_fix",
    "prepare_fix_task",
    "verify_before_fix",
    "confirm_before_suppress_or_downgrade",
}
PROVIDER_SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|sk_(?:test|live)_[A-Za-z0-9]{16,}|"
    r"gh[pousr]_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[0-9A-Za-z-]{20,})"
)


class SchemaValidationError(ValueError):
    pass


def validate_review_output_dir(output_dir: str | Path) -> dict[str, int]:
    root = Path(output_dir)
    packets = _load_json(root / "review_packets.json")
    llm_packet = _load_json(root / "llm_review_packet.json")
    verdicts = _load_json(root / "ai_review.json")
    decision_output = _load_json(root / "agent_review_decisions.json")
    candidates = _load_json(root / "suppression_candidates.json")
    decisions_text = _load_text(root / "agent_review_decisions.md")
    summary_text = _load_text(root / "ai_review_summary.md")
    if not isinstance(packets, list):
        raise SchemaValidationError("review_packets.json must be a list")
    if not isinstance(verdicts, list):
        raise SchemaValidationError("ai_review.json must be a list")
    decisions = _validate_decision_output_object(decision_output)
    if not isinstance(candidates, list):
        raise SchemaValidationError("suppression_candidates.json must be a list")
    if len(packets) != len(verdicts):
        raise SchemaValidationError("ai_review.json and review_packets.json must have the same length")
    validate_llm_review_packet(llm_packet, len(packets))
    _validate_coverage_matches_review_packet(decision_output, llm_packet)
    if len(decisions) != len(verdicts):
        raise SchemaValidationError("agent_review_decisions.json must cover every reviewed finding")

    packet_keys = set()
    verdict_by_key = {}
    for index, packet in enumerate(packets):
        validate_review_packet(packet, f"review_packets[{index}]")
        finding = packet["finding"]
        packet_keys.add((finding["id"], finding["fingerprint"]))
    for index, verdict in enumerate(verdicts):
        validate_ai_review_verdict(verdict, f"ai_review[{index}]")
        key = (verdict["finding_id"], verdict["fingerprint"])
        if key not in packet_keys:
            raise SchemaValidationError(f"ai_review[{index}] does not match any packet finding_id/fingerprint")
        verdict_by_key[key] = verdict
    decision_keys = set()
    must_review_count = 0
    downgrade_count = 0
    for index, decision in enumerate(decisions):
        validate_agent_review_decision(decision, f"agent_review_decisions[{index}]")
        key = (decision["finding_id"], decision["fingerprint"])
        if key not in verdict_by_key:
            raise SchemaValidationError(f"agent_review_decisions[{index}] does not match any verdict")
        if key in decision_keys:
            raise SchemaValidationError(f"agent_review_decisions[{index}] duplicates finding_id/fingerprint")
        decision_keys.add(key)
        _validate_decision_matches_verdict(decision, verdict_by_key[key], f"agent_review_decisions[{index}]")
        must_review_count += int(decision["must_review"])
        downgrade_count += int(decision["decision_type"] == "downgrade_candidate")
    if decision_keys != set(verdict_by_key):
        raise SchemaValidationError("agent_review_decisions.json must cover every ai_review verdict exactly once")
    _validate_decision_output_summary(decision_output, len(decisions), must_review_count, downgrade_count, len(candidates))
    for index, candidate in enumerate(candidates):
        validate_suppression_candidate(candidate, f"suppression_candidates[{index}]")
    for index, verdict in enumerate(verdicts):
        if verdict["finding_id"] not in decisions_text:
            raise SchemaValidationError(f"agent_review_decisions.md missing ai_review[{index}].finding_id")
    _validate_summary_count(summary_text, "Must review count", must_review_count)
    _validate_summary_count(summary_text, "Agent decision count", len(decisions))
    _validate_summary_count(summary_text, "Downgrade candidate count", downgrade_count)
    _validate_summary_count(summary_text, "Suppression candidate count", len(candidates))
    _validate_summary_count(summary_text, "Total findings", decision_output["summary"]["total_findings"])
    _validate_summary_count(
        summary_text,
        "Invalid severity count",
        decision_output["summary"]["invalid_severity_count"],
    )
    text = (root / "review_packets.json").read_text(encoding="utf-8")
    if PROVIDER_SECRET_RE.search(text):
        raise SchemaValidationError("review_packets.json contains an unredacted provider-shaped secret")
    return {
        "packets": len(packets),
        "verdicts": len(verdicts),
        "agent_decisions": len(decisions),
        "suppression_candidates": len(candidates),
    }


def validate_review_packet(packet: Any, path: str = "packet") -> None:
    _require_dict(packet, path)
    _require_dict(packet.get("project_profile"), f"{path}.project_profile")
    _require_list(packet["project_profile"].get("technologies"), f"{path}.project_profile.technologies", str)
    _require_list(packet["project_profile"].get("profile_evidence"), f"{path}.project_profile.profile_evidence", str)
    _require_type(packet["project_profile"].get("project_type"), str, f"{path}.project_profile.project_type")
    _require_type(packet["project_profile"].get("risk_level"), str, f"{path}.project_profile.risk_level")

    finding = packet.get("finding")
    _require_dict(finding, f"{path}.finding")
    for key in ("id", "title", "category", "confidence", "fingerprint", "evidence", "technical_reason"):
        _require_type(finding.get(key), str, f"{path}.finding.{key}")
    _require_enum(finding.get("severity"), SEVERITIES, f"{path}.finding.severity")
    _require_enum(finding.get("source_type"), SOURCE_TYPES, f"{path}.finding.source_type")
    _require_type(finding.get("gate_relevant"), bool, f"{path}.finding.gate_relevant")
    _require_list(finding.get("affected_files"), f"{path}.finding.affected_files", str)

    context = packet.get("evidence_context")
    _require_dict(context, f"{path}.evidence_context")
    for key in ("primary_file", "snippet"):
        _require_type(context.get(key), str, f"{path}.evidence_context.{key}")
    for key in ("snippet_start_line", "snippet_end_line"):
        _require_type(context.get(key), int, f"{path}.evidence_context.{key}")
    _require_list(context.get("nearby_security_signals"), f"{path}.evidence_context.nearby_security_signals", str)
    _require_list(context.get("nearby_risk_signals"), f"{path}.evidence_context.nearby_risk_signals", str)
    if len(context["snippet"].splitlines()) > 80:
        raise SchemaValidationError(f"{path}.evidence_context.snippet exceeds 80 lines")
    _require_enum(packet.get("rubric"), RUBRICS, f"{path}.rubric")


def validate_ai_review_verdict(verdict: Any, path: str = "verdict") -> None:
    _require_dict(verdict, path)
    for key in ("finding_id", "fingerprint", "reason", "rubric", "reviewer"):
        _require_type(verdict.get(key), str, f"{path}.{key}")
    _require_enum(verdict.get("verdict"), VERDICTS, f"{path}.verdict")
    _require_enum(verdict.get("confidence"), CONFIDENCES, f"{path}.confidence")
    _require_enum(verdict.get("recommended_final_severity"), SEVERITIES, f"{path}.recommended_final_severity")
    _require_type(verdict.get("gate_relevant"), bool, f"{path}.gate_relevant")
    _require_list(verdict.get("missing_evidence"), f"{path}.missing_evidence", str)
    _require_list(verdict.get("human_review_questions"), f"{path}.human_review_questions", str)
    _require_enum(verdict.get("recommended_action"), ACTIONS, f"{path}.recommended_action")
    _require_enum(verdict.get("agent_next_step"), AGENT_NEXT_STEPS, f"{path}.agent_next_step")
    _require_list(verdict.get("inspect_files"), f"{path}.inspect_files", str)
    _require_list(verdict.get("prohibited_changes"), f"{path}.prohibited_changes", str)
    _require_list(verdict.get("verification_commands"), f"{path}.verification_commands", str)
    if verdict.get("reviewer") != "rule-based":
        raise SchemaValidationError(f"{path}.reviewer must be rule-based")
    if verdict.get("safe_to_auto_suppress") is not False:
        raise SchemaValidationError(f"{path}.safe_to_auto_suppress must be false")
    _validate_agent_contract(verdict, path)


def validate_suppression_candidate(candidate: Any, path: str = "candidate") -> None:
    _require_dict(candidate, path)
    for key in ("finding_id", "fingerprint", "title", "source_type", "reason", "suggested_expiry"):
        _require_type(candidate.get(key), str, f"{path}.{key}")
    _require_type(candidate.get("requires_human_confirmation"), bool, f"{path}.requires_human_confirmation")
    if candidate.get("safe_to_auto_suppress") is not False:
        raise SchemaValidationError(f"{path}.safe_to_auto_suppress must be false")


def validate_agent_review_decision(decision: Any, path: str = "decision") -> None:
    _require_dict(decision, path)
    for key in (
        "decision_id",
        "source_output",
        "finding_id",
        "fingerprint",
        "title",
        "rubric",
        "verdict",
        "recommended_action",
        "recommended_final_severity",
        "agent_next_step",
        "decision_type",
        "reason",
    ):
        _require_type(decision.get(key), str, f"{path}.{key}")
    _require_enum(decision.get("rubric"), RUBRICS, f"{path}.rubric")
    _require_enum(decision.get("verdict"), VERDICTS, f"{path}.verdict")
    _require_enum(decision.get("recommended_action"), ACTIONS, f"{path}.recommended_action")
    _require_enum(decision.get("recommended_final_severity"), SEVERITIES, f"{path}.recommended_final_severity")
    _require_enum(decision.get("agent_next_step"), AGENT_NEXT_STEPS, f"{path}.agent_next_step")
    _require_enum(decision.get("decision_type"), DECISION_TYPES, f"{path}.decision_type")
    _require_type(decision.get("must_review"), bool, f"{path}.must_review")
    _require_type(decision.get("blocks_launch"), bool, f"{path}.blocks_launch")
    _require_type(decision.get("safe_for_agent_fix"), bool, f"{path}.safe_for_agent_fix")
    _require_list(decision.get("inspect_files"), f"{path}.inspect_files", str)
    _require_list(decision.get("prohibited_changes"), f"{path}.prohibited_changes", str)
    _require_list(decision.get("verification_commands"), f"{path}.verification_commands", str)
    if decision.get("safe_to_auto_suppress") is not False:
        raise SchemaValidationError(f"{path}.safe_to_auto_suppress must be false")
    if decision.get("source_output") != "ai_review.json":
        raise SchemaValidationError(f"{path}.source_output must be ai_review.json")
    if decision["decision_type"] in {"downgrade_candidate", "suppression_candidate", "false_positive_candidate"}:
        if decision["must_review"] is not False:
            raise SchemaValidationError(f"{path}.must_review must be false for downgrade/suppression/false-positive decisions")


def validate_llm_review_packet(packet: Any, expected_findings: int, path: str = "llm_review_packet") -> None:
    _require_dict(packet, path)
    if packet.get("schema_version") != "1.0":
        raise SchemaValidationError(f"{path}.schema_version must be 1.0")
    for key in (
        "project_profile",
        "product_context",
        "auth_and_data_flow",
    ):
        _require_dict(packet.get(key), f"{path}.{key}")
    for key in (
        "sensitive_assets",
        "attack_surfaces",
        "agent_tool_surfaces",
        "evidence_files",
        "rule_findings",
        "review_questions",
        "requested_outputs",
        "safety_boundaries",
    ):
        _require_list(packet.get(key), f"{path}.{key}", object)
    required_outputs = {
        "nontechnical_user_summary.md",
        "launch_risk_report.md",
        "security_review_findings.json",
        "agent_fix_plan.md",
        "retest_checklist.md",
    }
    if set(packet["requested_outputs"]) != required_outputs:
        raise SchemaValidationError(f"{path}.requested_outputs must match the LLM output contract")
    if len(packet["rule_findings"]) != expected_findings:
        raise SchemaValidationError(f"{path}.rule_findings must cover every reviewed finding")
    for index, finding in enumerate(packet["rule_findings"]):
        _require_dict(finding, f"{path}.rule_findings[{index}]")
        for key in ("finding_id", "fingerprint", "title", "rubric", "evidence_role"):
            _require_type(finding.get(key), str, f"{path}.rule_findings[{index}].{key}")
        if finding.get("evidence_role") != "baseline_hint_not_final_judgment":
            raise SchemaValidationError(f"{path}.rule_findings[{index}].evidence_role must mark rule findings as hints")
    if not packet["review_questions"]:
        raise SchemaValidationError(f"{path}.review_questions must not be empty")


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SchemaValidationError(f"missing required file: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise SchemaValidationError(f"{path.name} is not valid JSON: {exc}") from exc


def _load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SchemaValidationError(f"missing required file: {path.name}") from exc


def _validate_decision_output_object(value: Any) -> list[dict[str, Any]]:
    _require_dict(value, "agent_review_decisions")
    _require_type(value.get("schema_version"), str, "agent_review_decisions.schema_version")
    if value["schema_version"] != "1.0":
        raise SchemaValidationError("agent_review_decisions.schema_version must be 1.0")
    _require_type(value.get("reviewer"), str, "agent_review_decisions.reviewer")
    if value["reviewer"] != "rule-based":
        raise SchemaValidationError("agent_review_decisions.reviewer must be rule-based")
    _require_type(value.get("generated_by"), str, "agent_review_decisions.generated_by")
    if value["generated_by"] != "vibespec-gate review":
        raise SchemaValidationError("agent_review_decisions.generated_by must be vibespec-gate review")
    _require_dict(value.get("summary"), "agent_review_decisions.summary")
    decisions = value.get("decisions")
    if not isinstance(decisions, list):
        raise SchemaValidationError("agent_review_decisions.decisions must be a list")
    return decisions


def _validate_decision_output_summary(
    value: dict[str, Any],
    decision_count: int,
    must_review_count: int,
    downgrade_count: int,
    suppression_count: int,
) -> None:
    summary = value["summary"]
    expected = {
        "agent_decision_count": decision_count,
        "reviewed_findings": decision_count,
        "must_review_count": must_review_count,
        "downgrade_candidate_count": downgrade_count,
        "suppression_candidate_count": suppression_count,
    }
    for key, count in expected.items():
        actual = summary.get(key)
        if actual != count:
            raise SchemaValidationError(f"agent_review_decisions.summary.{key} expected {count}, found {actual}")
    total_findings = summary.get("total_findings")
    if not isinstance(total_findings, int) or isinstance(total_findings, bool) or total_findings < 0:
        raise SchemaValidationError("agent_review_decisions.summary.total_findings must be a non-negative integer")
    input_severity_counts = summary.get("input_severity_counts")
    if not isinstance(input_severity_counts, dict):
        raise SchemaValidationError("agent_review_decisions.summary.input_severity_counts must be an object")
    if any(
        not isinstance(severity, str)
        or not severity
        or not isinstance(count, int)
        or isinstance(count, bool)
        or count < 0
        for severity, count in input_severity_counts.items()
    ):
        raise SchemaValidationError("agent_review_decisions.summary.input_severity_counts is invalid")
    if sum(input_severity_counts.values()) > total_findings:
        raise SchemaValidationError("agent_review_decisions.summary.input_severity_counts exceeds total_findings")
    invalid_severity_count = summary.get("invalid_severity_count")
    if (
        not isinstance(invalid_severity_count, int)
        or isinstance(invalid_severity_count, bool)
        or invalid_severity_count < 0
    ):
        raise SchemaValidationError("agent_review_decisions.summary.invalid_severity_count must be a non-negative integer")
    expected_invalid_count = sum(
        count for severity, count in input_severity_counts.items() if severity not in SEVERITIES
    )
    if invalid_severity_count != expected_invalid_count:
        raise SchemaValidationError(
            "agent_review_decisions.summary.invalid_severity_count does not match input_severity_counts"
        )


def _validate_coverage_matches_review_packet(
    decision_output: dict[str, Any], llm_packet: dict[str, Any]
) -> None:
    coverage = decision_output["summary"].get("coverage")
    if coverage is not None and coverage_from_dict(coverage).to_dict() != coverage:
        raise SchemaValidationError("agent_review_decisions.summary.coverage is invalid")
    packet_coverage = llm_packet["project_profile"].get("coverage")
    if packet_coverage is not None and coverage_from_dict(packet_coverage).to_dict() != packet_coverage:
        raise SchemaValidationError("llm_review_packet.project_profile.coverage is invalid")
    if coverage is not None and packet_coverage is not None and coverage != packet_coverage:
        raise SchemaValidationError("agent_review_decisions.summary.coverage must match llm_review_packet project coverage")


def _require_dict(value: Any, path: str) -> None:
    if not isinstance(value, dict):
        raise SchemaValidationError(f"{path} must be an object")


def _require_type(value: Any, expected: type, path: str) -> None:
    if not isinstance(value, expected):
        raise SchemaValidationError(f"{path} must be {expected.__name__}")


def _require_list(value: Any, path: str, item_type: type) -> None:
    if not isinstance(value, list):
        raise SchemaValidationError(f"{path} must be a list")
    for index, item in enumerate(value):
        if not isinstance(item, item_type):
            raise SchemaValidationError(f"{path}[{index}] must be {item_type.__name__}")


def _require_enum(value: Any, allowed: set[str], path: str) -> None:
    if not isinstance(value, str) or value not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise SchemaValidationError(f"{path} must be one of: {allowed_text}")


def _validate_agent_contract(verdict: dict[str, Any], path: str) -> None:
    if verdict["recommended_action"] == "fix" and verdict["verdict"] in {"confirmed", "likely_true"}:
        if verdict["agent_next_step"] not in {"confirm_and_prepare_fix", "prepare_fix_task"}:
            raise SchemaValidationError(f"{path}.agent_next_step must prepare a confirmed fix task")
        if not verdict["inspect_files"]:
            raise SchemaValidationError(f"{path}.inspect_files must name files to inspect before fixing")
        if not verdict["verification_commands"]:
            raise SchemaValidationError(f"{path}.verification_commands must include fix verification suggestions")
    if verdict["verdict"] == "needs_human_review" and verdict["agent_next_step"] != "verify_before_fix":
        raise SchemaValidationError(f"{path}.agent_next_step must be verify_before_fix for human-review verdicts")
    if verdict["verdict"] in {"false_positive", "should_downgrade"}:
        if verdict["agent_next_step"] != "confirm_before_suppress_or_downgrade":
            raise SchemaValidationError(f"{path}.agent_next_step must require confirmation before downgrade/suppression")


def _validate_decision_matches_verdict(decision: dict[str, Any], verdict: dict[str, Any], path: str) -> None:
    for key in (
        "verdict",
        "recommended_action",
        "recommended_final_severity",
        "agent_next_step",
        "inspect_files",
        "prohibited_changes",
        "verification_commands",
        "safe_to_auto_suppress",
        "reason",
        "rubric",
    ):
        if decision[key] != verdict[key]:
            raise SchemaValidationError(f"{path}.{key} must match ai_review verdict")
    expected_must_review = (
        verdict["recommended_action"] in {"fix", "manual_review"}
        and verdict["verdict"] in {"confirmed", "likely_true", "needs_human_review"}
        and verdict["recommended_final_severity"] in {"P0", "P1"}
    )
    if decision["must_review"] is not expected_must_review:
        raise SchemaValidationError(f"{path}.must_review does not match queue semantics")
    expected_blocks = expected_must_review and verdict["recommended_final_severity"] in {"P0", "P1"}
    if decision["blocks_launch"] is not expected_blocks:
        raise SchemaValidationError(f"{path}.blocks_launch does not match queue severity semantics")
    expected_safe_fix = decision["decision_type"] == "fix_after_confirmation"
    if decision["safe_for_agent_fix"] is not expected_safe_fix:
        raise SchemaValidationError(f"{path}.safe_for_agent_fix does not match decision type")


def _validate_summary_count(summary_text: str, label: str, expected: int) -> None:
    pattern = rf"^- {re.escape(label)}: (?P<count>\d+)$"
    for line in summary_text.splitlines():
        match = re.match(pattern, line)
        if match:
            actual = int(match.group("count"))
            if actual != expected:
                raise SchemaValidationError(f"ai_review_summary.md {label} expected {expected}, found {actual}")
            return
    raise SchemaValidationError(f"ai_review_summary.md missing {label}")
