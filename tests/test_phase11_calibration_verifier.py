from __future__ import annotations

import json
from pathlib import Path

from scripts.verify_phase11_calibration import verify_phase11_calibration


def test_phase11_verifier_reports_incomplete_calibration(tmp_path):
    phase_root = _write_phase11_root(tmp_path, agents=["codex"], records=[])

    status = verify_phase11_calibration(phase_root)

    assert status["passed"] is False
    gates = {gate["id"]: gate for gate in status["gates"]}
    assert gates["real_host_agent_sample_non_empty"]["passed"] is True
    assert gates["three_agent_shared_packet"]["passed"] is False
    assert gates["human_calibration_minimum_set"]["passed"] is False
    assert "add Claude and Cursor samples" in gates["three_agent_shared_packet"]["action"]


def test_phase11_verifier_accepts_complete_calibration_evidence(tmp_path):
    records = [
        _human_record("golden-1", "secret_runtime_block", "golden_fixture", "pass", "BLOCK", True, "keep"),
        _human_record("golden-2", "missing_auth_review", "golden_fixture", "pass", "REVIEW", True, "keep"),
        _human_record("bad-1", "secret_runtime_overoptimistic", "bad_fixture", "fail", "BLOCK", True, "keep"),
        _human_record("bad-2", "missing_auth_ignores_uncertainty", "bad_fixture", "fail", "REVIEW", True, "keep"),
        _human_record("host-1", "secret_runtime_block", "host_agent_sample", "fail", "BLOCK", False, "defer"),
    ]
    phase_root = _write_phase11_root(tmp_path, agents=["codex", "claude", "cursor"], records=records)

    status = verify_phase11_calibration(phase_root)

    assert status["passed"] is True
    assert all(gate["passed"] for gate in status["gates"])


def _write_phase11_root(tmp_path: Path, agents: list[str], records: list[dict[str, object]]) -> Path:
    phase_root = tmp_path / "phase11"
    reports = phase_root / "reports"
    reports.mkdir(parents=True)
    cases = []
    for agent in agents:
        sample = phase_root / "host_agent_samples" / agent / "secret_runtime_block"
        _write_sample(sample, agent)
        cases.append(
            {
                "agent": agent,
                "case_id": "secret_runtime_block",
                "sample_path": str(sample),
                "expected_launch_decision": "BLOCK",
                "actual_launch_decision": "BLOCK",
                "soft_score": 100,
                "passed": True,
                "hard_failures": [],
                "failed_checks": [],
            }
        )
    matrix = {
        "schema_version": "1.0",
        "sample_count": len(cases),
        "agents": agents,
        "cases": cases,
    }
    (reports / "host_agent_sample_matrix.json").write_text(json.dumps(matrix, indent=2), encoding="utf-8")
    (reports / "host_agent_sample_matrix.md").write_text("# Host-Agent Sample Matrix\n", encoding="utf-8")
    (reports / "scorer_disagreement_log.md").write_text("# Scorer Disagreement Log\n", encoding="utf-8")
    (reports / "phase11_calibration_summary.md").write_text("# Summary\n", encoding="utf-8")
    ledger = {"schema_version": "1.0", "records": records}
    (phase_root / "human_calibration_ledger.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    (phase_root / "human_calibration_ledger.md").write_text("# Human Calibration Ledger\n", encoding="utf-8")
    (phase_root / "scorer_disagreement_log.md").write_text("# Scorer Disagreement Log\n", encoding="utf-8")
    (phase_root / "delivery_boundary_review.md").write_text(
        "# Delivery Boundary\n\n"
        "## Product Code\n\n## Regression Assets\n\n## User-Facing Docs\n\n## Historical And Generated Outputs\n",
        encoding="utf-8",
    )
    (phase_root / "phase11_calibration_summary.md").write_text(
        "fixture regression evidence, host-agent calibration evidence, and human calibration evidence\n",
        encoding="utf-8",
    )
    return phase_root


def _write_sample(sample: Path, agent: str) -> None:
    (sample / "outputs").mkdir(parents=True)
    for relative in (
        "llm_review_packet.json",
        "expected_quality.json",
        "sample_metadata.json",
        "outputs/nontechnical_user_summary.md",
        "outputs/launch_risk_report.md",
        "outputs/agent_fix_plan.md",
        "outputs/retest_checklist.md",
    ):
        (sample / relative).write_text("{}", encoding="utf-8")
    (sample / "outputs" / "security_review_findings.json").write_text("[]", encoding="utf-8")
    (sample / "sample_metadata.json").write_text(
        json.dumps({"schema_version": "1.0", "agent": agent}, indent=2),
        encoding="utf-8",
    )


def _human_record(
    review_id: str,
    case_id: str,
    sample_type: str,
    quality: str,
    launch_decision: str,
    agreement: bool,
    rubric_action: str,
) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "review_id": review_id,
        "case_id": case_id,
        "sample_type": sample_type,
        "scorer_passed": quality == "pass",
        "scorer_soft_score": 100,
        "scorer_hard_failures": [],
        "human_launch_decision": launch_decision,
        "human_quality_decision": quality,
        "agreement": agreement,
        "disagreement_type": None if agreement else "human_stricter",
        "human_notes": "Test reviewer decision.",
        "rubric_action": rubric_action,
        "proposed_rule_change": None,
    }
