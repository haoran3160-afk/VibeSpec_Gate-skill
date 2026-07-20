from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .coverage import EvidenceCoverage, insufficient_coverage


SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "Info": 4}
SEVERITY_WEIGHTS = {"P0": 40, "P1": 20, "P2": 6, "P3": 1, "Info": 0}


@dataclass
class Finding:
    id: str
    title: str
    severity: str
    category: str
    affected_files: list[str] = field(default_factory=list)
    evidence: str = ""
    why_it_matters_for_beginner: str = ""
    technical_reason: str = ""
    recommended_fix: str = ""
    codex_fix_prompt: str = ""
    verification_steps: list[str] = field(default_factory=list)
    false_positive_notes: str = ""
    references: list[str] = field(default_factory=list)
    confidence: str = "confirmed"
    source_type: str = "runtime"
    fingerprint: str = ""
    suppressed: bool = False
    suppression_reason: str = ""
    suppression_expires: str = ""
    group_count: int = 1
    grouped_files: list[str] = field(default_factory=list)
    gate_relevant: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectProfile:
    path: str
    project_type: str
    technologies: list[str]
    data_risk: list[str]
    launch_stage: str
    risk_level: str
    signals: list[str] = field(default_factory=list)
    profile_score: int = 0
    profile_evidence: list[str] = field(default_factory=list)
    profile_scores: dict[str, int] = field(default_factory=dict)
    coverage: EvidenceCoverage = field(default_factory=insufficient_coverage)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def severity_sort_key(finding: Finding) -> tuple[int, str]:
    return (SEVERITY_ORDER.get(finding.severity, 99), finding.title)


def finding_penalty(finding: Finding) -> int:
    if finding.severity == "Info" or not finding.gate_relevant:
        return 0
    if finding.source_type in {"docs", "test", "example"}:
        return 3 if finding.severity == "P1" else 1 if finding.severity in {"P2", "P3"} else 0
    if finding.severity == "P1" and finding.confidence in {"suspected", "manual_review"}:
        return 8
    if finding.severity == "P2" and finding.confidence in {"suspected", "manual_review"}:
        return 3
    return SEVERITY_WEIGHTS.get(finding.severity, 0)


def security_score(findings: list[Finding]) -> int:
    confirmed_penalty = 0
    suspected_p1_penalty = 0
    suspected_p2_penalty = 0
    other_penalty = 0
    for finding in findings:
        penalty = finding_penalty(finding)
        if finding.confidence in {"suspected", "manual_review"} and finding.severity == "P1":
            suspected_p1_penalty += penalty
        elif finding.confidence in {"suspected", "manual_review"} and finding.severity == "P2":
            suspected_p2_penalty += penalty
        elif finding.confidence == "confirmed":
            confirmed_penalty += penalty
        else:
            other_penalty += penalty
    penalty = confirmed_penalty + min(suspected_p1_penalty, 40) + min(suspected_p2_penalty, 18) + other_penalty
    return max(0, 100 - penalty)


def normalize_severity(value: str) -> str:
    normalized = value.strip()
    return normalized or "unknown"


def finding_from_dict(data: dict[str, Any]) -> Finding:
    return Finding(
        id=str(data.get("id", "")),
        title=str(data.get("title", "")),
        severity=normalize_severity(str(data.get("severity", "unknown"))),
        category=str(data.get("category", "Config")),
        affected_files=list(data.get("affected_files", [])),
        evidence=str(data.get("evidence", "")),
        why_it_matters_for_beginner=str(data.get("why_it_matters_for_beginner", "")),
        technical_reason=str(data.get("technical_reason", "")),
        recommended_fix=str(data.get("recommended_fix", "")),
        codex_fix_prompt=str(data.get("codex_fix_prompt", "")),
        verification_steps=list(data.get("verification_steps", [])),
        false_positive_notes=str(data.get("false_positive_notes", "")),
        references=list(data.get("references", [])),
        confidence=str(data.get("confidence", "confirmed")),
        source_type=str(data.get("source_type", "runtime")),
        fingerprint=str(data.get("fingerprint", "")),
        suppressed=bool(data.get("suppressed", False)),
        suppression_reason=str(data.get("suppression_reason", "")),
        suppression_expires=str(data.get("suppression_expires", "")),
        group_count=int(data.get("group_count", 1)),
        grouped_files=list(data.get("grouped_files", [])),
        gate_relevant=bool(data.get("gate_relevant", True)),
    )


def gate_relevant(findings: list[Finding]) -> list[Finding]:
    return [
        finding
        for finding in findings
        if finding.gate_relevant and not finding.suppressed and finding.severity != "Info"
    ]
