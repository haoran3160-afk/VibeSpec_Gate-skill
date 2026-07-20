from __future__ import annotations

import re
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
RUNTIME_SOURCE_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".py", ".mjs", ".cjs"}
AUTH_PATH_MARKERS = {
    "auth",
    "authentication",
    "authorization",
    "login",
    "middleware",
    "session",
    "signin",
    "signup",
}
DATA_PATH_MARKERS = {"database", "db", "firebase", "migrations", "prisma", "storage", "supabase"}
DEPLOYMENT_CONFIG_NAMES = {
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "fly.toml",
    "netlify.toml",
    "procfile",
    "render.yaml",
    "vercel.json",
    "wrangler.toml",
}
DEPLOYMENT_PATH_MARKERS = {"deploy", "deployment", "headers"}
DESKTOP_PATH_MARKERS = {"electron", "extension", "ipc", "preload", "renderer", "src-tauri", "vscode"}


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
        if any(not isinstance(ref, str) or not ref.strip() for ref in self.source_refs):
            raise ValueError(f"surface source_refs must be non-empty strings: {self.surface}")
        self.source_refs = [ref.strip() for ref in self.source_refs]
        if not isinstance(self.reason, str):
            raise ValueError(f"surface reason must be a string: {self.surface}")
        self.reason = self.reason.strip()
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
        return all(
            (
                item.status == "reviewed"
                and isinstance(item.source_refs, list)
                and bool(item.source_refs)
                and all(isinstance(ref, str) and bool(ref.strip()) for ref in item.source_refs)
            )
            or (item.status == "not_applicable" and isinstance(item.reason, str) and bool(item.reason.strip()))
            for item in by_surface.values()
        )

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
    coverage_status = value.get("coverage_status", "insufficient")
    files_discovered = value.get("files_discovered", 0)
    files_inspected = value.get("files_inspected", 0)
    files_skipped = value.get("files_skipped", 0)
    reason = value.get("reason", "")
    if (
        not isinstance(coverage_status, str)
        or any(not isinstance(count, int) or isinstance(count, bool) for count in (files_discovered, files_inspected, files_skipped))
        or not isinstance(reason, str)
    ):
        return insufficient_coverage("Coverage data was invalid or incomplete.")
    raw_surfaces = value.get("surfaces")
    if not isinstance(raw_surfaces, list):
        return insufficient_coverage("Coverage data was invalid or incomplete.")
    surfaces: list[SurfaceCoverage] = []
    for item in raw_surfaces:
        if not isinstance(item, dict):
            return insufficient_coverage("Coverage data was invalid or incomplete.")
        raw_source_refs = item.get("source_refs", [])
        surface = item.get("surface", "")
        status = item.get("status", "")
        surface_reason = item.get("reason", "")
        if (
            not isinstance(raw_source_refs, list)
            or any(not isinstance(ref, str) for ref in raw_source_refs)
            or not isinstance(surface, str)
            or not isinstance(status, str)
            or not isinstance(surface_reason, str)
        ):
            return insufficient_coverage("Coverage data was invalid or incomplete.")
        try:
            surfaces.append(
                SurfaceCoverage(
                    surface=surface,
                    status=status,
                    source_refs=raw_source_refs,
                    reason=surface_reason,
                )
            )
        except (TypeError, ValueError):
            return insufficient_coverage("Coverage data was invalid or incomplete.")
    if len({item.surface for item in surfaces}) != len(surfaces):
        return insufficient_coverage("Coverage data contained duplicate review surfaces.")
    try:
        return EvidenceCoverage(
            coverage_status=coverage_status,
            surfaces=surfaces,
            files_discovered=files_discovered,
            files_inspected=files_inspected,
            files_skipped=files_skipped,
            reason=reason,
        )
    except (TypeError, ValueError):
        return insufficient_coverage("Coverage data was invalid or incomplete.")


def project_inventory_coverage(
    *,
    rels: list[str],
    inspected_rels: list[str],
    scannable_rels: list[str],
    scannable_text_by_rel: dict[str, str],
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
            source_refs = _surface_source_refs(surface, scannable_rels, scannable_text_by_rel, project_type)
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


def _surface_source_refs(
    surface: str,
    scannable_rels: list[str],
    scannable_text_by_rel: dict[str, str],
    project_type: str,
) -> list[str]:
    runtime_refs = [ref for ref in scannable_rels if _is_runtime_source(ref)]
    if surface == "secrets":
        refs = list(scannable_rels)
    elif surface == "deployment":
        refs = [ref for ref in scannable_rels if _is_deployment_evidence(ref)]
    elif surface in {"auth", "authorization"}:
        refs = [
            ref
            for ref in scannable_rels
            if (
                _is_runtime_source(ref)
                and (_has_path_marker(ref, AUTH_PATH_MARKERS) or _has_auth_evidence(scannable_text_by_rel.get(ref, "")))
            )
            or _is_identity_policy_evidence(ref)
        ]
    elif surface == "data_rules":
        refs = [ref for ref in scannable_rels if _is_data_evidence(ref)]
    elif surface == "agent_tools":
        refs = runtime_refs
    elif surface == "desktop_ipc":
        if project_type == "MCP / IPC Tool":
            refs = runtime_refs
        else:
            refs = [
                ref
                for ref in runtime_refs
                if _has_path_marker(ref, DESKTOP_PATH_MARKERS)
                or (project_type == "Desktop/Electron App" and _path_name(ref).startswith("main."))
            ]
    else:
        refs = []
    return refs[:10]


def _is_runtime_source(ref: str) -> bool:
    return any(ref.lower().endswith(suffix) for suffix in RUNTIME_SOURCE_SUFFIXES)


def _is_deployment_evidence(ref: str) -> bool:
    lowered = ref.lower().replace("\\", "/")
    name = _path_name(lowered)
    return (
        _is_runtime_source(lowered)
        or name in DEPLOYMENT_CONFIG_NAMES
        or name.startswith(".env")
        or _has_path_marker(lowered, DEPLOYMENT_PATH_MARKERS)
    )


def _is_data_evidence(ref: str) -> bool:
    lowered = ref.lower().replace("\\", "/")
    return lowered.endswith((".sql", ".rules")) or _has_path_marker(lowered, DATA_PATH_MARKERS)


def _is_identity_policy_evidence(ref: str) -> bool:
    lowered = ref.lower().replace("\\", "/")
    return lowered.endswith((".sql", ".rules")) or _has_path_marker(lowered, DATA_PATH_MARKERS)


def _has_auth_evidence(text: str) -> bool:
    return bool(
        re.search(
            r"\b(?:auth|authenticate|authentication|authorization|authorize|current_?user|"
            r"get_?session|login|logout|require_?auth|session|signin|signup)\b",
            text,
        )
    )


def _has_path_marker(ref: str, markers: set[str]) -> bool:
    normalized = ref.lower().replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    stem_parts = [piece for part in parts for piece in part.replace("-", "_").replace(".", "_").split("_")]
    return bool(set(parts + stem_parts) & markers)


def _path_name(ref: str) -> str:
    return ref.replace("\\", "/").rsplit("/", 1)[-1].lower()


def _applicable_surfaces(project_type: str, technologies: list[str], data_risk: list[str]) -> set[str]:
    applicable = {"secrets", "deployment"}
    if project_type in {"Web App", "SaaS", "AI Agent", "LLM App"} or "auth" in data_risk:
        applicable.update({"auth", "authorization"})
    if (
        project_type == "SaaS"
        or any(item in {"Supabase", "Firebase"} for item in technologies)
        or any(item in {"database", "customer_data", "file_upload", "chat_history"} for item in data_risk)
    ):
        applicable.add("data_rules")
    if project_type in {"AI Agent", "LLM App", "MCP / IPC Tool"}:
        applicable.add("agent_tools")
    if project_type in {"Desktop/Electron App", "MCP / IPC Tool", "VS Code Extension"}:
        applicable.add("desktop_ipc")
    return applicable


def _not_applicable_reason(surface: str, project_type: str) -> str:
    return f"No {surface} surface was identified for project type {project_type}."
