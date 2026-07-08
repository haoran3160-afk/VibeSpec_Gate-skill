from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .risk_model import Finding, ProjectProfile


PROVIDER_SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|sk_(?:test|live)_[A-Za-z0-9]{16,}|"
    r"gh[pousr]_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[0-9A-Za-z-]{20,}|"
    r"-----BEGIN (?:RSA |EC |OPENSSH |)?PRIVATE KEY-----)",
    re.I,
)
GENERIC_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|private[_-]?key|database[_-]?url)\s*[:=]\s*['\"]?([^'\"\s]{8,})"
)
LOCATION_RE = re.compile(r"^(?P<path>.*?)(?::(?P<line>\d+))?$")

SECURITY_SIGNAL_WORDS = [
    "auth",
    "session",
    "middleware",
    "allowlist",
    "validate",
    "schema",
    "safeparse",
    "contextisolation",
    "nodeintegration",
    "workspace",
    "path.resolve",
    "startswith",
    "approval",
    "confirm",
    "audit",
    "logger",
    "user-selected",
]
RISK_SIGNAL_WORDS = [
    "delete",
    "writefile",
    "writefilesync",
    "unlink",
    "subprocess",
    "exec(",
    "shell.openexternal",
    "ipcmain",
    "tool_call",
    "call_tool",
    "openai",
    "anthropic",
    "password",
    "token",
    "apikey",
    "api_key",
]


def build_review_packet(
    root: Path,
    profile: ProjectProfile,
    finding: Finding,
    max_snippet_lines: int = 80,
) -> dict[str, Any]:
    primary = finding.affected_files[0] if finding.affected_files else ""
    context = evidence_context(root, primary, finding.source_type, max_snippet_lines)
    packet = {
        "project_profile": {
            "project_type": profile.project_type,
            "technologies": profile.technologies,
            "risk_level": profile.risk_level,
            "profile_evidence": profile.profile_evidence,
        },
        "finding": {
            "id": finding.id,
            "title": finding.title,
            "severity": finding.severity,
            "category": finding.category,
            "confidence": finding.confidence,
            "source_type": finding.source_type,
            "gate_relevant": finding.gate_relevant,
            "fingerprint": finding.fingerprint,
            "affected_files": finding.affected_files,
            "evidence": redact_text(finding.evidence),
            "technical_reason": finding.technical_reason,
        },
        "evidence_context": context,
        "rubric": rubric_for(finding),
    }
    return redact_value(packet)


def evidence_context(root: Path, location: str, source_type: str, max_snippet_lines: int) -> dict[str, Any]:
    rel_path, line_no = split_location(location)
    context = {
        "primary_file": rel_path,
        "snippet": "",
        "snippet_start_line": 0,
        "snippet_end_line": 0,
        "nearby_security_signals": [],
        "nearby_risk_signals": [],
    }
    if not rel_path or source_type in {"generated", "vendor", "cache"}:
        return context
    path = (root / rel_path).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return context
    if not path.exists() or not path.is_file():
        return context
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return context
    if not lines:
        return context
    max_lines = max(1, min(max_snippet_lines, 80))
    if line_no:
        start = max(1, line_no - 30)
        end = min(len(lines), line_no + 30)
        if end - start + 1 > max_lines:
            extra = max_lines // 2
            start = max(1, line_no - extra)
            end = min(len(lines), start + max_lines - 1)
    else:
        start = 1
        end = min(len(lines), max_lines)
    snippet = "\n".join(lines[start - 1 : end])
    redacted = redact_text(snippet)
    lowered = redacted.lower()
    context.update(
        {
            "snippet": redacted,
            "snippet_start_line": start,
            "snippet_end_line": end,
            "nearby_security_signals": sorted({word for word in SECURITY_SIGNAL_WORDS if word.lower() in lowered}),
            "nearby_risk_signals": sorted({word for word in RISK_SIGNAL_WORDS if word.lower() in lowered}),
        }
    )
    return context


def rubric_for(finding: Finding) -> str:
    combined = f"{finding.category} {finding.title}".lower()
    if "secret" in combined or "token" in combined or "api key" in combined or "apikey" in combined:
        return "secret"
    if "desktop" in combined or "electron" in combined:
        return "desktop"
    if "mcp" in combined or "ipc" in combined:
        return "mcp"
    if "llm" in combined or "agent" in combined or "prompt" in combined:
        return "llm"
    if re.search(r"\b(auth|authentication|authorization)\b", combined) or any(
        word in combined for word in ("owner", "rls", "firebase", "data access", "api route")
    ):
        return "auth"
    if "deploy" in combined or "cors" in combined or "header" in combined:
        return "deployment"
    if "depend" in combined or "lockfile" in combined:
        return "dependency"
    if "config" in combined or "debug" in combined:
        return "config"
    return "generic"


def packet_text(packet: dict[str, Any]) -> str:
    finding = packet["finding"]
    context = packet["evidence_context"]
    return " ".join(
        [
            str(finding.get("title", "")),
            str(finding.get("evidence", "")),
            str(finding.get("technical_reason", "")),
            str(context.get("snippet", "")),
            " ".join(context.get("nearby_security_signals", [])),
            " ".join(context.get("nearby_risk_signals", [])),
        ]
    ).lower()


def provider_secret_signal(text: str, title: str) -> bool:
    return bool(PROVIDER_SECRET_RE.search(text)) or any(
        word in title
        for word in ("openai api key", "anthropic api key", "stripe secret", "github token", "private key", "database url", "service role")
    )


def looks_placeholder_or_example(text: str) -> bool:
    return any(word in text for word in ("placeholder", "example", "your_", "replace_me", "changeme", ".env.example", "sample"))


def split_location(location: str) -> tuple[str, int | None]:
    match = LOCATION_RE.match(location or "")
    if not match:
        return location, None
    path = match.group("path") or ""
    line = int(match.group("line")) if match.group("line") else None
    return path, line


def redact_text(text: str) -> str:
    redacted = PROVIDER_SECRET_RE.sub(_mask_match, text)
    return GENERIC_SECRET_RE.sub(lambda m: f"{m.group(1)}=***REDACTED***", redacted)


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_value(item) for key, item in value.items()}
    return value


def _mask_match(match: re.Match[str]) -> str:
    value = match.group(0)
    if value.startswith("-----BEGIN"):
        return "-----BEGIN ***REDACTED*** PRIVATE KEY-----"
    if len(value) <= 10:
        return "***REDACTED***"
    return f"{value[:4]}...{value[-4:]}"
