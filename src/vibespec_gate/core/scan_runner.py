from __future__ import annotations

from pathlib import Path

from vibespec_gate.adapters import DEFAULT_ADAPTERS
from vibespec_gate.scanners import DEFAULT_SCANNERS

from .finding_processor import process_findings
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
    root = Path(project_path).resolve()
    profile = detect_profile(str(root), mode)
    findings: list[Finding] = []
    for scanner in DEFAULT_SCANNERS:
        findings.extend(scanner.scan(root, profile))
    if include_adapters:
        for adapter in DEFAULT_ADAPTERS:
            findings.extend(adapter.scan(root, profile))
    findings = process_findings(root, findings, suppression_file=suppression_file)
    return write_reports(Path(output_dir).resolve(), profile, findings)
