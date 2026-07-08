from __future__ import annotations

import json
from pathlib import Path

from vibesec.core.review_runner import run_review
from vibesec.core.review_schema import validate_review_output_dir
from vibesec.core.review_packets import build_review_packet
from vibesec.core.risk_model import Finding, ProjectProfile
from vibesec.core.scan_runner import run_scan


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


def test_review_packet_recursively_redacts_provider_shaped_tokens(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    token = "sk-tool-provider-shaped-value-1234567890"
    (project / f"{token}.ts").write_text(f"const token = '{token}'\n", encoding="utf-8")
    profile = ProjectProfile(
        path=str(project),
        project_type="MCP / IPC Tool",
        technologies=["TypeScript"],
        data_risk=["api_key"],
        launch_stage="public_launch",
        risk_level="L3",
        profile_evidence=[f"profile evidence mentions {token}"],
    )
    finding = Finding(
        id="VSG-TEST-SECRET",
        title=f"Provider-shaped token {token}",
        severity="P1",
        category="Secrets",
        affected_files=[f"{token}.ts:1"],
        evidence=f"evidence {token}",
        technical_reason=f"reason {token}",
        confidence="confirmed",
        source_type="runtime",
        fingerprint=f"fingerprint:{token}",
    )

    packet_text = json.dumps(build_review_packet(project, profile, finding), ensure_ascii=False)

    assert token not in packet_text
    assert "sk-t...7890" in packet_text


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
        llm_packet = json.loads((output / "llm_review_packet.json").read_text(encoding="utf-8"))
        decision_output = json.loads((output / "agent_review_decisions.json").read_text(encoding="utf-8"))
        decision_json = decision_output["decisions"]
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
        assert llm_packet["schema_version"] == "1.0", case
        assert len(llm_packet["rule_findings"]) == len(verdicts), case
        assert llm_packet["rule_findings"][0]["evidence_role"] == "baseline_hint_not_final_judgment", case
        assert llm_packet["project_profile"]["project_type"], case
        assert llm_packet["requested_outputs"], case
        assert decision_output["schema_version"] == "1.0", case
        assert decision_output["summary"]["agent_decision_count"] == len(verdicts), case
        assert len(decision_json) == len(verdicts), case
        assert decision_json[0]["finding_id"] == verdict["finding_id"], case
        assert decision_json[0]["verdict"] == verdict["verdict"], case
        assert decision_json[0]["recommended_action"] == verdict["recommended_action"], case
        assert decision_json[0]["agent_next_step"] == verdict["agent_next_step"], case
        assert decision_json[0]["decision_id"], case
        assert decision_json[0]["source_output"] == "ai_review.json", case
        assert isinstance(decision_json[0]["blocks_launch"], bool), case
        assert isinstance(decision_json[0]["safe_for_agent_fix"], bool), case
        assert decision_json[0]["safe_to_auto_suppress"] is False, case
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
    llm_packet = json.loads((output / "llm_review_packet.json").read_text(encoding="utf-8"))
    decision_output = json.loads((output / "agent_review_decisions.json").read_text(encoding="utf-8"))
    decision_json = decision_output["decisions"]
    candidates = json.loads((output / "suppression_candidates.json").read_text(encoding="utf-8"))
    queue = (output / "human_review_queue.md").read_text(encoding="utf-8")
    decisions = (output / "agent_review_decisions.md").read_text(encoding="utf-8")

    finding_ids = {verdict["finding_id"] for verdict in verdicts}
    queue_ids = {finding_id for finding_id in finding_ids if finding_id in queue}
    decision_ids = {finding_id for finding_id in finding_ids if finding_id in decisions}
    json_decision_ids = {decision["finding_id"] for decision in decision_json}
    must_review_decisions = [decision for decision in decision_json if decision["must_review"]]
    decision_type_by_id = {decision["finding_id"]: decision["decision_type"] for decision in decision_json}

    assert summary["reviewed_findings"] == 4
    assert llm_packet["schema_version"] == "1.0"
    assert llm_packet["project_profile"]["project_type"]
    assert llm_packet["sensitive_assets"]
    assert llm_packet["attack_surfaces"]
    assert llm_packet["auth_and_data_flow"]["missing_context_questions"]
    assert llm_packet["agent_tool_surfaces"]
    assert len(llm_packet["rule_findings"]) == len(verdicts)
    assert all(item["evidence_role"] == "baseline_hint_not_final_judgment" for item in llm_packet["rule_findings"])
    assert decision_output["schema_version"] == "1.0"
    assert decision_output["summary"]["must_review_count"] == 2
    assert summary["agent_decision_count"] == 4
    assert summary["must_review_count"] == 2
    assert summary["downgrade_candidate_count"] == 1
    assert summary["suppression_candidate_count"] == 1
    assert queue_ids == {"VSG-PROD-FIX-001", "VSG-PROD-REVIEW-001"}
    assert queue_ids != finding_ids
    assert decision_ids == finding_ids
    assert json_decision_ids == finding_ids
    assert len(must_review_decisions) == summary["must_review_count"]
    assert decision_type_by_id["VSG-PROD-FIX-001"] == "fix_after_confirmation"
    assert decision_type_by_id["VSG-PROD-REVIEW-001"] == "must_confirm_before_fix"
    assert decision_type_by_id["VSG-PROD-DOWN-001"] == "downgrade_candidate"
    assert decision_type_by_id["VSG-PROD-SUP-001"] == "false_positive_candidate"
    assert "VSG-PROD-DOWN-001" not in queue
    assert "VSG-PROD-SUP-001" not in queue
    assert all(verdict["safe_to_auto_suppress"] is False for verdict in verdicts)
    assert all(candidate["safe_to_auto_suppress"] is False for candidate in candidates)
    assert all(decision["safe_to_auto_suppress"] is False for decision in decision_json)


def test_scan_review_validate_e2e_product_flow(tmp_path):
    project = Path("tests/fixtures/vulnerable_ai_agent_app")
    scan_output = tmp_path / "scan"
    review_output = tmp_path / "review"

    scan_summary = run_scan(str(project), str(scan_output), include_adapters=False)
    assert scan_summary["total_findings"] > 0
    findings_path = scan_output / "findings.json"
    assert findings_path.exists()

    review_summary = run_review(str(findings_path), str(project), str(review_output), include_p2=True)
    validation = validate_review_output_dir(review_output)

    verdicts = json.loads((review_output / "ai_review.json").read_text(encoding="utf-8"))
    llm_packet = json.loads((review_output / "llm_review_packet.json").read_text(encoding="utf-8"))
    decision_output = json.loads((review_output / "agent_review_decisions.json").read_text(encoding="utf-8"))
    decision_json = decision_output["decisions"]
    candidates = json.loads((review_output / "suppression_candidates.json").read_text(encoding="utf-8"))
    queue = (review_output / "human_review_queue.md").read_text(encoding="utf-8")
    decisions = (review_output / "agent_review_decisions.md").read_text(encoding="utf-8")
    summary_md = (review_output / "ai_review_summary.md").read_text(encoding="utf-8")
    packets_text = (review_output / "review_packets.json").read_text(encoding="utf-8")

    finding_ids = {verdict["finding_id"] for verdict in verdicts}
    queue_ids = {finding_id for finding_id in finding_ids if finding_id in queue}
    markdown_decision_ids = {finding_id for finding_id in finding_ids if finding_id in decisions}
    json_decision_ids = {decision["finding_id"] for decision in decision_json}
    must_review_decisions = [decision for decision in decision_json if decision["must_review"]]

    assert validation["agent_decisions"] == len(verdicts)
    assert llm_packet["schema_version"] == "1.0"
    assert len(llm_packet["rule_findings"]) == len(verdicts)
    assert all(item["evidence_role"] == "baseline_hint_not_final_judgment" for item in llm_packet["rule_findings"])
    assert llm_packet["product_context"]["review_positioning"].startswith("LLM-native")
    assert llm_packet["sensitive_assets"]
    assert llm_packet["attack_surfaces"]
    assert llm_packet["agent_tool_surfaces"]
    assert decision_output["schema_version"] == "1.0"
    assert decision_output["summary"]["agent_decision_count"] == len(verdicts)
    assert review_summary["reviewed_findings"] == len(verdicts)
    assert review_summary["agent_decision_count"] == len(verdicts)
    assert review_summary["must_review_count"] == len(must_review_decisions)
    assert queue_ids != finding_ids
    assert markdown_decision_ids == finding_ids
    assert json_decision_ids == finding_ids
    assert "- Must review count: " + str(review_summary["must_review_count"]) in summary_md
    assert "- Agent decision count: " + str(len(decision_json)) in summary_md
    assert all(decision["decision_type"] not in {"downgrade_candidate", "suppression_candidate", "false_positive_candidate"} for decision in must_review_decisions)
    assert all(verdict["safe_to_auto_suppress"] is False for verdict in verdicts)
    assert all(candidate["safe_to_auto_suppress"] is False for candidate in candidates)
    assert "sk-proj-secret-value-1234567890" not in packets_text
    assert "ghp_providersecretvalue1234567890" not in packets_text
