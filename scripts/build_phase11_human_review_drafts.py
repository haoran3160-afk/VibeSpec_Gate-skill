from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DEFAULT_PHASE11_ROOT = ROOT / "test output" / "phase11_real_host_agent_calibration"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from vibespec_gate.core.llm_output_quality import score_llm_review_outputs  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) > 1:
        print("usage: py -3 scripts\\build_phase11_human_review_drafts.py [phase11_root]", file=sys.stderr)
        return 2
    phase_root = Path(args[0]) if args else DEFAULT_PHASE11_ROOT
    try:
        result = build_human_review_drafts(phase_root)
    except Exception as exc:  # noqa: BLE001 - CLI reports validation failures directly.
        print(f"FAIL build human review drafts: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_human_review_drafts(phase_root: Path) -> dict[str, object]:
    ledger = _load_json(phase_root / "human_calibration_ledger.json")
    queue = ledger.get("required_review_queue", [])
    if not isinstance(queue, list):
        raise ValueError("human_calibration_ledger.required_review_queue must be a list")
    drafts_root = phase_root / "human_review_drafts"
    drafts_root.mkdir(parents=True, exist_ok=True)
    records = []
    for item in queue:
        if not isinstance(item, dict):
            raise ValueError("required_review_queue entries must be objects")
        record = _draft_record(item)
        path = drafts_root / f"{record['review_id']}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        records.append({"review_id": record["review_id"], "path": str(path), "sample_type": record["sample_type"], "case_id": record["case_id"]})
    index = render_draft_index(records)
    (drafts_root / "README.md").write_text(index, encoding="utf-8")
    return {
        "schema_version": "1.0",
        "draft_count": len(records),
        "drafts_root": str(drafts_root),
        "drafts": records,
    }


def render_draft_index(records: list[dict[str, object]]) -> str:
    lines = [
        "# Phase 11 Human Review Drafts",
        "",
        "These records are not completed human calibration evidence. Fill the `human_*`, `agreement`, `disagreement_type`, and `rubric_action` fields, then import each completed record with `scripts/import_phase11_human_review.py`.",
        "",
        "| review_id | sample_type | case_id | draft |",
        "|---|---|---|---|",
    ]
    for record in records:
        lines.append(
            "| {review_id} | {sample_type} | {case_id} | {path} |".format(
                review_id=record["review_id"],
                sample_type=record["sample_type"],
                case_id=record["case_id"],
                path=record["path"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def _draft_record(item: dict[str, object]) -> dict[str, object]:
    sample_path = _resolve_path(item["path"])
    score = score_llm_review_outputs(sample_path)
    sample_type = str(item["sample_type"])
    case_id = str(item["case_id"])
    agent = item.get("agent")
    review_id = _review_id(sample_type, case_id, agent)
    return {
        "schema_version": "1.0",
        "review_id": review_id,
        "reviewed_at": None,
        "reviewer": "human_pending",
        "case_id": case_id,
        "sample_type": sample_type,
        "agent": agent,
        "sample_path": str(item["path"]),
        "scorer_passed": score["passed"],
        "scorer_soft_score": score["soft_score"],
        "scorer_hard_failures": score["hard_failures"],
        "human_launch_decision": None,
        "human_quality_decision": None,
        "agreement": None,
        "disagreement_type": None,
        "human_notes": "",
        "rubric_action": None,
        "proposed_rule_change": None,
    }


def _review_id(sample_type: str, case_id: str, agent: object) -> str:
    parts = ["phase11", sample_type, case_id]
    if agent:
        parts.append(str(agent))
    normalized = "-".join(_slug(part) for part in parts)
    return normalized


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _resolve_path(value: object) -> Path:
    path = Path(str(value))
    if path.is_absolute():
        return path
    return ROOT / path


def _load_json(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


if __name__ == "__main__":
    raise SystemExit(main())
