from __future__ import annotations

import json
import shutil
from pathlib import Path

from scripts.build_phase11_human_review_drafts import build_human_review_drafts


def test_build_human_review_drafts_prefills_scorer_fields_without_completing_reviews(tmp_path):
    phase_root = tmp_path / "phase11"
    golden = phase_root / "fixtures" / "golden" / "secret_runtime_block"
    bad = phase_root / "fixtures" / "bad" / "secret_runtime_overoptimistic"
    host = phase_root / "host_agent_samples" / "codex" / "secret_runtime_block"
    shutil.copytree(Path("tests/evaluation_cases/llm_outputs/secret_runtime_block"), golden)
    shutil.copytree(Path("tests/evaluation_cases/llm_outputs_bad/secret_runtime_overoptimistic"), bad)
    shutil.copytree(Path("tests/evaluation_cases/llm_outputs/secret_runtime_block"), host)
    _write_ledger(phase_root, golden, bad, host)

    result = build_human_review_drafts(phase_root)

    drafts_root = phase_root / "human_review_drafts"
    host_draft = json.loads((drafts_root / "phase11-host-agent-sample-secret-runtime-block-codex.json").read_text(encoding="utf-8"))
    bad_draft = json.loads((drafts_root / "phase11-bad-fixture-secret-runtime-overoptimistic.json").read_text(encoding="utf-8"))
    index = (drafts_root / "README.md").read_text(encoding="utf-8")
    assert result["draft_count"] == 3
    assert host_draft["scorer_passed"] is True
    assert host_draft["human_quality_decision"] is None
    assert host_draft["agreement"] is None
    assert bad_draft["scorer_passed"] is False
    assert "not completed human calibration evidence" in index


def _write_ledger(phase_root: Path, golden: Path, bad: Path, host: Path) -> None:
    ledger = {
        "schema_version": "1.0",
        "required_review_queue": [
            {
                "case_id": "secret_runtime_block",
                "sample_type": "golden_fixture",
                "path": str(golden),
                "human_review_status": "pending",
            },
            {
                "case_id": "secret_runtime_overoptimistic",
                "sample_type": "bad_fixture",
                "path": str(bad),
                "human_review_status": "pending",
            },
            {
                "case_id": "secret_runtime_block",
                "sample_type": "host_agent_sample",
                "agent": "codex",
                "path": str(host),
                "human_review_status": "pending",
            },
        ],
    }
    phase_root.mkdir(parents=True, exist_ok=True)
    (phase_root / "human_calibration_ledger.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")
