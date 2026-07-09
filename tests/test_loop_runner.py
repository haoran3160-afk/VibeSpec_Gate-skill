from pathlib import Path

from vibespec_gate.core.loop_runner import run_loop
from vibespec_gate.core.scan_runner import run_scan


def test_loop_runner_writes_review(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    run_scan("tests/fixtures/vulnerable_next_supabase_app", str(first), include_adapters=False)
    summary = run_loop("tests/fixtures/vulnerable_next_supabase_app", str(first / "findings.json"), str(second))
    assert summary["decision"] == "BLOCK"
    text = (second / "loop_review.md").read_text(encoding="utf-8")
    assert "Loop 1" in text
    assert "安全复审" in text
