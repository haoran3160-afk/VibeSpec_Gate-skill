from pathlib import Path

from vibespec_gate.core.project_intake import detect_profile
from vibespec_gate.scanners.llm_agent_scanner import LlmAgentScanner


def test_llm_agent_scanner_detects_agent_risks():
    root = Path("tests/fixtures/vulnerable_ai_agent_app")
    findings = LlmAgentScanner().scan(root, detect_profile(str(root), "ai-agent"))
    titles = {f.title for f in findings}
    assert "Possible system prompt exposure" in titles
    assert "Agent tools may have excessive authority without approval" in titles
    assert "LLM prompts or conversations may be logged" in titles
    assert "LLM calls may lack cost or rate limits" in titles
