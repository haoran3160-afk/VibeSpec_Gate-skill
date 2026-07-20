import pytest

from vibespec_gate.core.coverage import REVIEW_SURFACES, EvidenceCoverage, SurfaceCoverage
from vibespec_gate.core.gate_decision import decide_gate
from vibespec_gate.core.risk_model import Finding


def test_gate_blocks_on_p0():
    summary = decide_gate([Finding(id="VSG-X", title="x", severity="P0", category="Secrets")])
    assert summary["decision"] == "BLOCK"


@pytest.mark.parametrize("status", ["insufficient", "partial", "truncated"])
def test_gate_never_passes_incomplete_coverage(status):
    summary = decide_gate([], coverage=_coverage(status))

    assert summary["decision"] == "REVIEW"
    assert summary["coverage_status"] == status


def test_gate_defaults_missing_coverage_to_insufficient_review():
    summary = decide_gate([])

    assert summary["decision"] == "REVIEW"
    assert summary["coverage_status"] == "insufficient"


def test_gate_allows_pass_only_with_complete_coverage():
    summary = decide_gate([], coverage=_coverage("complete"))

    assert summary["decision"] == "PASS"
    assert summary["coverage"]["coverage_status"] == "complete"
    assert len(summary["coverage"]["surfaces"]) == len(REVIEW_SURFACES)


def test_gate_keeps_confirmed_runtime_p0_blocking_when_coverage_is_truncated():
    finding = Finding(id="VSG-X", title="x", severity="P0", category="Secrets")

    summary = decide_gate([finding], coverage=_coverage("truncated"))

    assert summary["decision"] == "BLOCK"


@pytest.mark.parametrize("confidence", ["suspected", "manual_review"])
def test_gate_requires_review_for_unconfirmed_runtime_p0(confidence):
    finding = Finding(id="VSG-X", title="x", severity="P0", category="Secrets", confidence=confidence)

    summary = decide_gate([finding], coverage=_coverage("complete"))

    assert summary["decision"] == "REVIEW"


def test_gate_rejects_complete_coverage_with_duplicate_or_inconsistent_inventory():
    coverage = _coverage("complete")
    coverage.surfaces[-1] = coverage.surfaces[0]
    coverage.files_skipped = 1

    summary = decide_gate([], coverage=coverage)

    assert summary["decision"] == "REVIEW"


def _coverage(status: str) -> EvidenceCoverage:
    surface_status = {
        "complete": "reviewed",
        "partial": "missing",
        "insufficient": "missing",
        "truncated": "truncated",
    }[status]
    return EvidenceCoverage(
        coverage_status=status,
        surfaces=[
            SurfaceCoverage(
                surface=surface,
                status=surface_status,
                source_refs=["tests/fixture:1"] if surface_status == "reviewed" else [],
                reason="Test coverage state." if surface_status != "reviewed" else "",
            )
            for surface in REVIEW_SURFACES
        ],
        files_discovered=1,
        files_inspected=1 if status == "complete" else 0,
        files_skipped=0 if status == "complete" else 1,
    )
