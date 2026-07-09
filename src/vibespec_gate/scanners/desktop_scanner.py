from __future__ import annotations

from pathlib import Path

from vibespec_gate.core.risk_model import Finding, ProjectProfile

from .base import BaseScanner, has_any, iter_text_files, next_id, read_lines, rel


DESKTOP_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
SCHEMA_MARKERS = ["zod", "joi", "yup", "schema", "validate", "validator", "safeparse"]
BOUNDARY_MARKERS = ["path.resolve", "path.normalize", "startswith", "startsWith", "workspace", "allowed", "allowlist"]
URL_VALIDATION_MARKERS = ["new url", "protocol", "hostname", "origin", "allowlist", "allowed"]


class DesktopScanner(BaseScanner):
    name = "desktop_scanner"

    def scan(self, root: Path, profile: ProjectProfile) -> list[Finding]:
        if profile.project_type != "Desktop/Electron App" and not any(
            tech in profile.technologies for tech in ("Electron", "Tauri")
        ):
            return []
        findings: list[Finding] = []
        index = 1
        for path in iter_text_files(root):
            if path.suffix not in DESKTOP_SUFFIXES:
                continue
            text = "\n".join(read_lines(path))
            lowered = text.lower()
            if "nodeintegration" in lowered and "true" in lowered:
                findings.append(self._finding(root, path, index, "Electron renderer enables nodeIntegration", "P1", "suspected", "Renderer access to Node.js APIs increases impact if untrusted content reaches the renderer.", "Set nodeIntegration to false unless this is a trusted internal window and document the exception."))
                index += 1
            if "contextisolation" in lowered and "false" in lowered:
                findings.append(self._finding(root, path, index, "Electron renderer disables contextIsolation", "P1", "suspected", "Disabling contextIsolation weakens the preload boundary between renderer code and privileged APIs.", "Enable contextIsolation and expose only narrow preload APIs through contextBridge."))
                index += 1
            if "contextbridge.exposeinmainworld" in lowered and has_any(lowered, ["readfile", "writefile", "delete", "copy", "shell", "ipcrenderer"]):
                findings.append(self._finding(root, path, index, "Electron preload may expose broad privileged APIs", "P1", "suspected", "A preload bridge that exposes file, shell, or raw IPC helpers can turn renderer input into privileged desktop actions.", "Expose narrow methods, validate arguments, and avoid passing raw IPC or filesystem primitives to the renderer."))
                index += 1
            if ("ipcmain.handle" in lowered or "ipcmain.on" in lowered) and not has_any(lowered, SCHEMA_MARKERS + ["channelallowlist", "allowedchannels"]):
                findings.append(self._finding(root, path, index, "Electron IPC handlers may lack schema validation or channel allowlist", "P1", "suspected", "Desktop IPC handlers are a trust boundary; unvalidated channels or arguments can reach privileged main-process code.", "Add explicit channel allowlists and validate each handler's arguments before filesystem, shell, or network actions."))
                index += 1
            if "shell.openexternal" in lowered and not has_any(lowered, URL_VALIDATION_MARKERS):
                findings.append(self._finding(root, path, index, "Electron shell.openExternal may open unvalidated URLs", "P1", "suspected", "Opening untrusted URLs from desktop code can expose users to unsafe schemes or unexpected external applications.", "Validate URL scheme and allowed hostnames before calling shell.openExternal."))
                index += 1
            if has_any(lowered, ["readfile", "writefile", "unlink", "rm(", "copyfile", "rename("]) and has_any(lowered, ["filepath", "file_path", "path"]) and not has_any(lowered, BOUNDARY_MARKERS):
                findings.append(self._finding(root, path, index, "Desktop file operation may lack workspace path boundary checks", "P1", "suspected", "File operations in desktop apps need path normalization and workspace boundary checks when paths can come from renderer, user, or tool input.", "Resolve and normalize paths, enforce an allowed workspace/root, and reject traversal before read/write/delete/copy operations."))
                index += 1
        return findings

    def _finding(
        self,
        root: Path,
        path: Path,
        index: int,
        title: str,
        severity: str,
        confidence: str,
        reason: str,
        fix: str,
    ) -> Finding:
        location = rel(path, root)
        return Finding(
            id=next_id("DESK", index),
            title=title,
            severity=severity,
            category="Desktop/Electron",
            affected_files=[location],
            evidence=f"{location} contains Electron/desktop boundary markers for this check.",
            why_it_matters_for_beginner=reason,
            technical_reason=reason,
            recommended_fix=fix,
            verification_steps=["Rerun VibeSpec Gate and manually verify the Electron main/preload/renderer boundary."],
            false_positive_notes="If this is test, generated, or strictly internal developer code, downgrade or suppress with evidence.",
            references=["https://www.electronjs.org/docs/latest/tutorial/security"],
            confidence=confidence,
        )
