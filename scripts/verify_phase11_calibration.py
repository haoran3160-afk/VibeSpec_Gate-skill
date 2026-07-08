from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PHASE11_ROOT = ROOT / "test output" / "phase11_real_host_agent_calibration"
ALLOWED_RUBRIC_ACTIONS = {"keep", "adjust", "add_check", "defer"}
REQUIRED_SAMPLE_FILES = {
    "llm_review_packet.json",
    "expected_quality.json",
    "sample_metadata.json",
    "outputs/nontechnical_user_summary.md",
    "outputs/launch_risk_report.md",
    "outputs/security_review_findings.json",
    "outputs/agent_fix_plan.md",
    "outputs/retest_checklist.md",
}
REQUIRED_REPORTS = {
    "reports/host_agent_sample_matrix.json",
    "reports/host_agent_sample_matrix.md",
    "reports/scorer_disagreement_log.md",
    "reports/phase11_calibration_summary.md",
    "human_calibration_ledger.json",
    "human_calibration_ledger.md",
    "scorer_disagreement_log.md",
    "delivery_boundary_review.md",
    "phase11_calibration_summary.md",
}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) > 1:
        print("usage: py -3 scripts\\verify_phase11_calibration.py [phase11_root]", file=sys.stderr)
        return 2
    phase_root = Path(args[0]) if args else DEFAULT_PHASE11_ROOT
    status = verify_phase11_calibration(phase_root)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


def verify_phase11_calibration(phase_root: Path) -> dict[str, object]:
    matrix = _load_json(phase_root / "reports" / "host_agent_sample_matrix.json")
    ledger = _load_json(phase_root / "human_calibration_ledger.json")
    gates = [
        _required_artifacts_gate(phase_root),
        _sample_structure_gate(matrix),
        _non_empty_sample_gate(matrix),
        _three_agent_shared_packet_gate(matrix),
        _human_calibration_gate(ledger),
        _disagreement_disposition_gate(ledger),
        _rule_change_evidence_gate(ledger),
        _report_distinction_gate(phase_root),
        _delivery_boundary_gate(phase_root),
    ]
    missing_actions = [
        gate["action"]
        for gate in gates
        if not gate["passed"] and gate.get("action")
    ]
    return {
        "schema_version": "1.0",
        "phase": "phase11_real_host_agent_calibration",
        "phase_root": str(phase_root),
        "passed": all(gate["passed"] for gate in gates),
        "gates": gates,
        "missing_actions": missing_actions,
    }


def _required_artifacts_gate(phase_root: Path) -> dict[str, object]:
    missing = sorted(path for path in REQUIRED_REPORTS if not (phase_root / path).exists())
    return _gate(
        "required_artifacts",
        not missing,
        "all expected Phase 11 artifact files exist" if not missing else f"missing {missing}",
        "create the missing Phase 11 artifact files" if missing else "",
    )


def _sample_structure_gate(matrix: dict[str, object]) -> dict[str, object]:
    missing: list[str] = []
    for case in matrix.get("cases", []):
        sample_path = _resolve_path(case.get("sample_path", ""))
        for relative in REQUIRED_SAMPLE_FILES:
            if not (sample_path / relative).exists():
                missing.append(f"{sample_path}/{relative}")
    return _gate(
        "sample_structure",
        not missing,
        "all matrix samples have required files" if not missing else f"missing {missing}",
        "populate every host-agent sample with the required contract files" if missing else "",
    )


def _non_empty_sample_gate(matrix: dict[str, object]) -> dict[str, object]:
    sample_count = int(matrix.get("sample_count", 0) or 0)
    return _gate(
        "real_host_agent_sample_non_empty",
        sample_count >= 1,
        f"sample_count={sample_count}",
        "add at least one real host-agent sample" if sample_count < 1 else "",
    )


def _three_agent_shared_packet_gate(matrix: dict[str, object]) -> dict[str, object]:
    agents_by_case: dict[str, set[str]] = defaultdict(set)
    for case in matrix.get("cases", []):
        case_id = str(case.get("case_id", ""))
        agent = str(case.get("agent", ""))
        if case_id and agent:
            agents_by_case[case_id].add(agent)
    complete_cases = sorted(case_id for case_id, agents in agents_by_case.items() if len(agents) >= 3)
    detail = (
        f"shared packets with >=3 agents: {complete_cases}"
        if complete_cases
        else f"agent coverage by case: {_coverage_detail(agents_by_case)}"
    )
    return _gate(
        "three_agent_shared_packet",
        bool(complete_cases),
        detail,
        "add Claude and Cursor samples for the same shared packet" if not complete_cases else "",
    )


def _human_calibration_gate(ledger: dict[str, object]) -> dict[str, object]:
    records = [_record for _record in ledger.get("records", []) if is_completed_human_record(_record)]
    counts = Counter(record.get("sample_type") for record in records)
    passed = len(records) >= 5 and counts["golden_fixture"] >= 2 and counts["bad_fixture"] >= 2 and counts["host_agent_sample"] >= 1
    detail = (
        f"completed={len(records)}, golden={counts['golden_fixture']}, "
        f"bad={counts['bad_fixture']}, host_agent={counts['host_agent_sample']}"
    )
    return _gate(
        "human_calibration_minimum_set",
        passed,
        detail,
        "record at least two golden, two bad, and one host-agent human reviews" if not passed else "",
    )


def _disagreement_disposition_gate(ledger: dict[str, object]) -> dict[str, object]:
    records = ledger.get("records", [])
    unresolved = [
        record.get("review_id", record.get("case_id", "<unknown>"))
        for record in records
        if record.get("agreement") is False and record.get("rubric_action") not in ALLOWED_RUBRIC_ACTIONS
    ]
    return _gate(
        "disagreement_disposition",
        not unresolved,
        "all disagreements have a rubric disposition" if not unresolved else f"unresolved {unresolved}",
        "add keep, adjust, add_check, or defer disposition to every disagreement" if unresolved else "",
    )


def _rule_change_evidence_gate(ledger: dict[str, object]) -> dict[str, object]:
    records = ledger.get("records", [])
    unsupported = [
        record.get("review_id", record.get("case_id", "<unknown>"))
        for record in records
        if record.get("rubric_action") in {"adjust", "add_check"}
        and not record.get("proposed_rule_change")
    ]
    return _gate(
        "rule_change_evidence",
        not unsupported,
        "no unsupported rule-change requests" if not unsupported else f"unsupported {unsupported}",
        "attach proposed_rule_change evidence before changing scorer rules" if unsupported else "",
    )


def _report_distinction_gate(phase_root: Path) -> dict[str, object]:
    summary = phase_root / "phase11_calibration_summary.md"
    text = summary.read_text(encoding="utf-8").lower() if summary.exists() else ""
    passed = "fixture" in text and "host-agent" in text and "human" in text
    return _gate(
        "report_distinguishes_evidence",
        passed,
        "summary distinguishes fixture, host-agent, and human evidence" if passed else "summary lacks evidence-type distinction",
        "update phase11_calibration_summary.md to distinguish fixture, host-agent, and human evidence" if not passed else "",
    )


def _delivery_boundary_gate(phase_root: Path) -> dict[str, object]:
    review = phase_root / "delivery_boundary_review.md"
    text = review.read_text(encoding="utf-8").lower() if review.exists() else ""
    required = ["product code", "regression assets", "user-facing docs", "historical"]
    missing = [item for item in required if item not in text]
    return _gate(
        "delivery_boundary_review",
        not missing,
        "delivery boundary review covers all required groups" if not missing else f"missing sections {missing}",
        "complete delivery_boundary_review.md classification" if missing else "",
    )


def is_completed_human_record(record: object) -> bool:
    if not isinstance(record, dict):
        return False
    return (
        record.get("sample_type") in {"golden_fixture", "bad_fixture", "host_agent_sample"}
        and record.get("human_quality_decision") in {"pass", "fail"}
        and record.get("human_launch_decision") in {"PASS", "PASS_WITH_WARNINGS", "REVIEW", "BLOCK"}
        and isinstance(record.get("agreement"), bool)
        and record.get("rubric_action") in ALLOWED_RUBRIC_ACTIONS
    )


def _load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_path(value: object) -> Path:
    path = Path(str(value))
    if path.is_absolute():
        return path
    return ROOT / path


def _coverage_detail(agents_by_case: dict[str, set[str]]) -> dict[str, list[str]]:
    return {case_id: sorted(agents) for case_id, agents in sorted(agents_by_case.items())}


def _gate(gate_id: str, passed: bool, detail: str, action: str) -> dict[str, object]:
    return {
        "id": gate_id,
        "passed": passed,
        "detail": detail,
        "action": action,
    }


if __name__ == "__main__":
    raise SystemExit(main())
