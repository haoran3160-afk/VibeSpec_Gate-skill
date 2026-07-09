from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from vibespec_gate.core.loop_runner import _loop_relevant
from vibespec_gate.core.risk_model import finding_from_dict
from vibespec_gate.core.scan_runner import run_scan


BASE = Path("tests/evaluation_cases")


def _cases() -> list[Path]:
    return sorted(path.parent for path in BASE.rglob("expected.json") if "review" not in path.parts)


def test_evaluation_cases_cover_phase2_minimum():
    assert len(_cases()) >= 20


def test_evaluation_cases(tmp_path):
    for case in _cases():
        expected = json.loads((case / "expected.json").read_text(encoding="utf-8"))
        output = tmp_path / case.relative_to(BASE)
        summary = run_scan(str(case), str(output), include_adapters=False)
        findings = json.loads((output / "findings.json").read_text(encoding="utf-8"))
        active = [item for item in findings if not item.get("suppressed")]
        suppressed = [item for item in findings if item.get("suppressed")]
        active_titles = [item["title"] for item in active]
        all_active_text = json.dumps(active, ensure_ascii=False)
        codex_tasks = (output / "codex_fix_tasks.md").read_text(encoding="utf-8")

        assert summary["profile"]["project_type"] == expected["expected_profile"], case
        assert summary["decision"] == expected["expected_gate"], case
        assert "profile_score" in summary["profile"], case
        assert "profile_evidence" in summary["profile"], case
        for title in expected.get("must_find", []):
            assert title in all_active_text, case
        for title in expected.get("must_not_find", []):
            assert title not in all_active_text, case
        for title in expected.get("must_suppress", []):
            assert any(title in item["title"] for item in suppressed), case
        for title, max_count in expected.get("max_title_count", {}).items():
            count = sum(1 for active_title in active_titles if title in active_title)
            assert count <= max_count, case
        for text in expected.get("codex_must_find", []):
            assert text in codex_tasks, case
        for text in expected.get("codex_must_not_find", []):
            assert text not in codex_tasks, case


def test_info_findings_are_not_loop_relevant():
    info = finding_from_dict({"id": "VSG-INFO", "title": "tool missing", "severity": "Info", "category": "Config"})
    assert not _loop_relevant(info)
