from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PHASE11_ROOT = ROOT / "test output" / "phase11_real_host_agent_calibration"
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from verify_phase11_calibration import ALLOWED_RUBRIC_ACTIONS, is_completed_human_record  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) not in {1, 2}:
        print("usage: py -3 scripts\\import_phase11_human_review.py <record_json> [phase11_root]", file=sys.stderr)
        return 2
    record_path = Path(args[0])
    phase_root = Path(args[1]) if len(args) == 2 else DEFAULT_PHASE11_ROOT
    try:
        result = import_human_review(record_path, phase_root)
    except Exception as exc:  # noqa: BLE001 - CLI reports validation failures directly.
        print(f"FAIL import human review: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def import_human_review(record_path: Path, phase_root: Path) -> dict[str, object]:
    record = _load_json(record_path)
    validate_human_record(record)
    ledger_path = phase_root / "human_calibration_ledger.json"
    ledger = _load_json(ledger_path)
    records = list(ledger.get("records", []))
    review_id = str(record["review_id"])
    duplicate = [existing for existing in records if existing.get("review_id") == review_id]
    if duplicate:
        raise ValueError(f"duplicate review_id: {review_id}")
    records.append(record)
    ledger["schema_version"] = ledger.get("schema_version", "1.0")
    ledger["phase"] = ledger.get("phase", "phase11_real_host_agent_calibration")
    ledger["records"] = records
    _refresh_ledger_status(ledger)
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    (phase_root / "human_calibration_ledger.md").write_text(render_ledger_markdown(ledger), encoding="utf-8")
    (phase_root / "scorer_disagreement_log.md").write_text(render_disagreement_log(ledger), encoding="utf-8")
    return {
        "imported": True,
        "review_id": review_id,
        "completed_human_review_count": ledger["completed_human_review_count"],
        "human_calibration_minimum_met": _minimum_human_calibration_met(records),
    }


def validate_human_record(record: object) -> None:
    if not isinstance(record, dict):
        raise ValueError("record must be a JSON object")
    required = {
        "review_id",
        "case_id",
        "sample_type",
        "scorer_passed",
        "scorer_soft_score",
        "scorer_hard_failures",
        "human_launch_decision",
        "human_quality_decision",
        "agreement",
        "rubric_action",
    }
    missing = sorted(key for key in required if key not in record)
    if missing:
        raise ValueError(f"missing required fields: {missing}")
    if not is_completed_human_record(record):
        raise ValueError("record does not satisfy Phase 11 completed human review fields")
    if record.get("rubric_action") not in ALLOWED_RUBRIC_ACTIONS:
        raise ValueError(f"rubric_action must be one of {sorted(ALLOWED_RUBRIC_ACTIONS)}")
    if record.get("rubric_action") in {"adjust", "add_check"} and not record.get("proposed_rule_change"):
        raise ValueError("proposed_rule_change is required for adjust/add_check")
    if record.get("agreement") is False and not record.get("disagreement_type"):
        raise ValueError("disagreement_type is required when agreement is false")
    if not isinstance(record.get("scorer_hard_failures"), list):
        raise ValueError("scorer_hard_failures must be a list")


def render_ledger_markdown(ledger: dict[str, object]) -> str:
    records = [record for record in ledger.get("records", []) if isinstance(record, dict)]
    observations = [item for item in ledger.get("agent_structured_observations", []) if isinstance(item, dict)]
    queue = [item for item in ledger.get("required_review_queue", []) if isinstance(item, dict)]
    counts = _record_counts(records)
    lines = [
        "# Phase 11 Human Calibration Ledger",
        "",
        f"Status: {ledger.get('status', 'unknown')}.",
        "",
        (
            f"Completed human reviews: {ledger.get('completed_human_review_count', 0)} "
            f"(golden={counts['golden_fixture']}, bad={counts['bad_fixture']}, "
            f"host_agent={counts['host_agent_sample']})."
        ),
        "",
        "## Completed Human Reviews",
        "",
    ]
    if records:
        lines.extend(
            [
                "| review_id | sample_type | agent | case_id | human_launch_decision | human_quality_decision | agreement | rubric_action |",
                "|---|---|---|---|---|---|---|---|",
            ]
        )
        for record in records:
            lines.append(
                "| {review_id} | {sample_type} | {agent} | {case_id} | {launch} | {quality} | {agreement} | {rubric_action} |".format(
                    review_id=record.get("review_id", ""),
                    sample_type=record.get("sample_type", ""),
                    agent=record.get("agent", "n/a"),
                    case_id=record.get("case_id", ""),
                    launch=record.get("human_launch_decision", ""),
                    quality=record.get("human_quality_decision", ""),
                    agreement=record.get("agreement", ""),
                    rubric_action=record.get("rubric_action", ""),
                )
            )
    else:
        lines.append("None.")
    lines.extend(["", "## Agent-Structured Observations", ""])
    if observations:
        lines.extend(
            [
                "| review_id | sample_type | agent | case_id | scorer_passed | soft_score | metadata_decision | human_review |",
                "|---|---|---|---|---|---:|---|---|",
            ]
        )
        for item in observations:
            lines.append(
                "| {review_id} | {sample_type} | {agent} | {case_id} | {passed} | {score} | {metadata} | pending |".format(
                    review_id=item.get("review_id", ""),
                    sample_type=item.get("sample_type", ""),
                    agent=item.get("agent", ""),
                    case_id=item.get("case_id", ""),
                    passed=item.get("scorer_passed", ""),
                    score=item.get("scorer_soft_score", ""),
                    metadata=item.get("metadata_quality_decision") or "pending",
                )
            )
    else:
        lines.append("None.")
    lines.extend(["", "## Required Human Review Queue", ""])
    if queue:
        lines.extend(["| sample_type | agent | case_id | path | status |", "|---|---|---|---|---|"])
        for item in queue:
            lines.append(
                "| {sample_type} | {agent} | {case_id} | {path} | {status} |".format(
                    sample_type=item.get("sample_type", ""),
                    agent=item.get("agent", "n/a"),
                    case_id=item.get("case_id", ""),
                    path=item.get("path", ""),
                    status=item.get("human_review_status", ""),
                )
            )
    else:
        lines.append("None.")
    lines.extend(["", "## Blocking Gaps", ""])
    for gap in ledger.get("blocking_gaps", []):
        lines.append(f"- {gap}")
    if not ledger.get("blocking_gaps"):
        lines.append("None recorded in the ledger.")
    lines.append("")
    return "\n".join(lines)


def render_disagreement_log(ledger: dict[str, object]) -> str:
    records = [record for record in ledger.get("records", []) if isinstance(record, dict)]
    disagreements = [record for record in records if record.get("agreement") is False]
    lines = ["# Phase 11 Scorer Disagreement Log", ""]
    if not disagreements:
        lines.extend(
            [
                "No independent human-vs-scorer disagreements recorded.",
                "",
                "Rubric action: defer scorer changes until disagreement evidence exists.",
                "",
            ]
        )
        return "\n".join(lines)
    for record in disagreements:
        lines.extend(
            [
                f"## {record.get('review_id', record.get('case_id', '<unknown>'))}",
                "",
                f"- Case: {record.get('case_id')}",
                f"- Sample type: {record.get('sample_type')}",
                f"- Agent: {record.get('agent', 'n/a')}",
                f"- Human quality decision: {record.get('human_quality_decision')}",
                f"- Human launch decision: {record.get('human_launch_decision')}",
                f"- Disagreement type: {record.get('disagreement_type')}",
                f"- Rubric action: {record.get('rubric_action')}",
                f"- Proposed rule change: {record.get('proposed_rule_change') or 'none'}",
                f"- Notes: {record.get('human_notes', '')}",
                "",
            ]
        )
    return "\n".join(lines)


def _refresh_ledger_status(ledger: dict[str, object]) -> None:
    records = [record for record in ledger.get("records", []) if is_completed_human_record(record)]
    ledger["human_review_performed"] = bool(records)
    ledger["minimum_required_review_count"] = 5
    ledger["completed_human_review_count"] = len(records)
    if _minimum_human_calibration_met(records):
        ledger["status"] = "human_calibration_minimum_met"
        ledger["blocking_gaps"] = [
            gap
            for gap in ledger.get("blocking_gaps", [])
            if "human reviewer decisions" not in str(gap)
        ]
    else:
        ledger["status"] = "blocked_on_external_human_review"


def _minimum_human_calibration_met(records: list[object]) -> bool:
    completed = [record for record in records if is_completed_human_record(record)]
    counts = _record_counts(completed)
    return len(completed) >= 5 and counts["golden_fixture"] >= 2 and counts["bad_fixture"] >= 2 and counts["host_agent_sample"] >= 1


def _record_counts(records: list[object]) -> Counter[str]:
    return Counter(record.get("sample_type") for record in records if isinstance(record, dict))


def _load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


if __name__ == "__main__":
    raise SystemExit(main())
