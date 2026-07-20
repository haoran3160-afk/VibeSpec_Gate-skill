from __future__ import annotations

from .coverage import EvidenceCoverage, insufficient_coverage
from .risk_model import Finding, ProjectProfile, gate_relevant, security_score


SENSITIVE_RISKS = {"payment", "medical", "financial", "enterprise", "minor", "sensitive_identity", "customer_data"}
LOCAL_ONLY_TYPES = {"Desktop/Electron App", "CLI / Local Tool"}


def decide_gate(
    findings: list[Finding],
    profile: ProjectProfile | None = None,
    coverage: EvidenceCoverage | None = None,
) -> dict[str, object]:
    relevant_findings = gate_relevant(findings)
    evidence_coverage = coverage or (profile.coverage if profile else insufficient_coverage())
    counts = {severity: 0 for severity in ("P0", "P1", "P2", "P3", "Info")}
    for finding in relevant_findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1

    needs_expert = bool(profile and set(profile.data_risk) & SENSITIVE_RISKS)
    project_type = profile.project_type if profile else ""
    local_only = project_type in LOCAL_ONLY_TYPES

    confirmed_runtime_p0 = [
        finding
        for finding in relevant_findings
        if finding.severity == "P0" and finding.source_type == "runtime" and finding.confidence == "confirmed"
    ]
    confirmed_runtime_p1 = [
        finding
        for finding in relevant_findings
        if finding.severity == "P1" and finding.source_type == "runtime" and finding.confidence == "confirmed"
    ]
    suspected_runtime_p1 = [
        finding
        for finding in relevant_findings
        if finding.severity == "P1" and finding.source_type == "runtime" and finding.confidence in {"suspected", "manual_review"}
    ]
    ambiguous_runtime_p0 = [
        finding
        for finding in relevant_findings
        if finding.severity == "P0" and finding.source_type == "runtime" and finding.confidence != "confirmed"
    ]

    if confirmed_runtime_p0:
        decision = "BLOCK"
        reason = "Confirmed runtime P0 findings must be fixed before launch."
    elif ambiguous_runtime_p0:
        decision = "REVIEW"
        reason = "Unconfirmed runtime P0 findings require manual review before launch."
    elif confirmed_runtime_p1 and needs_expert and not local_only:
        decision = "BLOCK"
        reason = "Confirmed runtime P1 findings exist in a sensitive externally exposed project."
    elif confirmed_runtime_p1 or suspected_runtime_p1 or needs_expert:
        decision = "REVIEW"
        reason = "Runtime P1 or sensitive-context findings require manual review, but suspected findings do not directly block launch."
    elif not evidence_coverage.allows_pass():
        decision = "REVIEW"
        reason = "Evidence coverage is incomplete, so the project cannot receive a launch pass."
    elif counts["P2"] or counts["P3"]:
        decision = "PASS_WITH_WARNINGS"
        reason = "No blocking runtime issue was found, but lower-priority findings remain."
    else:
        decision = "PASS"
        reason = "The basic VibeSpec launch gate passed."

    return {
        "decision": decision,
        "reason": reason,
        "score": security_score(relevant_findings) if evidence_coverage.allows_pass() else None,
        "counts": counts,
        "total_findings": len(findings),
        "gate_relevant_findings": len(relevant_findings),
        "suppressed_findings": len([f for f in findings if f.suppressed]),
        "requires_expert_review": needs_expert,
        "confirmed_runtime_p1": len(confirmed_runtime_p1),
        "suspected_runtime_p1": len(suspected_runtime_p1),
        "coverage_status": evidence_coverage.coverage_status,
        "coverage": evidence_coverage.to_dict(),
        "missing_evidence": evidence_coverage.missing_evidence(),
    }
