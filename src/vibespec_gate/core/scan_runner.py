from __future__ import annotations

from vibespec_gate.adapters import DEFAULT_ADAPTERS
from vibespec_gate.scanners import DEFAULT_SCANNERS

from .finding_processor import process_findings
from .path_safety import require_disjoint_paths
from .project_intake import detect_profile
from .report_builder import write_reports
from .risk_model import Finding


def run_scan(
    project_path: str,
    output_dir: str,
    mode: str | None = None,
    include_adapters: bool = True,
    suppression_file: str | None = None,
) -> dict[str, object]:
    root, output = require_disjoint_paths(
        project_path,
        output_dir,
        first_label="project",
        second_label="output",
    )
    resolved_suppression: str | None = None
    if suppression_file:
        suppression, output = require_disjoint_paths(
            suppression_file,
            output,
            first_label="suppression input",
            second_label="output",
        )
        resolved_suppression = str(suppression)
    profile = detect_profile(str(root), mode)
    findings: list[Finding] = []
    for scanner in DEFAULT_SCANNERS:
        findings.extend(scanner.scan(root, profile))
    if include_adapters:
        for adapter in DEFAULT_ADAPTERS:
            findings.extend(adapter.scan(root, profile))
    findings = process_findings(root, findings, suppression_file=resolved_suppression)
    return write_reports(output, profile, findings)
