from __future__ import annotations

import json
from pathlib import Path

from .gate_decision import decide_gate
from .path_safety import require_disjoint_paths
from .risk_model import Finding, ProjectProfile, finding_from_dict, gate_relevant, security_score, severity_sort_key


DISCLAIMER = (
    "This report is a basic pre-launch security gate and remediation aid. "
    "It is not a professional penetration test, security audit, legal opinion, or compliance certification. "
    "Only scan projects you own or are authorized to review."
)
TOP_ACTIONABLE_LIMIT = 20


def write_reports(output_dir: Path, profile: ProjectProfile, findings: list[Finding]) -> dict[str, object]:
    _, output_dir = require_disjoint_paths(
        profile.path,
        output_dir,
        first_label="project",
        second_label="output",
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    sorted_findings = sorted(findings, key=severity_sort_key)
    active = [f for f in sorted_findings if not f.suppressed]
    suppressed = [f for f in sorted_findings if f.suppressed]
    gate = decide_gate(sorted_findings, profile, profile.coverage)
    (output_dir / "findings.json").write_text(
        json.dumps([f.to_dict() for f in sorted_findings], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    gate_summary = {"profile": profile.to_dict(), **gate}
    (output_dir / "gate_summary.json").write_text(json.dumps(gate_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "vibespec_gate_report_user.md").write_text(_user_report(profile, active, suppressed, gate), encoding="utf-8")
    (output_dir / "vibespec_gate_report_developer.md").write_text(
        _developer_report(profile, active, suppressed, gate), encoding="utf-8"
    )
    (output_dir / "codex_fix_tasks.md").write_text(_fix_tasks(active), encoding="utf-8")
    if not (output_dir / "loop_review.md").exists():
        (output_dir / "loop_review.md").write_text(_initial_loop_review(active, suppressed, gate), encoding="utf-8")
    return gate_summary


def load_findings(path: Path) -> list[Finding]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [finding_from_dict(item) for item in data]


def _user_report(profile: ProjectProfile, findings: list[Finding], suppressed: list[Finding], gate: dict[str, object]) -> str:
    gate_findings = gate_relevant(findings)
    top = gate_findings[:5]
    lines = [
        "# VibeSpec Gate Beginner Security Report",
        "",
        f"- Security score: {gate['score']}/100" if gate["score"] is not None else "- Security score: N/A (evidence coverage incomplete)",
        f"- Launch gate: {gate['decision']}",
        f"- Reason: {gate['reason']}",
        f"- Project type: {profile.project_type}",
        f"- Risk level: {profile.risk_level}",
        f"- Technologies: {', '.join(profile.technologies)}",
        f"- Gate-relevant findings: {gate['gate_relevant_findings']} of {gate['total_findings']}",
        "",
        "## Project Profile Evidence",
        *_bullet_lines(profile.profile_evidence or profile.signals or ["No profile evidence recorded."]),
        "",
        "## Evidence Coverage",
        *_coverage_lines(profile),
        "",
        "## Top Issues To Fix First",
    ]
    if not top:
        lines.append("No runtime P0/P1/P2 findings are currently blocking the basic gate.")
    for finding in top:
        lines.extend(
            [
                "",
                f"### {finding.severity} - {finding.title}",
                f"- Source type: {finding.source_type}",
                f"- Location: {', '.join(finding.affected_files) or 'project'}",
                f"- Plain-language impact: {finding.why_it_matters_for_beginner}",
                f"- What can go wrong: {finding.technical_reason}",
                f"- Fix first: {finding.recommended_fix}",
                f"- Retest: {'; '.join(finding.verification_steps)}",
            ]
        )
    lines.extend(_suppressed_section(suppressed))
    lines.extend(["", "## Manual Review", "Use expert review for payment, enterprise/customer data, medical, financial, minor, or sensitive identity data.", "", "## Disclaimer", DISCLAIMER, ""])
    return "\n".join(lines)


def _developer_report(profile: ProjectProfile, findings: list[Finding], suppressed: list[Finding], gate: dict[str, object]) -> str:
    shown = findings[:TOP_ACTIONABLE_LIMIT]
    hidden_count = max(0, len(findings) - len(shown))
    lines = [
        "# VibeSpec Gate Developer Security Report",
        "",
        f"Gate: `{gate['decision']}`",
        f"Gate-relevant findings: {gate['gate_relevant_findings']} / total active findings: {len(findings)}",
        "",
        "## Project Profile",
        "```json",
        json.dumps(profile.to_dict(), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Evidence Coverage",
        *_coverage_lines(profile),
        "",
        f"## Top {TOP_ACTIONABLE_LIMIT} Active Findings",
    ]
    if not shown:
        lines.append("No active findings.")
    for finding in shown:
        lines.extend(_finding_block(finding))
    if hidden_count:
        lines.extend(["", "## Grouped / Hidden Summary", f"- {hidden_count} additional active findings were omitted from the default report view. See `findings.json` for full details."])
    lines.extend(_suppressed_section(suppressed))
    lines.extend(["", "## Disclaimer", DISCLAIMER, ""])
    return "\n".join(lines)


def _finding_block(finding: Finding) -> list[str]:
    grouped = f" grouped_count={finding.group_count}" if finding.group_count > 1 else ""
    lines = [
        "",
        f"### {finding.id} {finding.severity} {finding.title}{grouped}",
        f"- Category: {finding.category}",
        f"- Source type: {finding.source_type}",
        f"- Confidence: {finding.confidence}",
        f"- Fingerprint: `{finding.fingerprint}`",
        f"- Files: {', '.join(finding.affected_files)}",
        f"- Evidence: {finding.evidence}",
        f"- Technical reason: {finding.technical_reason}",
        f"- Recommended fix: {finding.recommended_fix}",
        f"- Verification: {'; '.join(finding.verification_steps)}",
        f"- False-positive notes: {finding.false_positive_notes}",
        f"- References: {', '.join(finding.references)}",
    ]
    if finding.grouped_files:
        lines.append(f"- Grouped files: {', '.join(finding.grouped_files[:20])}")
    return lines


def _fix_tasks(findings: list[Finding]) -> str:
    actionable = [
        f
        for f in findings
        if f.severity in {"P0", "P1", "P2"}
        and f.source_type not in {"generated", "vendor", "cache"}
        and not f.suppressed
        and f.codex_fix_prompt
    ][:TOP_ACTIONABLE_LIMIT]
    if not actionable:
        return "# Codex Fix Tasks\n\nNo actionable P0/P1/P2 fix tasks were generated.\n"
    return "# Codex Fix Tasks\n\n" + "\n\n".join(f.codex_fix_prompt for f in actionable)


def _initial_loop_review(findings: list[Finding], suppressed: list[Finding], gate: dict[str, object]) -> str:
    return f"""# VibeSpec Gate Loop Review

## Scan Loop
- Current active findings: {len(findings)}
- Current suppressed findings: {len(suppressed)}
- Current gate decision: {gate['decision']}
- Note: run `vibespec-gate loop <project> --previous <findings.json>` after fixes to compare changes.
"""


def _suppressed_section(suppressed: list[Finding]) -> list[str]:
    lines = ["", "## Suppressed Findings"]
    if not suppressed:
        lines.append("No suppressed findings.")
        return lines
    for finding in suppressed:
        warning = " P0 SUPPRESSED - REVIEW CAREFULLY." if finding.severity == "P0" else ""
        lines.extend(
            [
                f"- {finding.severity} {finding.title}{warning}",
                f"  - Fingerprint: `{finding.fingerprint}`",
                f"  - Reason: {finding.suppression_reason}",
                f"  - Expires: {finding.suppression_expires or 'not set'}",
            ]
        )
    return lines


def _bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]


def _coverage_lines(profile: ProjectProfile) -> list[str]:
    coverage = profile.coverage
    lines = [
        f"- Coverage status: {coverage.coverage_status}",
        f"- Files: {coverage.files_inspected} inspected / {coverage.files_discovered} discovered / {coverage.files_skipped} skipped",
    ]
    for item in coverage.surfaces:
        detail = ", ".join(item.source_refs) if item.source_refs else item.reason
        lines.append(f"- {item.surface}: {item.status} - {detail}")
    return lines
