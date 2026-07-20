from __future__ import annotations

import json

from .path_safety import require_disjoint_paths
from .project_intake import detect_profile
from .report_builder import load_findings
from .review_outputs import (
    agent_review_decision_items,
    agent_review_decisions_json,
    agent_review_decisions_markdown,
    human_queue_items,
    human_queue_markdown,
    select_findings,
    summary,
    summary_markdown,
    suppression_candidates,
)
from .review_packets import build_review_packet
from .review_llm_packet import build_llm_review_packet
from .review_rubrics import review_packet
from .review_schema import validate_review_output_dir


def run_review(
    findings_path: str,
    project_path: str,
    output_dir: str,
    max_snippet_lines: int = 80,
    include_p2: bool = False,
    offline: bool = True,
    reviewer_rule_based: bool = True,
) -> dict[str, object]:
    if not offline:
        raise ValueError("Phase 5 review is offline-only and never calls external services.")
    if not reviewer_rule_based:
        raise ValueError("Only the local rule-based reviewer is available.")

    root, output = require_disjoint_paths(
        project_path,
        output_dir,
        first_label="project",
        second_label="output",
    )
    findings, output = require_disjoint_paths(
        findings_path,
        output,
        first_label="findings input",
        second_label="output",
    )
    output.mkdir(parents=True, exist_ok=True)

    profile = detect_profile(str(root))
    loaded_findings = load_findings(findings)
    selected, skipped = select_findings(loaded_findings, include_p2)
    packets = [build_review_packet(root, profile, finding, max_snippet_lines=max_snippet_lines) for finding in selected]
    verdicts = [review_packet(packet) for packet in packets]
    queue = human_queue_items(packets, verdicts)
    candidates = suppression_candidates(packets, verdicts)
    decisions = agent_review_decision_items(packets, verdicts)
    data = summary(profile, loaded_findings, packets, verdicts, skipped, queue, candidates)
    decision_output = agent_review_decisions_json(data, decisions)
    llm_packet = build_llm_review_packet(profile, loaded_findings, packets, verdicts)

    (output / "review_packets.json").write_text(json.dumps(packets, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "llm_review_packet.json").write_text(json.dumps(llm_packet, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "ai_review.json").write_text(json.dumps(verdicts, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "human_review_queue.md").write_text(human_queue_markdown(profile, packets, verdicts), encoding="utf-8")
    (output / "agent_review_decisions.md").write_text(agent_review_decisions_markdown(profile, packets, verdicts), encoding="utf-8")
    (output / "agent_review_decisions.json").write_text(json.dumps(decision_output, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "suppression_candidates.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")

    (output / "ai_review_summary.md").write_text(summary_markdown(data), encoding="utf-8")
    validate_review_output_dir(output)
    return data
