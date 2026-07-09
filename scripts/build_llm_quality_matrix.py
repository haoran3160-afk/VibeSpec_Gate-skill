from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
FIXTURE_ROOT = ROOT / "tests" / "evaluation_cases" / "llm_outputs"
BAD_FIXTURE_ROOT = ROOT / "tests" / "evaluation_cases" / "llm_outputs_bad"
OUTPUT_ROOT = ROOT / "test output" / "phase9_real_llm_review_evaluation"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from vibespec_gate.core.llm_output_quality import score_llm_review_outputs  # noqa: E402


def main() -> int:
    matrix = build_matrix()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "llm_quality_matrix.json").write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT_ROOT / "llm_quality_matrix.md").write_text(render_markdown(matrix), encoding="utf-8")
    print(json.dumps(matrix, ensure_ascii=False, indent=2))
    return 0 if matrix["expectations_failed"] == 0 else 1


def build_matrix() -> dict[str, object]:
    cases = []
    for fixture_kind, root in (("golden", FIXTURE_ROOT), ("bad", BAD_FIXTURE_ROOT)):
        for expected in sorted(root.glob("*/expected_quality.json")):
            cases.append(_score_case(expected.parent, fixture_kind))
    expectations_met = sum(1 for case in cases if case["expectation_met"])
    return {
        "schema_version": "1.1",
        "total_cases": len(cases),
        "golden_cases": sum(1 for case in cases if case["fixture_kind"] == "golden"),
        "bad_cases": sum(1 for case in cases if case["fixture_kind"] == "bad"),
        "expectations_met": expectations_met,
        "expectations_failed": len(cases) - expectations_met,
        "cases": cases,
    }


def _score_case(fixture: Path, fixture_kind: str) -> dict[str, object]:
    expected = json.loads((fixture / "expected_quality.json").read_text(encoding="utf-8"))
    score = score_llm_review_outputs(fixture)
    expected_pass = bool(expected.get("expected_pass", True))
    actual_pass = bool(score["passed"])
    expectation_met = expected_pass is actual_pass
    return {
        "case_id": score["case_id"],
        "fixture_kind": fixture_kind,
        "risk_domain": score["risk_domain"],
        "expected_launch_decision": score["expected_launch_decision"],
        "actual_launch_decision": score["actual_launch_decision"],
        "score": score["score"],
        "soft_score": score["soft_score"],
        "max_score": score["max_score"],
        "minimum_score": score["minimum_score"],
        "expected_pass": expected_pass,
        "actual_pass": actual_pass,
        "expectation_met": expectation_met,
        "hard_failures": score["hard_failures"],
        "failed_checks": score["failed_checks"],
        "fixture_path": str(fixture.relative_to(ROOT)).replace("\\", "/"),
    }


def render_markdown(matrix: dict[str, object]) -> str:
    lines = [
        "# LLM Review Quality Matrix",
        "",
        f"Total cases: {matrix['total_cases']}",
        f"Golden cases: {matrix['golden_cases']}",
        f"Bad cases: {matrix['bad_cases']}",
        f"Expectations met: {matrix['expectations_met']}",
        f"Expectations failed: {matrix['expectations_failed']}",
        "",
        "| case_id | kind | risk_domain | expected_launch_decision | actual_launch_decision | score | expected_pass | actual_pass | expectation_met | hard_failures | failed_checks |",
        "|---|---|---|---|---|---:|---|---|---|---|---|",
    ]
    for case in matrix["cases"]:
        failed = ", ".join(case["failed_checks"]) if case["failed_checks"] else ""
        hard = ", ".join(case["hard_failures"]) if case["hard_failures"] else ""
        lines.append(
            "| {case_id} | {kind} | {risk_domain} | {expected} | {actual} | {score}/{max_score} | {expected_pass} | {actual_pass} | {expectation_met} | {hard} | {failed} |".format(
                case_id=case["case_id"],
                kind=case["fixture_kind"],
                risk_domain=case["risk_domain"],
                expected=case["expected_launch_decision"],
                actual=case["actual_launch_decision"],
                score=case["score"],
                max_score=case["max_score"],
                expected_pass=str(case["expected_pass"]).lower(),
                actual_pass=str(case["actual_pass"]).lower(),
                expectation_met=str(case["expectation_met"]).lower(),
                hard=hard,
                failed=failed,
            )
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
