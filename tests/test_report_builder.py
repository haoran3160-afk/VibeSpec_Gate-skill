from pathlib import Path

from vibespec_gate.core.scan_runner import run_scan


def test_scan_writes_reports(tmp_path):
    output = tmp_path / "scan"
    summary = run_scan("tests/fixtures/vulnerable_next_supabase_app", str(output), include_adapters=False)
    assert summary["decision"] == "BLOCK"
    for name in [
        "vibespec_gate_report_user.md",
        "vibespec_gate_report_developer.md",
        "codex_fix_tasks.md",
        "gate_summary.json",
        "findings.json",
        "loop_review.md",
    ]:
        assert (output / name).exists()
    assert "sk-test-1234567890abcdef1234567890abcdef" not in (output / "vibespec_gate_report_developer.md").read_text(encoding="utf-8")
