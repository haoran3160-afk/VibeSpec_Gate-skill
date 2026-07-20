from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.run_lite_release_validation import (
    _extract_decision,
    _fixture_sha256,
    _record_section,
    _skill_tree_sha256,
)


EVAL_ROOT = Path("evals")
HISTORICAL_RUN = EVAL_ROOT / "runs/2026-07-20-agent-simulation"
LATEST_RUN = EVAL_ROOT / "runs/2026-07-20-agent-simulation-v2"


def test_trigger_matrix_has_five_positive_and_five_negative_cases():
    cases = _load("trigger_cases.yaml")["cases"]

    assert len(cases) == 10
    assert sum(case["expected_trigger"] is True for case in cases) == 5
    assert sum(case["expected_trigger"] is False for case in cases) == 5
    assert len({case["id"] for case in cases}) == 10


def test_behavior_matrix_covers_eight_required_gates():
    cases = _load("behavior_cases.yaml")["cases"]

    assert len(cases) == 8
    assert len({case["id"] for case in cases}) == 8
    for case in cases:
        assert (Path.cwd() / case["fixture"]).exists()
        assert case["allowed_decisions"]
        assert case["must_not_modify_fixture"] is True
    by_id = {case["id"]: case for case in cases}
    for case_id in (
        "behavior-empty-project",
        "behavior-truncated-scope",
        "behavior-runtime-secret",
        "behavior-missing-ownership",
        "behavior-mcp-missing-allowlist",
    ):
        assert not {"PASS", "PASS_WITH_WARNINGS"} & set(by_id[case_id]["allowed_decisions"])


def test_eval_protocol_requires_fresh_tasks_raw_traces_and_pending_status():
    protocol = (EVAL_ROOT / "protocol.md").read_text(encoding="utf-8")

    for phrase in (
        "new task",
        "clean context",
        "raw user request",
        "Skill Git commit",
        "unedited final output",
        "PENDING",
        "Never substitute a prewritten sample",
        "standard user location",
    ):
        assert phrase.lower() in protocol.lower()


def test_recorded_run_preserves_outputs_but_keeps_unobservable_results_pending():
    summary = json.loads((EVAL_ROOT / "runs/2026-07-20/summary.json").read_text(encoding="utf-8"))

    assert len(summary["trigger_cases"]) == 10
    assert len(summary["behavior_cases"]) == 8
    assert summary["activation_observability"] == "unavailable"
    assert all(case["status"] == "PENDING" for case in summary["trigger_cases"])
    assert all(case["activated"] is None for case in summary["trigger_cases"])
    assert all(case["status"] == "PENDING" for case in summary["behavior_cases"])
    assert all(case["fixture_sha256_before"] == case["fixture_sha256_after"] for case in summary["behavior_cases"])
    assert all(case["files_written"] is None for case in summary["behavior_cases"])
    assert all(case["write_observability"] == "unavailable" for case in summary["behavior_cases"])
    assert len(summary["failed_attempts"]) == 4
    for group in ("trigger_cases", "behavior_cases", "failed_attempts"):
        for case in summary[group]:
            assert (EVAL_ROOT / "runs/2026-07-20" / case["output"]).is_file()


def test_recorded_agent_simulation_keeps_failed_and_unobservable_gates_closed():
    summary = json.loads((HISTORICAL_RUN / "summary.json").read_text(encoding="utf-8"))
    cases = _load("behavior_cases.yaml")["cases"]
    records = {record["id"]: record for record in summary["behavior_cases"]}

    assert summary["behavior_semantic_status"] == "FAIL"
    assert summary["write_safety_status"] == "PENDING"
    assert summary["behavior_status"] == "FAIL"
    assert summary["trigger_status"] == "PENDING"
    assert summary["overall_status"] == "FAIL"
    assert summary["automatic_trigger_observability"] == "unavailable"
    assert len(summary["trigger_cases"]) == 10
    assert all(record["status"] == "PENDING" for record in summary["trigger_cases"])
    assert set(records) == {case["id"] for case in cases}

    for case in cases:
        record = records[case["id"]]
        trace = (HISTORICAL_RUN / record["output"]).read_text(encoding="utf-8")
        assert _record_section(trace, "Raw Request", "Unedited Final Output") == case["prompt"]
        rendered = _record_section(trace, "Unedited Final Output")
        decision = _extract_decision(rendered)
        assert decision == record["decision"]
        assert decision in case["allowed_decisions"]
        assert decision not in case["forbidden_decisions"]
        required_concepts_present = all(term.lower() in rendered.lower() for term in case["required_terms"])
        assert record["semantic_status"] == ("PASS" if required_concepts_present else "FAIL")
        assert record["status"] == ("PENDING" if required_concepts_present else "FAIL")

        evidence = json.loads((HISTORICAL_RUN / record["integrity_evidence"]).read_text(encoding="utf-8"))
        current_hash = _fixture_sha256(Path(case["fixture"]))
        assert evidence["event_type"] == "isolated_content_integrity_comparison"
        assert evidence["scope"] == "isolated_case_root"
        assert evidence["fixture_sha256_before"] == current_hash
        assert evidence["fixture_sha256_after"] == current_hash
        assert evidence["net_created_paths"] == []
        assert evidence["net_modified_paths"] == []
        assert evidence["net_deleted_paths"] == []
        assert "cannot detect transient" in evidence["observation_limit"]
        assert record["fixture_sha256_before"] == current_hash
        assert record["fixture_sha256_after"] == current_hash
        assert record["files_written"] is None
        assert record["write_observability"] == "unavailable"

    assert len(summary["skill_tree_sha256"]) == 64


def test_latest_agent_simulation_passes_semantics_but_keeps_untrusted_gates_pending():
    summary = json.loads((LATEST_RUN / "summary.json").read_text(encoding="utf-8"))
    cases = _load("behavior_cases.yaml")["cases"]
    records = {record["id"]: record for record in summary["behavior_cases"]}

    assert summary["behavior_semantic_status"] == "PASS"
    assert summary["write_safety_status"] == "PENDING"
    assert summary["behavior_status"] == "PENDING"
    assert summary["trigger_status"] == "PENDING"
    assert summary["overall_status"] == "PENDING"
    assert summary["provenance_status"].endswith("not externally authenticated")
    assert len(summary["trigger_cases"]) == 10
    assert all(record["status"] == "PENDING" for record in summary["trigger_cases"])
    assert set(records) == {case["id"] for case in cases}

    for case in cases:
        record = records[case["id"]]
        trace_path = LATEST_RUN / record["output"]
        trace = trace_path.read_text(encoding="utf-8")
        assert hashlib.sha256(trace_path.read_bytes()).hexdigest() == record["output_sha256"]
        assert _record_section(trace, "Raw Request", "Unedited Final Output") == case["prompt"]
        rendered = _record_section(trace, "Unedited Final Output")
        decision = _extract_decision(rendered)
        assert decision == record["decision"]
        assert decision in case["allowed_decisions"]
        assert decision not in case["forbidden_decisions"]
        assert all(term.lower() in rendered.lower() for term in case["required_terms"])
        for required_heading in ("Limitations", "Human Confirmation Required"):
            assert required_heading.lower() in rendered.lower()
        assert record["semantic_status"] == "PASS"
        assert record["status"] == "PENDING"

        evidence_path = LATEST_RUN / record["integrity_evidence"]
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        assert hashlib.sha256(evidence_path.read_bytes()).hexdigest() == record["integrity_evidence_sha256"]
        current_hash = _fixture_sha256(Path(case["fixture"]))
        assert evidence["source_fixture"] == case["fixture"]
        assert evidence["fixture_sha256_before"] == current_hash
        assert evidence["fixture_sha256_after"] == current_hash
        assert evidence["file_sha256_before"] == evidence["file_sha256_after"]
        assert evidence["net_created_paths"] == []
        assert evidence["net_modified_paths"] == []
        assert evidence["net_deleted_paths"] == []
        assert record["files_written"] is None
        assert record["write_observability"] == "unavailable"
        assert "write_evidence" not in record

    assert summary["skill_tree_sha256"] == _skill_tree_sha256(Path("skills/vibespec-gate"))
    failed_attempt = summary["failed_attempts"][0]
    assert failed_attempt["status"] == "FAIL"
    assert (LATEST_RUN / failed_attempt["output"]).is_file()


def _load(name: str) -> dict[str, object]:
    return json.loads((EVAL_ROOT / name).read_text(encoding="utf-8"))
