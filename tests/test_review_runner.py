from __future__ import annotations

import json
from pathlib import Path

from vibesec.core.review_runner import run_review


BASE = Path("tests/evaluation_cases/review")
PRODUCT_BASE = Path("tests/evaluation_cases/review_product")


def _cases() -> list[Path]:
    return sorted(path.parent for path in BASE.rglob("expected.json"))


def test_review_cases_cover_phase4_minimum():
    assert len(_cases()) >= 10
    desktop = [case for case in _cases() if case.name.startswith("electron_")]
    mcp = [case for case in _cases() if case.name.startswith("mcp_")]
    llm = [case for case in _cases() if case.name.startswith("llm_")]
    assert len(desktop) >= 4
    assert len(mcp) >= 4
    assert len(llm) >= 4


def test_rule_based_review_cases(tmp_path):
    for case in _cases():
        expected = json.loads((case / "expected.json").read_text(encoding="utf-8"))
        output = tmp_path / case.relative_to(BASE)
        summary = run_review(
            str(case / "findings.json"),
            str(case),
            str(output),
            include_p2=True,
        )
        verdicts = json.loads((output / "ai_review.json").read_text(encoding="utf-8"))
        queue = (output / "human_review_queue.md").read_text(encoding="utf-8")
        decisions = (output / "agent_review_decisions.md").read_text(encoding="utf-8")
        packets_text = (output / "review_packets.json").read_text(encoding="utf-8")

        assert verdicts, case
        verdict = verdicts[0]
        assert verdict["verdict"] == expected["expected_verdict"], case
        assert verdict["recommended_action"] == expected["expected_action"], case
        assert verdict["agent_next_step"] == expected["expected_agent_next_step"], case
        assert verdict["safe_to_auto_suppress"] is False, case
        assert verdict["inspect_files"], case
        assert verdict["prohibited_changes"], case
        assert verdict["verification_commands"], case
        assert (verdict["finding_id"] in queue) is expected["expected_human_queue"], case
        assert "## Must confirm before fix" in queue
        assert "## Likely true, fix after confirmation" in queue
        assert "## Downgrade candidates" not in queue
        assert "## Suppression candidates" not in queue
        assert verdict["finding_id"] in decisions, case
        assert "## Downgrade candidates" in decisions
        assert "## Suppression and false-positive candidates" in decisions
        assert summary["reviewed_findings"] >= 1, case
        assert "sk-proj-secret-value-1234567890" not in packets_text, case
        assert "ghp_providersecretvalue1234567890" not in packets_text, case


def test_product_queue_semantics_do_not_expand_to_all_findings(tmp_path):
    case = PRODUCT_BASE / "queue_semantics_mixed"
    output = tmp_path / "queue_semantics_mixed"
    summary = run_review(
        str(case / "findings.json"),
        str(case),
        str(output),
        include_p2=True,
    )
    verdicts = json.loads((output / "ai_review.json").read_text(encoding="utf-8"))
    candidates = json.loads((output / "suppression_candidates.json").read_text(encoding="utf-8"))
    queue = (output / "human_review_queue.md").read_text(encoding="utf-8")
    decisions = (output / "agent_review_decisions.md").read_text(encoding="utf-8")

    finding_ids = {verdict["finding_id"] for verdict in verdicts}
    queue_ids = {finding_id for finding_id in finding_ids if finding_id in queue}
    decision_ids = {finding_id for finding_id in finding_ids if finding_id in decisions}

    assert summary["reviewed_findings"] == 4
    assert summary["agent_decision_count"] == 4
    assert summary["must_review_count"] == 2
    assert summary["downgrade_candidate_count"] == 1
    assert summary["suppression_candidate_count"] == 1
    assert queue_ids == {"VSG-PROD-FIX-001", "VSG-PROD-REVIEW-001"}
    assert queue_ids != finding_ids
    assert decision_ids == finding_ids
    assert "VSG-PROD-DOWN-001" not in queue
    assert "VSG-PROD-SUP-001" not in queue
    assert all(verdict["safe_to_auto_suppress"] is False for verdict in verdicts)
    assert all(candidate["safe_to_auto_suppress"] is False for candidate in candidates)
