from __future__ import annotations

import json
from pathlib import Path

from scripts.build_evaluation_matrix import DOMAINS, build_matrix, decision_type_for


REVIEW_CASES = Path("tests/evaluation_cases/review")
REQUIRED_LLM_OUTPUTS = {
    "nontechnical_user_summary.md",
    "launch_risk_report.md",
    "security_review_findings.json",
    "agent_fix_plan.md",
    "retest_checklist.md",
}


def _review_case_dirs() -> list[Path]:
    return sorted(path.parent for path in REVIEW_CASES.rglob("expected.json"))


def test_evaluation_matrix_covers_all_review_fixtures():
    matrix = build_matrix()
    matrix_by_case = {case["case_id"]: case for case in matrix["cases"]}
    case_dirs = _review_case_dirs()

    assert matrix["schema_version"] == "1.0"
    assert matrix["total_cases"] == len(case_dirs)
    assert set(matrix_by_case) == {case.name for case in case_dirs}
    assert all(item["case_count"] > 0 for item in matrix["domains"] if item["domain"] in DOMAINS)

    for case_dir in case_dirs:
        expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
        matrix_case = matrix_by_case[case_dir.name]
        assert matrix_case["fixture_path"] == str(case_dir).replace("\\", "/")
        assert matrix_case["expected_verdict"] == expected["expected_verdict"]
        assert matrix_case["expected_action"] == expected["expected_action"]
        assert matrix_case["expected_agent_next_step"] == expected["expected_agent_next_step"]
        assert matrix_case["expected_decision_type"] == decision_type_for(expected)
        assert matrix_case["expected_must_review"] is expected["expected_human_queue"]
        assert matrix_case["risk_pattern"]
        assert matrix_case["regression_class"]


def test_obsolete_phase7_release_hardening_goal_is_absent():
    obsolete_goal = Path("test output/phase7_evaluation_release_hardening_goal.md")

    assert not obsolete_goal.exists()


def test_llm_review_contract_documents_required_outputs():
    contract = Path("docs/usage/llm_review_contract.md").read_text(encoding="utf-8")
    strategy = Path("docs/design/model_invocation_strategy.md").read_text(encoding="utf-8")

    for output_name in REQUIRED_LLM_OUTPUTS:
        assert output_name in contract

    for required_field in (
        "llm_review_packet.json",
        "baseline_hint_not_final_judgment",
        "project_profile",
        "sensitive_assets",
        "attack_surfaces",
        "auth_and_data_flow",
        "agent_tool_surfaces",
        "safety_boundaries",
    ):
        assert required_field in contract

    for mode in (
        "Host-Agent Mode",
        "API-Backed Mode",
        "Local / Private Model Mode",
        "No-Model Deterministic Baseline",
    ):
        assert mode in strategy


def test_core_docs_keep_llm_native_positioning():
    docs = [
        Path("README.md"),
        Path("SKILL.md"),
        Path("docs/usage/quickstart.md"),
        Path("docs/usage/examples.md"),
        Path("docs/usage/agent_review_cookbook.md"),
        Path("docs/usage/verification.md"),
    ]
    forbidden_claims = (
        "is an offline scanner",
        "is a local-only scanner",
        "is a static-analysis CLI",
        "is a rule-only review engine",
    )

    for doc in docs:
        text = doc.read_text(encoding="utf-8").lower()
        if doc == Path("README.md"):
            assert "launch security review" in text
            assert "products built with vibe coding" in text
        else:
            assert "llm-native" in text, doc
            assert "llm_review_packet.json" in text, doc
        for claim in forbidden_claims:
            assert claim not in text, (doc, claim)


def test_repository_has_one_authoritative_skill_entry():
    assert Path("SKILL.md").exists()
    assert not Path("skill/SKILL.md").exists()
