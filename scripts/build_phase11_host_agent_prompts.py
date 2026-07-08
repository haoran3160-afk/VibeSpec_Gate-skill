from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PHASE11_ROOT = ROOT / "test output" / "phase11_real_host_agent_calibration"
DEFAULT_AGENTS = ("claude", "cursor")
SHARED_CASE_ID = "secret_runtime_block"
PACKET_PATH = ROOT / "tests" / "evaluation_cases" / "llm_outputs" / SHARED_CASE_ID / "llm_review_packet.json"
EXPECTED_QUALITY_PATH = ROOT / "tests" / "evaluation_cases" / "llm_outputs" / SHARED_CASE_ID / "expected_quality.json"
CONTRACT_PATH = ROOT / "docs" / "usage" / "llm_review_contract.md"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) > 1:
        print("usage: py -3 scripts\\build_phase11_host_agent_prompts.py [phase11_root]", file=sys.stderr)
        return 2
    phase_root = Path(args[0]) if args else DEFAULT_PHASE11_ROOT
    result = build_host_agent_prompts(phase_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_host_agent_prompts(phase_root: Path, agents: tuple[str, ...] = DEFAULT_AGENTS) -> dict[str, object]:
    output_root = phase_root / "host_agent_prompts"
    output_root.mkdir(parents=True, exist_ok=True)
    packet_text = PACKET_PATH.read_text(encoding="utf-8")
    expected_quality_text = EXPECTED_QUALITY_PATH.read_text(encoding="utf-8")
    contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
    prompts = []
    for agent in agents:
        path = output_root / f"{agent}_{SHARED_CASE_ID}_prompt.md"
        path.write_text(
            render_prompt(agent, packet_text, expected_quality_text, contract_text),
            encoding="utf-8",
        )
        prompts.append({"agent": agent, "case_id": SHARED_CASE_ID, "path": str(path)})
    (output_root / "README.md").write_text(render_index(prompts), encoding="utf-8")
    return {
        "schema_version": "1.0",
        "prompt_count": len(prompts),
        "prompts_root": str(output_root),
        "prompts": prompts,
    }


def render_prompt(agent: str, packet_text: str, expected_quality_text: str, contract_text: str) -> str:
    destination = f"test output/phase11_real_host_agent_calibration/host_agent_samples/{agent}/{SHARED_CASE_ID}"
    return "\n".join(
        [
            f"# Phase 11 Host-Agent Prompt: {agent} / {SHARED_CASE_ID}",
            "",
            "You are producing a defensive VibeSec Gate LLM review sample for calibration.",
            "",
            "## Rules",
            "",
            "- Use the packet below as the only project evidence.",
            "- Follow the output contract below exactly.",
            "- Do not call tools, provider APIs, repository scripts, CLIs, browsers, or network services.",
            "- Do not edit the real reviewed project.",
            "- Do not write suppressions.",
            "- Preserve uncertainty and missing evidence.",
            "- Produce only the five requested output files and no extra commentary.",
            "",
            "## Required Local Save Path After Manual Collection",
            "",
            f"`{destination}`",
            "",
            "After manual collection, copy `llm_review_packet.json`, `expected_quality.json`, `sample_metadata.json`, and the five generated output files to that directory, then run:",
            "",
            "```powershell",
            f"py -3 scripts\\import_phase11_host_agent_sample.py \"{destination}\" \"test output\\phase11_real_host_agent_calibration\"",
            "py -3 scripts\\verify_phase11_calibration.py \"test output\\phase11_real_host_agent_calibration\"",
            "```",
            "",
            "## sample_metadata.json",
            "",
            "Set `repository_script_invoked_provider` to `false` because repository scripts must not invoke the host agent.",
            "",
            "```json",
            json.dumps(
                {
                    "schema_version": "1.0",
                    "agent": agent,
                    "case_id": SHARED_CASE_ID,
                    "source_packet": f"tests/evaluation_cases/llm_outputs/{SHARED_CASE_ID}/llm_review_packet.json",
                    "generated_by": "manual_host_agent_session",
                    "generated_at": "2026-07-08",
                    "prompt_contract": "docs/usage/llm_review_contract.md",
                    "human_review_status": "pending",
                    "human_quality_decision": None,
                    "scorer_human_agreement": None,
                    "raw_response_preserved": True,
                    "repository_script_invoked_provider": False,
                    "notes": "Manually collected outside repository scripts.",
                },
                indent=2,
            ),
            "```",
            "",
            "## llm_review_packet.json",
            "",
            "```json",
            packet_text,
            "```",
            "",
            "## expected_quality.json",
            "",
            "Use this file unchanged for scoring the collected sample.",
            "",
            "```json",
            expected_quality_text,
            "```",
            "",
            "## Output Contract",
            "",
            contract_text,
            "",
        ]
    )


def render_index(prompts: list[dict[str, object]]) -> str:
    lines = [
        "# Phase 11 Host-Agent Prompt Bundles",
        "",
        "These prompt bundles are manual collection inputs only. They are not host-agent output samples and must not be counted as calibration evidence.",
        "",
        "| agent | case_id | prompt |",
        "|---|---|---|",
    ]
    for prompt in prompts:
        lines.append(f"| {prompt['agent']} | {prompt['case_id']} | {prompt['path']} |")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
