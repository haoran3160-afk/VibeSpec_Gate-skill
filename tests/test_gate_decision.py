import pytest

from vibespec_gate.core.coverage import REVIEW_SURFACES, EvidenceCoverage, SurfaceCoverage, coverage_from_dict
from vibespec_gate.core.gate_decision import decide_gate
from vibespec_gate.core.risk_model import Finding, finding_from_dict


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


def test_gate_blocks_confirmed_config_p0():
    finding = Finding(id="VSG-X", title="x", severity="P0", category="Secrets", source_type="config")

    summary = decide_gate([finding], coverage=_coverage("complete"))

    assert summary["decision"] == "BLOCK"


def test_gate_reviews_p0_with_unknown_source_metadata():
    finding = Finding(id="VSG-X", title="x", severity="P0", category="Secrets", source_type="unknown")

    summary = decide_gate([finding], coverage=_coverage("complete"))

    assert summary["decision"] == "REVIEW"


def test_gate_reviews_finding_with_unknown_severity_metadata():
    finding = finding_from_dict({"id": "VSG-X", "title": "x", "severity": "Critical", "category": "Secrets"})

    summary = decide_gate([finding], coverage=_coverage("complete"))

    assert finding.severity == "Critical"
    assert summary["decision"] == "REVIEW"


def test_gate_reviews_loaded_finding_with_missing_severity_metadata():
    finding = finding_from_dict({"id": "VSG-X", "title": "x", "category": "Secrets"})

    summary = decide_gate([finding], coverage=_coverage("complete"))

    assert finding.severity == "unknown"
    assert summary["decision"] == "REVIEW"


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


def test_gate_rejects_blank_coverage_source_references():
    payload = {
        "coverage_status": "complete",
        "surfaces": [
            {"surface": surface, "status": "reviewed", "source_refs": [""], "reason": ""}
            for surface in REVIEW_SURFACES
        ],
        "files_discovered": 1,
        "files_inspected": 1,
        "files_skipped": 0,
    }

    summary = decide_gate([], coverage=coverage_from_dict(payload))

    assert summary["decision"] == "REVIEW"


def test_gate_rechecks_coverage_references_after_mutation():
    coverage = _coverage("complete")
    coverage.surfaces[0].source_refs = [""]

    assert decide_gate([], coverage=coverage)["decision"] == "REVIEW"


def test_gate_rejects_non_list_coverage_source_references():
    payload = _coverage("complete").to_dict()
    payload["surfaces"][0]["source_refs"] = "tests/fixture:1"

    assert decide_gate([], coverage=coverage_from_dict(payload))["decision"] == "REVIEW"


@pytest.mark.parametrize("invalid_ref", [None, 1, {"path": "tests/fixture:1"}])
def test_gate_rejects_non_string_coverage_source_references(invalid_ref):
    payload = _coverage("complete").to_dict()
    payload["surfaces"][0]["source_refs"] = [invalid_ref]

    assert decide_gate([], coverage=coverage_from_dict(payload))["decision"] == "REVIEW"


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
