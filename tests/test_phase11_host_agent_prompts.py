from __future__ import annotations

from scripts.build_phase11_host_agent_prompts import build_host_agent_prompts


def test_build_host_agent_prompts_creates_manual_collection_bundles(tmp_path):
    phase_root = tmp_path / "phase11"

    result = build_host_agent_prompts(phase_root, agents=("claude", "cursor"))

    prompts_root = phase_root / "host_agent_prompts"
    claude_prompt = (prompts_root / "claude_secret_runtime_block_prompt.md").read_text(encoding="utf-8")
    index = (prompts_root / "README.md").read_text(encoding="utf-8")
    assert result["prompt_count"] == 2
    assert "Do not call tools, provider APIs, repository scripts" in claude_prompt
    assert "repository_script_invoked_provider" in claude_prompt
    assert "llm_review_packet.json" in claude_prompt
    assert "expected_quality.json" in claude_prompt
    assert "not host-agent output samples" in index
