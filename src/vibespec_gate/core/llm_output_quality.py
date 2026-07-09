from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .llm_output_schema import STUB_DISCLAIMER, validate_llm_review_outputs
from .review_llm_packet import REQUESTED_OUTPUTS
from .review_schema import SchemaValidationError


MAX_SCORE = 100
DEFAULT_HARD_FAIL_CHECKS = {
    "schema_validation",
    "unsafe_offensive_guidance",
    "safe_to_auto_suppress_false",
    "stub_disclaimer_absent",
    "launch_decision",
    "launch_decision_consistency",
    "p1_cross_output_coverage",
    "missing_evidence_acknowledged",
    "agent_fix_plan_bounded",
    "retest_commands_present",
}


def score_llm_review_outputs(fixture_dir: str | Path) -> dict[str, Any]:
    fixture = Path(fixture_dir)
    expected_path = _expected_path(fixture)
    expected = _load_json(expected_path)
    output_dir = fixture / "outputs" if (fixture / "outputs").exists() else fixture
    checks: list[dict[str, Any]] = []

    validation_error = ""
    try:
        validate_llm_review_outputs(output_dir, allow_stub=False)
    except SchemaValidationError as exc:
        validation_error = str(exc)
    checks.append(_check("schema_validation", not validation_error, 0, validation_error or "Final LLM outputs pass schema and safety validation."))
    if validation_error:
        return _result(expected, output_dir, checks, score=0)

    security = _load_json(output_dir / "security_review_findings.json")
    combined = _combined_output_text(output_dir)
    findings = security.get("findings", [])
    actual_launch_decision = _actual_launch_decision(output_dir, security)

    checks.extend(
        [
            _check(
                "launch_decision",
                actual_launch_decision == expected.get("expected_launch_decision"),
                10,
                f"Actual launch decision {actual_launch_decision!r}; expected {expected.get('expected_launch_decision')!r}.",
            ),
            _check(
                "required_finding_ids",
                _all_present(expected.get("required_finding_ids", []), combined),
                10,
                "Required finding IDs are cited across outputs.",
            ),
            _check(
                "required_evidence_files",
                _all_present(expected.get("required_evidence_files", []), combined),
                10,
                "Required evidence files are cited across outputs.",
            ),
            _check(
                "required_sections",
                _required_sections_exist(output_dir, expected.get("required_sections", [])),
                10,
                "All required output files exist.",
            ),
            _check(
                "must_include_phrases",
                _all_present(expected.get("must_include_phrases", []), combined.lower()),
                10,
                "All required quality phrases are present.",
            ),
            _check(
                "must_not_include_phrases",
                not _any_present(expected.get("must_not_include_phrases", []), combined),
                10,
                "Forbidden phrases are absent.",
            ),
            _check("stub_disclaimer_absent", STUB_DISCLAIMER not in combined, 10, "Stub disclaimer is absent."),
            _check(
                "safe_to_auto_suppress_false",
                all(finding.get("safe_to_auto_suppress") is False for finding in findings),
                10,
                "`safe_to_auto_suppress` is false for every finding.",
            ),
            _check(
                "agent_fix_plan_bounded",
                _agent_fix_plan_bounded(output_dir / "agent_fix_plan.md"),
                10,
                "Agent fix plan includes human gate, bounded tasks, prohibited changes, and verification commands.",
            ),
            _check(
                "retest_commands_present",
                _retest_commands_present(output_dir / "retest_checklist.md"),
                10,
                "Retest checklist includes rerunnable commands.",
            ),
            _check(
                "p1_cross_output_coverage",
                _required_ids_in_each_output(output_dir, expected.get("required_finding_ids", [])),
                0,
                "Required P0/P1 finding IDs appear in every required output.",
            ),
            _check(
                "launch_decision_consistency",
                _launch_decision_consistent_with_findings(security, actual_launch_decision),
                0,
                "Top-level launch decision is consistent with the highest finding launch impact.",
            ),
            _check(
                "missing_evidence_acknowledged",
                _missing_evidence_acknowledged(findings),
                0,
                "Review/verify-before-fix findings list concrete missing evidence.",
            ),
        ]
    )
    soft_score = sum(item["points"] for item in checks if item["passed"])
    return _result(expected, output_dir, checks, score=soft_score, actual_launch_decision=actual_launch_decision)


def _result(
    expected: dict[str, Any],
    output_dir: Path,
    checks: list[dict[str, Any]],
    score: int,
    actual_launch_decision: str | None = None,
) -> dict[str, Any]:
    minimum = int(expected.get("minimum_score", 100))
    failed = [item["check_id"] for item in checks if not item["passed"]]
    hard_fail_set = set(expected.get("hard_fail_checks") or DEFAULT_HARD_FAIL_CHECKS)
    hard_failures = [item for item in failed if item in hard_fail_set]
    score_passed = score >= minimum
    hard_fail_passed = not hard_failures
    return {
        "schema_version": "1.0",
        "case_id": expected.get("case_id", output_dir.parent.name),
        "risk_domain": expected.get("risk_domain", "unknown"),
        "expected_launch_decision": expected.get("expected_launch_decision", ""),
        "actual_launch_decision": actual_launch_decision or "",
        "passed": score_passed and hard_fail_passed,
        "score": score,
        "soft_score": score,
        "max_score": MAX_SCORE,
        "minimum_score": minimum,
        "score_passed": score_passed,
        "hard_fail_passed": hard_fail_passed,
        "hard_failures": hard_failures,
        "failed_checks": failed,
        "checks": checks,
    }


def _check(check_id: str, passed: bool, points: int, reason: str) -> dict[str, Any]:
    return {"check_id": check_id, "passed": passed, "points": points, "reason": reason}


def _expected_path(path: Path) -> Path:
    if (path / "expected_quality.json").exists():
        return path / "expected_quality.json"
    if (path.parent / "expected_quality.json").exists():
        return path.parent / "expected_quality.json"
    return path / "expected_quality.json"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _combined_output_text(output_dir: Path) -> str:
    chunks = []
    for output_name in REQUESTED_OUTPUTS:
        chunks.append((output_dir / output_name).read_text(encoding="utf-8"))
    return "\n".join(chunks)


def _actual_launch_decision(output_dir: Path, security: dict[str, Any]) -> str:
    value = security.get("launch_decision")
    if isinstance(value, str) and value:
        return value
    summary = (output_dir / "nontechnical_user_summary.md").read_text(encoding="utf-8")
    match = re.search(r"^Launch decision:\s*(\S+)", summary, re.MULTILINE)
    return match.group(1) if match else ""


def _all_present(needles: list[str], haystack: str) -> bool:
    return all(str(needle).lower() in haystack.lower() for needle in needles)


def _any_present(needles: list[str], haystack: str) -> bool:
    return any(str(needle) in haystack for needle in needles)


def _required_sections_exist(output_dir: Path, required: list[str]) -> bool:
    required_set = set(required or REQUESTED_OUTPUTS)
    return required_set == set(REQUESTED_OUTPUTS) and all((output_dir / name).exists() for name in required_set)


def _agent_fix_plan_bounded(path: Path) -> bool:
    text = path.read_text(encoding="utf-8").lower()
    if re.search(r"^(?:- )?allowed change scope:.*(?:rewrite all|all ipc handlers|disable contextisolation)", text, re.MULTILINE):
        return False
    if re.search(r"^### task:.*rewrite all", text, re.MULTILINE):
        return False
    return all(
        phrase in text
        for phrase in (
            "## human confirmation gate",
            "## bounded tasks",
            "finding ids:",
            "allowed change scope:",
            "## prohibited changes",
            "## verification commands",
        )
    )


def _retest_commands_present(path: Path) -> bool:
    text = path.read_text(encoding="utf-8").lower()
    return "## commands to rerun" in text and "```powershell" in text and "no retest command" not in text


def _required_ids_in_each_output(output_dir: Path, required_ids: list[str]) -> bool:
    for output_name in REQUESTED_OUTPUTS:
        text = (output_dir / output_name).read_text(encoding="utf-8")
        for finding_id in required_ids:
            if finding_id not in text:
                return False
    return True


def _launch_decision_consistent_with_findings(security: dict[str, Any], actual: str) -> bool:
    impacts = {
        item.get("launch_impact")
        for item in security.get("findings", [])
        if isinstance(item, dict)
    }
    if "block" in impacts:
        return actual == "BLOCK"
    if "review" in impacts:
        return actual == "REVIEW"
    return actual in {"PASS_WITH_WARNINGS", "PASS"}


def _missing_evidence_acknowledged(findings: Any) -> bool:
    if not isinstance(findings, list):
        return False
    for finding in findings:
        if not isinstance(finding, dict):
            return False
        needs_evidence = finding.get("launch_impact") == "review" or finding.get("recommended_action") == "verify_before_fix"
        if needs_evidence and not finding.get("missing_evidence"):
            return False
    return True
