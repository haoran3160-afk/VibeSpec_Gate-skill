from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .risk_model import Finding, SEVERITY_ORDER
from .source_classifier import source_type_for_path


@dataclass
class Suppression:
    fingerprint: str
    reason: str
    expires: str = ""
    reviewed_by: str = ""

    @property
    def is_expired(self) -> bool:
        if not self.expires:
            return False
        try:
            return date.fromisoformat(self.expires) < date.today()
        except ValueError:
            return True


def process_findings(root: Path, findings: list[Finding], suppression_file: str | None = None) -> list[Finding]:
    normalized = [_normalize_finding(root, finding) for finding in findings]
    deduped = _dedupe(normalized)
    grouped = _group_similar(deduped)
    suppressions = _load_suppressions(root, suppression_file)
    return [_apply_suppression(finding, suppressions) for finding in grouped]


def _normalize_finding(root: Path, finding: Finding) -> Finding:
    primary = finding.affected_files[0] if finding.affected_files else str(root)
    finding.source_type = source_type_for_path(primary)
    if finding.source_type in {"docs", "example", "test"}:
        finding.confidence = "suspected"
        if finding.severity == "P0":
            finding.severity = "P1"
        elif finding.severity == "P1":
            finding.severity = "P2"
    finding.gate_relevant = _is_gate_relevant(finding)
    finding.fingerprint = finding.fingerprint or fingerprint_for(finding)
    finding.codex_fix_prompt = _refresh_fix_prompt_if_needed(finding)
    return finding


def _is_gate_relevant(finding: Finding) -> bool:
    if finding.suppressed or finding.severity == "Info":
        return False
    return finding.source_type not in {"generated", "vendor", "cache"}


def fingerprint_for(finding: Finding) -> str:
    primary = finding.affected_files[0] if finding.affected_files else "project"
    path, line = _split_location(primary)
    normalized_title = re.sub(r"[^a-z0-9]+", "-", finding.title.lower()).strip("-")
    evidence_type = re.sub(r"[^a-z0-9]+", "-", finding.category.lower()).strip("-")
    return f"VSG:{finding.category}:{normalized_title}:{path}:{line}:{evidence_type}"


def _split_location(location: str) -> tuple[str, str]:
    match = re.match(r"(.+):(\d+)$", location)
    if match:
        return match.group(1), match.group(2)
    return location, "file"


def _dedupe(findings: list[Finding]) -> list[Finding]:
    by_fp: dict[str, Finding] = {}
    by_secret_line: dict[str, Finding] = {}
    for finding in findings:
        secret_key = _secret_line_key(finding)
        if secret_key:
            existing_secret = by_secret_line.get(secret_key)
            if existing_secret:
                chosen = _choose_more_specific(existing_secret, finding)
                by_secret_line[secret_key] = chosen
                by_fp[existing_secret.fingerprint] = chosen
                by_fp[finding.fingerprint] = chosen
                continue
            by_secret_line[secret_key] = finding
        existing = by_fp.get(finding.fingerprint)
        if not existing:
            by_fp[finding.fingerprint] = finding
            continue
        if SEVERITY_ORDER.get(finding.severity, 99) < SEVERITY_ORDER.get(existing.severity, 99):
            finding.references = sorted(set(finding.references + existing.references))
            by_fp[finding.fingerprint] = finding
        else:
            existing.references = sorted(set(existing.references + finding.references))
            existing.group_count += 1
            existing.grouped_files.extend(finding.affected_files)
    unique: dict[str, Finding] = {}
    for finding in by_fp.values():
        unique[finding.fingerprint] = finding
    return list(unique.values())


def _secret_line_key(finding: Finding) -> str:
    if finding.category != "Secrets" or not finding.affected_files:
        return ""
    primary = finding.affected_files[0]
    path, line = _split_location(primary)
    if line == "file":
        return ""
    return f"secret:{path}:{line}"


def _choose_more_specific(left: Finding, right: Finding) -> Finding:
    if SEVERITY_ORDER.get(right.severity, 99) < SEVERITY_ORDER.get(left.severity, 99):
        return right
    if SEVERITY_ORDER.get(left.severity, 99) < SEVERITY_ORDER.get(right.severity, 99):
        return left
    specific_terms = ("service role", "private key", "openai", "anthropic", "stripe", "github token", "database url")
    left_score = sum(term in left.title.lower() for term in specific_terms)
    right_score = sum(term in right.title.lower() for term in specific_terms)
    return right if right_score > left_score else left


def _group_similar(findings: list[Finding]) -> list[Finding]:
    grouped: dict[tuple[str, str, str, str], list[Finding]] = {}
    passthrough: list[Finding] = []
    for finding in findings:
        if finding.confidence != "suspected" or finding.severity not in {"P1", "P2"}:
            passthrough.append(finding)
            continue
        primary = finding.affected_files[0] if finding.affected_files else "project"
        directory = str(Path(_split_location(primary)[0]).parent).replace("\\", "/")
        key = (finding.category, finding.title, finding.severity, finding.source_type + ":" + directory)
        grouped.setdefault(key, []).append(finding)

    for items in grouped.values():
        if len(items) < 3:
            passthrough.extend(items)
            continue
        first = items[0]
        files: list[str] = []
        for item in items:
            files.extend(item.affected_files)
        first.group_count = len(items)
        first.grouped_files = sorted(set(files))
        first.affected_files = first.grouped_files[:10]
        first.evidence = f"{len(items)} similar suspected findings grouped; showing representative files."
        first.fingerprint = fingerprint_for(first)
        passthrough.append(first)
    return passthrough


def _load_suppressions(root: Path, suppression_file: str | None) -> dict[str, Suppression]:
    candidates: list[Path] = []
    if suppression_file:
        candidates.append(Path(suppression_file))
    candidates.extend([root / "vibespec_gate.suppressions.json", root / ".vibespecignore"])
    suppressions: dict[str, Suppression] = {}
    for path in candidates:
        if not path.exists() or not path.is_file():
            continue
        if path.name == ".vibespecignore":
            for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                suppressions[line] = Suppression(fingerprint=line, reason=".vibespecignore")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data:
            fingerprint = str(item.get("fingerprint", "")).strip()
            reason = str(item.get("reason", "")).strip()
            if not fingerprint or not reason:
                continue
            suppressions[fingerprint] = Suppression(
                fingerprint=fingerprint,
                reason=reason,
                expires=str(item.get("expires", "")),
                reviewed_by=str(item.get("reviewed_by", "")),
            )
    return suppressions


def _apply_suppression(finding: Finding, suppressions: dict[str, Suppression]) -> Finding:
    suppression = suppressions.get(finding.fingerprint)
    if not suppression or suppression.is_expired:
        return finding
    finding.suppressed = True
    finding.suppression_reason = suppression.reason
    finding.suppression_expires = suppression.expires
    return finding


def _refresh_fix_prompt_if_needed(finding: Finding) -> str:
    from .fix_prompt_builder import build_fix_prompt

    if finding.severity == "Info" or finding.source_type in {"generated", "vendor", "cache"}:
        return ""
    return build_fix_prompt(
        title=finding.title,
        risk=finding.why_it_matters_for_beginner or finding.technical_reason,
        files=finding.affected_files,
        fix=finding.recommended_fix,
        tests=finding.verification_steps,
        confidence=finding.confidence,
        source_type=finding.source_type,
        category=finding.category,
    )
