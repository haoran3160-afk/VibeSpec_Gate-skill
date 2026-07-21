from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from scripts.run_lite_release_validation import (
    SKILL_EVAL_SUMMARY,
    _extract_decision,
    _fixture_sha256,
    _record_section,
    _skill_eval_passed,
    _skill_tree_sha256,
)


EVAL_ROOT = Path("evals")
HISTORICAL_RUN = EVAL_ROOT / "runs/2026-07-20-agent-simulation"
SEMANTIC_RUN = EVAL_ROOT / "runs/2026-07-20-agent-simulation-v2"
FAILED_ACTIVATION_RUN = EVAL_ROOT / "runs/2026-07-20-agent-simulation-v3"
CURRENT_RUN = EVAL_ROOT / "runs/2026-07-21-codex-cli-v6"


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
    summary = json.loads((SEMANTIC_RUN / "summary.json").read_text(encoding="utf-8"))
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
        trace_path = SEMANTIC_RUN / record["output"]
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

        evidence_path = SEMANTIC_RUN / record["integrity_evidence"]
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

    assert summary["skill_tree_sha256"] != _skill_tree_sha256(Path("skills/vibespec-gate"))
    failed_attempt = summary["failed_attempts"][0]
    assert failed_attempt["status"] == "FAIL"
    assert (SEMANTIC_RUN / failed_attempt["output"]).is_file()


def test_failed_activation_candidate_keeps_release_gate_closed():
    summary_path = FAILED_ACTIVATION_RUN / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["skill_tree_sha256"] == _skill_tree_sha256(Path("skills/vibespec-gate"))
    assert summary["skill_activation_status"] == "FAIL"
    assert summary["behavior_status"] == "FAIL"
    assert summary["trigger_status"] == "PENDING"
    assert summary["write_safety_status"] == "PENDING"
    assert summary["overall_status"] == "FAIL"
    assert len(summary["failed_attempts"]) == 3
    for attempt in summary["failed_attempts"]:
        output = FAILED_ACTIVATION_RUN / attempt["output"]
        assert output.is_file()
        assert hashlib.sha256(output.read_bytes()).hexdigest() == attempt["output_sha256"]
        assert attempt["fixture_sha256_before"] == attempt["fixture_sha256_after"]
        assert attempt["files_written"] is None
        assert attempt["write_observability"] == "unavailable"


def test_current_codex_host_run_requires_external_digest_and_passes_full_reconstruction(monkeypatch):
    summary_path = CURRENT_RUN / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(summary_path.read_bytes()).hexdigest()
    monkeypatch.delenv("VIBESPEC_TRUSTED_EVAL_SHA256", raising=False)

    assert SKILL_EVAL_SUMMARY == summary_path.resolve()
    assert summary["skill_tree_sha256"] == _skill_tree_sha256(Path("skills/vibespec-gate"))
    assert summary["skill_activation_status"] == "PASS"
    assert summary["behavior_semantic_status"] == "PASS"
    assert summary["write_safety_status"] == "PASS"
    assert summary["user_skill_isolation_status"] == "PASS"
    assert summary["behavior_status"] == "PASS"
    assert summary["trigger_status"] == "PASS"
    assert summary["overall_status"] == "PASS"
    assert len(summary["trigger_cases"]) == 10
    assert len(summary["behavior_cases"]) == 8

    assert not _skill_eval_passed(summary_path)
    assert not _skill_eval_passed(summary_path, trusted_summary_sha256="0" * 64)
    assert _skill_eval_passed(summary_path, trusted_summary_sha256=digest)


def test_current_eval_rejects_schema_downgrade_with_matching_digest(tmp_path):
    summary_path = _copy_current_run(tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["schema_version"] = "1.3"
    _write_json(summary_path, summary)

    assert not _trusted_eval_passes(summary_path)


def test_current_eval_binds_final_output_to_host_trace(tmp_path):
    summary_path = _copy_current_run(tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    record = summary["trigger_cases"][0]
    output_path = summary_path.parent / record["output"]
    output_path.write_text(
        output_path.read_text(encoding="utf-8") + "\ntampered final output\n",
        encoding="utf-8",
        newline="\n",
    )
    record["output_sha256"] = hashlib.sha256(output_path.read_bytes()).hexdigest()
    _write_json(summary_path, summary)

    assert not _trusted_eval_passes(summary_path)


def test_current_eval_binds_task_identity_to_host_trace(tmp_path):
    summary_path = _copy_current_run(tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    record = summary["trigger_cases"][0]
    record["task_id"] = "substituted-task-id"
    activation_path = summary_path.parent / record["activation_evidence"]
    activation = json.loads(activation_path.read_text(encoding="utf-8"))
    activation["task_id"] = record["task_id"]
    _write_json(activation_path, activation)
    record["activation_evidence_sha256"] = hashlib.sha256(
        activation_path.read_bytes()
    ).hexdigest()
    _write_json(summary_path, summary)

    assert not _trusted_eval_passes(summary_path)


def test_current_eval_requires_successful_skill_resource_reads(tmp_path):
    summary_path = _copy_current_run(tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    record = next(
        item for item in summary["trigger_cases"] if item["expected_trigger"] is True
    )
    trace_path = summary_path.parent / record["host_trace"]
    events = [
        json.loads(line)
        for line in trace_path.read_text(encoding="utf-8").splitlines()
    ]
    changed = 0
    for event in events:
        event_item = event.get("item", {})
        command = str(event_item.get("command", ""))
        if (
            event.get("type") == "item.completed"
            and event_item.get("type") == "command_execution"
            and any(
                resource in command.lower()
                for resource in ("review-protocol.md", "evidence-coverage.md")
            )
        ):
            event_item["status"] = "declined"
            event_item["exit_code"] = -1
            changed += 1
    assert changed == 2
    _rebind_trigger_host_trace(summary_path.parent, record, events)
    _write_json(summary_path, summary)

    assert not _trusted_eval_passes(summary_path)


def test_current_eval_rejects_incomplete_turn_write_attempt_or_other_user_skill(tmp_path):
    for mutation in ("remove_completion", "add_write_attempt", "add_other_skill_read"):
        run_root = tmp_path / mutation
        shutil.copytree(CURRENT_RUN, run_root)
        summary_path = run_root / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        record = summary["trigger_cases"][0]
        trace_path = run_root / record["host_trace"]
        events = [
            json.loads(line)
            for line in trace_path.read_text(encoding="utf-8").splitlines()
        ]
        if mutation == "remove_completion":
            assert events[-1]["type"] == "turn.completed"
            events.pop()
        elif mutation == "add_write_attempt":
            events.insert(
                -1,
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": "py -3 -c \"open('changed.txt', 'w').write('x')\"",
                        "status": "declined",
                        "exit_code": -1,
                    },
                },
            )
        else:
            events.insert(
                -1,
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": (
                            "Get-Content 'C:\\Users\\lenovo\\.agents\\skills"
                            "\\other-skill\\SKILL.md'"
                        ),
                        "aggregated_output": "other instructions\n",
                        "status": "completed",
                        "exit_code": 0,
                    },
                },
            )
        _rebind_trigger_host_trace(run_root, record, events)
        _write_json(summary_path, summary)

        assert not _trusted_eval_passes(summary_path)


def _load(name: str) -> dict[str, object]:
    return json.loads((EVAL_ROOT / name).read_text(encoding="utf-8"))


def _copy_current_run(tmp_path: Path) -> Path:
    run_root = tmp_path / "current-run"
    shutil.copytree(CURRENT_RUN, run_root)
    return run_root / "summary.json"


def _trusted_eval_passes(summary_path: Path) -> bool:
    digest = hashlib.sha256(summary_path.read_bytes()).hexdigest()
    return _skill_eval_passed(summary_path, trusted_summary_sha256=digest)


def _rebind_trigger_host_trace(
    run_root: Path,
    record: dict[str, object],
    events: list[dict[str, object]],
) -> None:
    trace_path = run_root / str(record["host_trace"])
    trace_path.write_text(
        "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
        encoding="utf-8",
        newline="\n",
    )
    trace_digest = hashlib.sha256(trace_path.read_bytes()).hexdigest()
    record["host_trace_sha256"] = trace_digest
    activation_path = run_root / str(record["activation_evidence"])
    activation = json.loads(activation_path.read_text(encoding="utf-8"))
    activation["host_trace_sha256"] = trace_digest
    _write_json(activation_path, activation)
    record["activation_evidence_sha256"] = hashlib.sha256(
        activation_path.read_bytes()
    ).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
