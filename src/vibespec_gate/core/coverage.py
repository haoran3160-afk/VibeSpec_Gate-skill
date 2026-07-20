from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


REVIEW_SURFACES = (
    "auth",
    "authorization",
    "secrets",
    "data_rules",
    "deployment",
    "agent_tools",
    "desktop_ipc",
)
COVERAGE_STATUSES = {"complete", "partial", "insufficient", "truncated"}
SURFACE_STATUSES = {"reviewed", "not_applicable", "missing", "truncated"}


@dataclass
class SurfaceCoverage:
    surface: str
    status: str
    source_refs: list[str] = field(default_factory=list)
    reason: str = ""

    def __post_init__(self) -> None:
        if self.surface not in REVIEW_SURFACES:
            raise ValueError(f"unknown review surface: {self.surface}")
        if self.status not in SURFACE_STATUSES:
            raise ValueError(f"unknown surface status: {self.status}")
        if self.status == "reviewed" and not self.source_refs:
            raise ValueError(f"reviewed surface requires source_refs: {self.surface}")
        if self.status != "reviewed" and not self.reason:
            raise ValueError(f"{self.status} surface requires a reason: {self.surface}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceCoverage:
    coverage_status: str
    surfaces: list[SurfaceCoverage] = field(default_factory=list)
    files_discovered: int = 0
    files_inspected: int = 0
    files_skipped: int = 0
    reason: str = ""

    def __post_init__(self) -> None:
        if self.coverage_status not in COVERAGE_STATUSES:
            raise ValueError(f"unknown coverage status: {self.coverage_status}")
        if min(self.files_discovered, self.files_inspected, self.files_skipped) < 0:
            raise ValueError("coverage file counts cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def allows_pass(self) -> bool:
        if self.coverage_status != "complete":
            return False
        if self.files_discovered == 0 or self.files_inspected != self.files_discovered or self.files_skipped != 0:
            return False
        by_surface = {item.surface: item for item in self.surfaces}
        if len(self.surfaces) != len(REVIEW_SURFACES) or set(by_surface) != set(REVIEW_SURFACES):
            return False
        return all(item.status in {"reviewed", "not_applicable"} for item in by_surface.values())

    def missing_evidence(self) -> list[str]:
        messages = [
            f"{item.surface}: {item.reason}"
            for item in self.surfaces
            if item.status in {"missing", "truncated"}
        ]
        present = {item.surface for item in self.surfaces}
        messages.extend(f"{surface}: coverage was not recorded" for surface in REVIEW_SURFACES if surface not in present)
        if not messages and not self.allows_pass():
            messages.append(self.reason or f"coverage status is {self.coverage_status}")
        return messages


def insufficient_coverage(reason: str = "Evidence coverage was not provided.") -> EvidenceCoverage:
    return EvidenceCoverage(
        coverage_status="insufficient",
        surfaces=[SurfaceCoverage(surface=surface, status="missing", reason=reason) for surface in REVIEW_SURFACES],
        reason=reason,
    )


def coverage_from_dict(value: Any) -> EvidenceCoverage:
    if not isinstance(value, dict):
        return insufficient_coverage()
    raw_surfaces = value.get("surfaces")
    if not isinstance(raw_surfaces, list):
        return insufficient_coverage("Coverage data was invalid or incomplete.")
    surfaces: list[SurfaceCoverage] = []
    for item in raw_surfaces:
        if not isinstance(item, dict):
            return insufficient_coverage("Coverage data was invalid or incomplete.")
        try:
            surfaces.append(
                SurfaceCoverage(
                    surface=str(item.get("surface", "")),
                    status=str(item.get("status", "")),
                    source_refs=[str(ref) for ref in item.get("source_refs", [])],
                    reason=str(item.get("reason", "")),
                )
            )
        except ValueError:
            return insufficient_coverage("Coverage data was invalid or incomplete.")
    if len({item.surface for item in surfaces}) != len(surfaces):
        return insufficient_coverage("Coverage data contained duplicate review surfaces.")
    try:
        return EvidenceCoverage(
            coverage_status=str(value.get("coverage_status", "insufficient")),
            surfaces=surfaces,
            files_discovered=int(value.get("files_discovered", 0)),
            files_inspected=int(value.get("files_inspected", 0)),
            files_skipped=int(value.get("files_skipped", 0)),
            reason=str(value.get("reason", "")),
        )
    except (TypeError, ValueError):
        return insufficient_coverage("Coverage data was invalid or incomplete.")


def project_inventory_coverage(
    *,
    rels: list[str],
    inspected_rels: list[str],
    scannable_rels: list[str],
    unsupported_source_rels: list[str],
    unreadable_count: int,
    project_type: str,
    technologies: list[str],
    data_risk: list[str],
) -> EvidenceCoverage:
    discovered = len(rels)
    inspected = len(inspected_rels) - unreadable_count - len(unsupported_source_rels)
    skipped = discovered - inspected
    if discovered == 0:
        return insufficient_coverage("No project files were available to review.")

    if discovered > len(inspected_rels):
        reason = f"Only the first {len(inspected_rels)} of {discovered} files were inspected for project context."
        return _incomplete_inventory_coverage("truncated", "truncated", reason, discovered, inspected, skipped)
    elif unreadable_count:
        reason = f"{unreadable_count} project file(s) could not be read."
        return _incomplete_inventory_coverage("partial", "missing", reason, discovered, inspected, skipped)

    if unsupported_source_rels:
        preview = ", ".join(unsupported_source_rels[:5])
        reason = f"Security-relevant source files use unsupported formats: {preview}."
        return _incomplete_inventory_coverage("partial", "missing", reason, discovered, inspected, skipped)

    if project_type == "Unknown":
        reason = "Project type and applicable review surfaces could not be determined."
        return EvidenceCoverage(
            coverage_status="insufficient",
            surfaces=[SurfaceCoverage(surface=surface, status="missing", reason=reason) for surface in REVIEW_SURFACES],
            files_discovered=discovered,
            files_inspected=max(0, inspected),
            files_skipped=max(0, skipped),
            reason=reason,
        )

    applicable = _applicable_surfaces(project_type, technologies, data_risk)
    surfaces: list[SurfaceCoverage] = []
    for surface in REVIEW_SURFACES:
        if surface not in applicable:
            surfaces.append(
                SurfaceCoverage(
                    surface=surface,
                    status="not_applicable",
                    reason=_not_applicable_reason(surface, project_type),
                )
            )
        else:
            source_refs = _surface_source_refs(surface, scannable_rels)
            if source_refs:
                surfaces.append(SurfaceCoverage(surface=surface, status="reviewed", source_refs=source_refs))
            else:
                surfaces.append(
                    SurfaceCoverage(
                        surface=surface,
                        status="missing",
                        reason=f"No scanner-supported evidence was available for the applicable {surface} surface.",
                    )
                )

    coverage_status = "partial" if any(item.status == "missing" for item in surfaces) else "complete"
    reason = "One or more applicable review surfaces lacked scanner-supported evidence." if coverage_status == "partial" else ""

    return EvidenceCoverage(
        coverage_status=coverage_status,
        surfaces=surfaces,
        files_discovered=discovered,
        files_inspected=max(0, inspected),
        files_skipped=max(0, skipped),
        reason=reason,
    )


def _incomplete_inventory_coverage(
    coverage_status: str,
    surface_status: str,
    reason: str,
    discovered: int,
    inspected: int,
    skipped: int,
) -> EvidenceCoverage:
    return EvidenceCoverage(
        coverage_status=coverage_status,
        surfaces=[SurfaceCoverage(surface=surface, status=surface_status, reason=reason) for surface in REVIEW_SURFACES],
        files_discovered=discovered,
        files_inspected=max(0, inspected),
        files_skipped=max(0, skipped),
        reason=reason,
    )


def _surface_source_refs(surface: str, scannable_rels: list[str]) -> list[str]:
    if surface in {"agent_tools", "desktop_ipc"}:
        supported = {".js", ".jsx", ".ts", ".tsx", ".py", ".mjs", ".cjs"}
        refs = [ref for ref in scannable_rels if any(ref.lower().endswith(suffix) for suffix in supported)]
    else:
        refs = list(scannable_rels)
    return refs[:10]


def _applicable_surfaces(project_type: str, technologies: list[str], data_risk: list[str]) -> set[str]:
    applicable = {"secrets", "deployment"}
    if project_type in {"Web App", "SaaS", "AI Agent", "LLM App"} or "auth" in data_risk:
        applicable.update({"auth", "authorization"})
    if project_type in {"Web App", "SaaS"} or any(item in {"Supabase", "Firebase"} for item in technologies):
        applicable.add("data_rules")
    if project_type in {"AI Agent", "LLM App", "MCP / IPC Tool"}:
        applicable.add("agent_tools")
    if project_type in {"Desktop/Electron App", "MCP / IPC Tool", "VS Code Extension"}:
        applicable.add("desktop_ipc")
    return applicable


def _not_applicable_reason(surface: str, project_type: str) -> str:
    return f"No {surface} surface was identified for project type {project_type}."
