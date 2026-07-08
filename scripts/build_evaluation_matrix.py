from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REVIEW_CASES = ROOT / "tests" / "evaluation_cases" / "review"
DEFAULT_OUTPUT = ROOT / "test output" / "phase7_release_hardening"
DOMAINS = [
    "Secrets",
    "Auth/API",
    "Desktop/Electron",
    "MCP/IPC",
    "LLM/Agent",
    "Config/Deployment",
    "Dependency",
]


def build_matrix() -> dict[str, Any]:
    cases = []
    for expected_path in sorted(REVIEW_CASES.rglob("expected.json")):
        case_dir = expected_path.parent
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        findings = json.loads((case_dir / "findings.json").read_text(encoding="utf-8"))
        finding = findings[0]
        domain = domain_for(finding)
        decision_type = decision_type_for(expected)
        cases.append(
            {
                "case_id": case_dir.name,
                "domain": domain,
                "fixture_path": str(case_dir.relative_to(ROOT)).replace("\\", "/"),
                "expected_verdict": expected["expected_verdict"],
                "expected_action": expected["expected_action"],
                "expected_agent_next_step": expected["expected_agent_next_step"],
                "expected_decision_type": decision_type,
                "expected_must_review": bool(expected["expected_human_queue"]),
                "risk_pattern": finding["title"],
                "downgrade_or_suppression_reason": reason_for(expected, finding),
                "regression_class": regression_class_for(domain, expected),
            }
        )
    counts = Counter(case["domain"] for case in cases)
    return {
        "schema_version": "1.0",
        "generated_by": "scripts/build_evaluation_matrix.py",
        "domains": [{"domain": domain, "case_count": counts.get(domain, 0)} for domain in DOMAINS],
        "total_cases": len(cases),
        "cases": cases,
    }


def write_matrix(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    matrix = build_matrix()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "evaluation_matrix.json").write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "evaluation_matrix.md").write_text(matrix_markdown(matrix), encoding="utf-8")
    return matrix


def matrix_markdown(matrix: dict[str, Any]) -> str:
    lines = [
        "# Evaluation Matrix",
        "",
        f"- Schema version: {matrix['schema_version']}",
        f"- Total cases: {matrix['total_cases']}",
        "",
        "## Domain Coverage",
        "",
        "| Domain | Cases |",
        "| --- | ---: |",
    ]
    for item in matrix["domains"]:
        lines.append(f"| {item['domain']} | {item['case_count']} |")
    lines.extend(
        [
            "",
            "## Cases",
            "",
            "| Case | Domain | Verdict | Action | Next step | Decision type | Must review |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for case in matrix["cases"]:
        lines.append(
            "| {case_id} | {domain} | {expected_verdict} | {expected_action} | {expected_agent_next_step} | "
            "{expected_decision_type} | {expected_must_review} |".format(**case)
        )
    lines.append("")
    return "\n".join(lines)


def domain_for(finding: dict[str, Any]) -> str:
    combined = f"{finding.get('category', '')} {finding.get('title', '')}".lower()
    if any(word in combined for word in ("secret", "token", "api key", "apikey")):
        return "Secrets"
    if any(word in combined for word in ("desktop", "electron")):
        return "Desktop/Electron"
    if any(word in combined for word in ("mcp", "ipc")):
        return "MCP/IPC"
    if any(word in combined for word in ("llm", "agent", "prompt")):
        return "LLM/Agent"
    if re.search(r"\b(auth|authentication|authorization)\b", combined) or any(word in combined for word in ("owner", "api route")):
        return "Auth/API"
    if any(word in combined for word in ("config", "debug", "deployment", "cors", "header")):
        return "Config/Deployment"
    if "depend" in combined:
        return "Dependency"
    return "Config/Deployment"


def decision_type_for(expected: dict[str, Any]) -> str:
    verdict = expected["expected_verdict"]
    action = expected["expected_action"]
    if verdict == "needs_human_review":
        return "must_confirm_before_fix"
    if action == "fix":
        return "fix_after_confirmation"
    if verdict == "false_positive":
        return "false_positive_candidate"
    if action == "suppress":
        return "suppression_candidate"
    if action == "downgrade":
        return "downgrade_candidate"
    return "informational_decision"


def reason_for(expected: dict[str, Any], finding: dict[str, Any]) -> str:
    if expected["expected_action"] == "downgrade":
        return f"Downgrade expected because {finding['technical_reason']}"
    if expected["expected_action"] == "suppress" or expected["expected_verdict"] == "false_positive":
        return f"Suppression candidate because {finding['technical_reason']}"
    return "Not a downgrade or suppression case."


def regression_class_for(domain: str, expected: dict[str, Any]) -> str:
    if expected["expected_human_queue"]:
        return f"{domain} must-review precision"
    if expected["expected_action"] in {"downgrade", "suppress"}:
        return f"{domain} false-positive reduction"
    return f"{domain} decision contract"


def main() -> int:
    write_matrix()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
