from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from vibespec_gate.core.llm_output_quality import score_llm_review_outputs  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: py -3 scripts\\compare_host_agent_samples.py <samples_root>", file=sys.stderr)
        return 2
    result = compare_samples(Path(args[0]))
    write_reports(Path(args[0]), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def compare_samples(samples_root: Path) -> dict[str, object]:
    sample_dirs = sorted(samples_root.glob("*/*/expected_quality.json"))
    if not sample_dirs:
        return {
            "schema_version": "1.0",
            "sample_count": 0,
            "message": "No host-agent samples found. Add manually generated outputs to compare.",
        }
    cases = []
    agents = set()
    for expected in sample_dirs:
        case_dir = expected.parent
        agent = case_dir.parent.name
        agents.add(agent)
        score = score_llm_review_outputs(case_dir)
        metadata = _load_metadata(case_dir)
        cases.append(
            {
                "agent": agent,
                "case_id": score["case_id"],
                "generated_by": metadata.get("generated_by", ""),
                "generated_at": metadata.get("generated_at", ""),
                "risk_domain": score["risk_domain"],
                "expected_launch_decision": score["expected_launch_decision"],
                "actual_launch_decision": score["actual_launch_decision"],
                "soft_score": score["soft_score"],
                "passed": score["passed"],
                "hard_failures": score["hard_failures"],
                "failed_checks": score["failed_checks"],
                "human_quality_decision": metadata.get("human_quality_decision"),
                "scorer_human_agreement": metadata.get("scorer_human_agreement"),
                "sample_path": str(case_dir),
            }
        )
    return {
        "schema_version": "1.0",
        "sample_count": len(cases),
        "agents": sorted(agents),
        "cases": cases,
    }


def write_reports(samples_root: Path, result: dict[str, object]) -> None:
    reports = samples_root.parent / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "host_agent_sample_matrix.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (reports / "host_agent_sample_matrix.md").write_text(render_matrix_markdown(result), encoding="utf-8")
    (reports / "scorer_disagreement_log.md").write_text(render_disagreement_log(result), encoding="utf-8")


def render_matrix_markdown(result: dict[str, object]) -> str:
    lines = [
        "# Host-Agent Sample Matrix",
        "",
        f"Sample count: {result.get('sample_count', 0)}",
        "",
        "| agent | case_id | expected_launch_decision | actual_launch_decision | soft_score | hard_failures | passed | human_quality_decision | scorer_human_agreement |",
        "|---|---|---|---|---:|---|---|---|---|",
    ]
    for case in result.get("cases", []):
        hard = ", ".join(case.get("hard_failures", []))
        lines.append(
            "| {agent} | {case_id} | {expected} | {actual} | {score} | {hard} | {passed} | {human} | {agreement} |".format(
                agent=case.get("agent", ""),
                case_id=case.get("case_id", ""),
                expected=case.get("expected_launch_decision", ""),
                actual=case.get("actual_launch_decision", ""),
                score=case.get("soft_score", ""),
                hard=hard,
                passed=str(case.get("passed", "")).lower(),
                human=case.get("human_quality_decision") or "",
                agreement=case.get("scorer_human_agreement") if case.get("scorer_human_agreement") is not None else "",
            )
        )
    lines.append("")
    return "\n".join(lines)


def render_disagreement_log(result: dict[str, object]) -> str:
    lines = ["# Scorer Disagreement Log", ""]
    disagreements = [
        case for case in result.get("cases", [])
        if case.get("scorer_human_agreement") is False
    ]
    if not disagreements:
        lines.append("No scorer/human disagreements recorded in sample metadata.")
        lines.append("")
        return "\n".join(lines)
    for case in disagreements:
        lines.extend(
            [
                f"## {case.get('agent')} / {case.get('case_id')}",
                "",
                f"- Scorer passed: {case.get('passed')}",
                f"- Human quality decision: {case.get('human_quality_decision')}",
                f"- Failed checks: {', '.join(case.get('failed_checks', []))}",
                "",
            ]
        )
    return "\n".join(lines)


def _load_metadata(case_dir: Path) -> dict[str, object]:
    path = case_dir / "sample_metadata.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
