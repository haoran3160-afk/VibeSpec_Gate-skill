from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .review_llm_packet import REQUESTED_OUTPUTS
from .review_schema import SchemaValidationError


SEVERITIES = {"P0", "P1", "P2", "P3", "Info"}
CONFIDENCES = {"high", "medium", "low"}
LAUNCH_IMPACTS = {"block", "review", "warning", "none"}
ACTIONS = {"fix", "verify_before_fix", "downgrade", "suppress_candidate", "keep"}
STUB_DISCLAIMER = "This is a contract stub, not a completed LLM security review."
UNSAFE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"exploit payload\s*:",
        r"bypass (?:authentication|auth) by",
        r"steal credentials",
        r"credential theft steps",
        r"brute force (?:attack|password|login)",
        r"persistence mechanism",
        r"destructive test plan",
        r"delete production data",
        r"exfiltrate (?:data|secrets|credentials)",
    )
]


def validate_llm_review_outputs(workspace_or_output_dir: str | Path, allow_stub: bool = True) -> dict[str, Any]:
    root = Path(workspace_or_output_dir)
    packet = _load_json(_packet_path(root))
    known_finding_ids = {
        item.get("finding_id")
        for item in packet.get("rule_findings", [])
        if isinstance(item, dict) and isinstance(item.get("finding_id"), str)
    }

    for output_name in REQUESTED_OUTPUTS:
        path = root / output_name
        if not path.exists():
            raise SchemaValidationError(f"missing required LLM output file: {output_name}")
        text = path.read_text(encoding="utf-8")
        _reject_unsafe_text(path, text)
        if not allow_stub and STUB_DISCLAIMER in text:
            raise SchemaValidationError(f"{output_name} contains the contract stub disclaimer")

    findings = _load_json(root / "security_review_findings.json")
    _validate_security_review_findings(findings, known_finding_ids, allow_stub=allow_stub)
    agent_plan = (root / "agent_fix_plan.md").read_text(encoding="utf-8")
    if not allow_stub:
        _require_markdown_section(agent_plan, "Human Confirmation Gate", "agent_fix_plan.md")
    _require_markdown_section(agent_plan, "Prohibited Changes", "agent_fix_plan.md")
    _require_markdown_section(agent_plan, "Verification Commands", "agent_fix_plan.md")
    _reject_true_suppression(findings, "security_review_findings")
    return {
        "valid": True,
        "workspace": str(root),
        "required_outputs": len(REQUESTED_OUTPUTS),
        "security_findings": len(findings.get("findings", [])),
        "model_api_called": False,
        "allow_stub": allow_stub,
    }


def _validate_security_review_findings(value: Any, known_finding_ids: set[str], allow_stub: bool) -> None:
    if not isinstance(value, dict):
        raise SchemaValidationError("security_review_findings.json must be an object")
    if value.get("schema_version") != "1.0":
        raise SchemaValidationError("security_review_findings.schema_version must be 1.0")
    findings = value.get("findings")
    if not isinstance(findings, list):
        raise SchemaValidationError("security_review_findings.findings must be a list")
    for index, finding in enumerate(findings):
        path = f"security_review_findings.findings[{index}]"
        if not isinstance(finding, dict):
            raise SchemaValidationError(f"{path} must be an object")
        finding_id = finding.get("finding_id")
        if not isinstance(finding_id, str) or not finding_id:
            raise SchemaValidationError(f"{path}.finding_id must be a non-empty string")
        if finding_id not in known_finding_ids and finding.get("new_llm_finding") is not True:
            raise SchemaValidationError(f"{path}.finding_id must come from llm_review_packet.json or set new_llm_finding=true")
        _require_enum(finding.get("severity"), SEVERITIES, f"{path}.severity")
        _require_enum(finding.get("confidence"), CONFIDENCES, f"{path}.confidence")
        _require_enum(finding.get("launch_impact"), LAUNCH_IMPACTS, f"{path}.launch_impact")
        _require_enum(finding.get("recommended_action"), ACTIONS, f"{path}.recommended_action")
        if finding.get("safe_to_auto_suppress") is not False:
            raise SchemaValidationError(f"{path}.safe_to_auto_suppress must be false")
        _require_string_list(finding.get("evidence_files"), f"{path}.evidence_files")
        if not allow_stub and not any(item != "llm_review_packet.json" for item in finding["evidence_files"]):
            raise SchemaValidationError(f"{path}.evidence_files must cite a concrete evidence file for final outputs")
        _require_string_list(finding.get("missing_evidence"), f"{path}.missing_evidence")
        for key in ("title", "reasoning_summary"):
            if not isinstance(finding.get(key), str) or not finding[key].strip():
                raise SchemaValidationError(f"{path}.{key} must be a non-empty string")


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SchemaValidationError(f"missing required file: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise SchemaValidationError(f"{path.name} is not valid JSON: {exc}") from exc


def _packet_path(root: Path) -> Path:
    direct = root / "llm_review_packet.json"
    if direct.exists():
        return direct
    parent = root.parent / "llm_review_packet.json"
    if parent.exists():
        return parent
    return direct


def _reject_unsafe_text(path: Path, text: str) -> None:
    for pattern in UNSAFE_PATTERNS:
        if pattern.search(text):
            raise SchemaValidationError(f"{path.name} contains unsafe offensive guidance: {pattern.pattern}")


def _reject_true_suppression(value: Any, path: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key == "safe_to_auto_suppress" and item is True:
                raise SchemaValidationError(f"{child} must not be true")
            _reject_true_suppression(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_true_suppression(item, f"{path}[{index}]")


def _require_markdown_section(text: str, section: str, path: str) -> None:
    if not re.search(rf"^##\s+{re.escape(section)}\s*$", text, re.MULTILINE | re.IGNORECASE):
        raise SchemaValidationError(f"{path} must contain a '{section}' section")


def _require_enum(value: Any, allowed: set[str], path: str) -> None:
    if not isinstance(value, str) or value not in allowed:
        raise SchemaValidationError(f"{path} must be one of: {', '.join(sorted(allowed))}")


def _require_string_list(value: Any, path: str) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SchemaValidationError(f"{path} must be a list of strings")
