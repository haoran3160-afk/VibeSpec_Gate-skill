from __future__ import annotations

from pathlib import Path

from vibesec.core.risk_model import Finding, ProjectProfile

from .base import BaseScanner, has_any, iter_text_files, next_id, read_lines, rel


MCP_SUFFIXES = {".py", ".js", ".ts", ".mjs", ".cjs"}
SCHEMA_MARKERS = ["pydantic", "jsonschema", "zod", "schema", "validate", "safeparse", "typeguard"]
CLIENT_BOUNDARY_MARKERS = ["allowed_client", "allowedclients", "origin", "peercred", "pid", "allowlist", "trusted"]
TOOL_ALLOWLIST_MARKERS = ["allowed_tools", "allowedtools", "tool_allowlist", "if tool_name in", "match tool_name"]
COMMAND_BOUNDARY_MARKERS = ["allowlist", "confirm", "approval", "path.resolve", "path.normalize", "startswith", "workspace"]
AUDIT_MARKERS = ["audit", "logger", "logging", "structured log", "tool_call_id"]


class McpIpcScanner(BaseScanner):
    name = "mcp_ipc_scanner"

    def scan(self, root: Path, profile: ProjectProfile) -> list[Finding]:
        if profile.project_type != "MCP / IPC Tool":
            return []
        findings: list[Finding] = []
        index = 1
        for path in iter_text_files(root):
            if path.suffix not in MCP_SUFFIXES:
                continue
            text = "\n".join(read_lines(path))
            lowered = text.lower()
            ipc_context = has_any(lowered, ["mcp", "ipc", "jsonrpc", "stdin", "stdout", "websocket", "socket", "pipe", "tool"])
            if not ipc_context:
                continue
            if has_any(lowered, ["json.loads", "message", "request", "params", "stdin", "onmessage"]) and not has_any(lowered, SCHEMA_MARKERS):
                findings.append(self._finding(root, path, index, "MCP/IPC inbound messages may lack schema validation", "P1", "suspected", "MCP/IPC message handlers should validate message shape and argument types before dispatching tools.", "Add schema/type validation for inbound messages and reject unknown fields or malformed arguments."))
                index += 1
            if has_any(lowered, ["socket", "pipe", "stdin", "server", "websocket"]) and not has_any(lowered, CLIENT_BOUNDARY_MARKERS):
                findings.append(self._finding(root, path, index, "MCP/IPC endpoint may lack allowed-client or process boundary checks", "P1", "suspected", "Local IPC can still be reached by unintended clients if process, origin, or permission boundaries are not checked.", "Document and enforce allowed clients, origins, process identity, or local permission boundaries."))
                index += 1
            if has_any(lowered, ["tool_name", "toolname", "name = message", "call_tool", "dispatch"]) and not has_any(lowered, TOOL_ALLOWLIST_MARKERS):
                findings.append(self._finding(root, path, index, "MCP/IPC tool dispatch may lack an explicit allowlist", "P1", "suspected", "Dynamic tool names from messages can expose unintended local capabilities.", "Dispatch only from an explicit tool allowlist and validate each tool's arguments."))
                index += 1
            if has_any(lowered, ["subprocess", "os.system", "exec(", "shell=true", "write_text", "unlink", "remove("]) and not has_any(lowered, COMMAND_BOUNDARY_MARKERS):
                findings.append(self._finding(root, path, index, "MCP/IPC command or file operation may lack execution boundary checks", "P1", "suspected", "Command and file operations reachable from protocol messages need allowlists, confirmation, and path constraints.", "Add command allowlists, path boundary checks, and confirmation for high-risk tool calls."))
                index += 1
            if has_any(lowered, ["socket", "namedpipe", "mkfifo", "tempfile", "temporarydirectory"]) and not has_any(lowered, ["chmod", "permission", "mode=", "secure"]):
                findings.append(self._finding(root, path, index, "MCP/IPC local endpoint permissions need manual review", "P2", "manual_review", "Local sockets, pipes, and temporary files need permissions that prevent unintended local users or processes from connecting.", "Verify file/socket permissions and document the local trust boundary."))
                index += 1
            if has_any(lowered, ["subprocess", "os.system", "exec(", "write_text", "unlink", "remove(", "call_tool"]) and not has_any(lowered, AUDIT_MARKERS):
                findings.append(self._finding(root, path, index, "MCP/IPC high-risk tool calls may lack audit logging", "P2", "manual_review", "High-risk local tool calls should leave enough audit trail to investigate misuse without logging secrets.", "Add minimal structured audit logging for tool name, caller/session, decision, and redacted outcome."))
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
            id=next_id("IPC", index),
            title=title,
            severity=severity,
            category="MCP/IPC",
            affected_files=[location],
            evidence=f"{location} contains MCP/IPC boundary markers for this check.",
            why_it_matters_for_beginner=reason,
            technical_reason=reason,
            recommended_fix=fix,
            verification_steps=["Rerun VibeSpec Gate and manually verify the MCP/IPC message and tool boundary."],
            false_positive_notes="A local helper script is not automatically remotely exploitable; confirm who can send messages before changing code.",
            references=["https://modelcontextprotocol.io/specification"],
            confidence=confidence,
        )
