from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SEVERITIES = {"P0", "P1", "P2", "P3", "Info"}
SOURCE_TYPES = {"runtime", "test", "docs", "example", "generated", "vendor", "cache", "unknown"}
RUBRICS = {"secret", "auth", "desktop", "mcp", "llm", "deployment", "dependency", "config", "generic"}
VERDICTS = {"confirmed", "likely_true", "needs_human_review", "should_downgrade", "false_positive"}
CONFIDENCES = {"high", "medium", "low"}
ACTIONS = {"fix", "manual_review", "downgrade", "suppress", "keep"}
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
    verdicts = _load_json(root / "ai_review.json")
    candidates = _load_json(root / "suppression_candidates.json")
    decisions_text = _load_text(root / "agent_review_decisions.md")
    if not isinstance(packets, list):
        raise SchemaValidationError("review_packets.json must be a list")
    if not isinstance(verdicts, list):
        raise SchemaValidationError("ai_review.json must be a list")
    if not isinstance(candidates, list):
        raise SchemaValidationError("suppression_candidates.json must be a list")
    if len(packets) != len(verdicts):
        raise SchemaValidationError("ai_review.json and review_packets.json must have the same length")

    packet_keys = set()
    for index, packet in enumerate(packets):
        validate_review_packet(packet, f"review_packets[{index}]")
        finding = packet["finding"]
        packet_keys.add((finding["id"], finding["fingerprint"]))
    for index, verdict in enumerate(verdicts):
        validate_ai_review_verdict(verdict, f"ai_review[{index}]")
        key = (verdict["finding_id"], verdict["fingerprint"])
        if key not in packet_keys:
            raise SchemaValidationError(f"ai_review[{index}] does not match any packet finding_id/fingerprint")
    for index, candidate in enumerate(candidates):
        validate_suppression_candidate(candidate, f"suppression_candidates[{index}]")
    for index, verdict in enumerate(verdicts):
        if verdict["finding_id"] not in decisions_text:
            raise SchemaValidationError(f"agent_review_decisions.md missing ai_review[{index}].finding_id")
    text = (root / "review_packets.json").read_text(encoding="utf-8")
    if PROVIDER_SECRET_RE.search(text):
        raise SchemaValidationError("review_packets.json contains an unredacted provider-shaped secret")
    return {"packets": len(packets), "verdicts": len(verdicts), "suppression_candidates": len(candidates)}


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
