from pathlib import Path

from vibespec_gate.core.project_intake import detect_profile


def test_detect_ai_agent_profile():
    profile = detect_profile(str(Path("tests/fixtures/vulnerable_ai_agent_app")), "ai-agent")
    assert profile.project_type == "AI Agent"
    assert "OpenAI SDK" in profile.technologies
