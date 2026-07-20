from __future__ import annotations

import json
from pathlib import Path


EVAL_ROOT = Path("evals")


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


def _load(name: str) -> dict[str, object]:
    return json.loads((EVAL_ROOT / name).read_text(encoding="utf-8"))
