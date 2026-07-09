from __future__ import annotations

from typing import Any

from .review_packets import looks_placeholder_or_example, packet_text, provider_secret_signal


FIX_NEXT_STEPS = {
    "confirmed": "prepare_fix_task",
    "likely_true": "confirm_and_prepare_fix",
}


def review_packet(packet: dict[str, Any]) -> dict[str, Any]:
    rubric = packet["rubric"]
    finding = packet["finding"]
    source_type = finding.get("source_type", "runtime")
    text = packet_text(packet)

    if source_type in {"generated", "vendor", "cache"}:
        return _verdict(
            packet,
            "should_downgrade",
            "medium",
            "Info",
            False,
            "downgrade",
            "Generated/vendor/cache findings should not block the gate.",
        )
    if source_type in {"docs", "test", "example"}:
        if rubric == "secret" and looks_placeholder_or_example(text):
            return _verdict(
                packet,
                "false_positive",
                "high",
                "Info",
                False,
                "suppress",
                "Secret-like evidence is in docs/tests/examples and appears to be placeholder or example material.",
            )
        return _verdict(
            packet,
            "should_downgrade",
            "medium",
            _downgraded_severity(finding),
            False,
            "downgrade",
            "Finding is not runtime source and should not directly block launch.",
        )

    if rubric == "secret":
        return _review_secret(packet)
    if rubric == "auth":
        return _review_auth(packet)
    if rubric == "desktop":
        return _review_desktop(packet)
    if rubric == "mcp":
        return _review_mcp(packet)
    if rubric == "llm":
        return _review_llm(packet)
    if rubric == "deployment":
        return _review_deployment(packet)
    if rubric == "dependency":
        return _review_dependency(packet)
    if rubric == "config":
        return _review_config(packet)
    return _verdict(
        packet,
        "needs_human_review",
        "low",
        finding["severity"],
        finding["gate_relevant"],
        "manual_review",
        "Generic finding lacks a specialized rubric match.",
        questions=["What runtime caller reaches this code?", "What local evidence proves the reported risk is exploitable?"],
    )


def _review_secret(packet: dict[str, Any]) -> dict[str, Any]:
    finding = packet["finding"]
    text = packet_text(packet)
    title = finding["title"].lower()
    if looks_placeholder_or_example(text):
        return _verdict(
            packet,
            "false_positive",
            "high",
            "Info",
            False,
            "suppress",
            "Secret-like value appears to be placeholder/example material.",
        )
    if provider_secret_signal(text, title):
        severity = "P0" if "private key" in title or "service role" in title else finding["severity"]
        return _verdict(
            packet,
            "confirmed",
            "high",
            severity,
            True,
            "fix",
            "Provider-shaped runtime secret evidence supports the finding.",
            verification_commands=["Rotate the exposed credential in the provider console.", "Run the app's secret scan again after removal."],
        )
    if any(word in title for word in ("token", "apikey", "api_key", "secret", "password")):
        return _verdict(
            packet,
            "should_downgrade",
            "medium",
            "P2",
            True,
            "downgrade",
            "Generic token/apiKey/secret variable evidence is not enough for confirmed P1.",
        )
    return _verdict(
        packet,
        "needs_human_review",
        "low",
        finding["severity"],
        finding["gate_relevant"],
        "manual_review",
        "Secret finding lacks enough evidence to confirm or suppress.",
        questions=["Is the value a real provider credential or only a local placeholder?", "Can the credential be used in production or CI?"],
    )


def _review_auth(packet: dict[str, Any]) -> dict[str, Any]:
    title = packet["finding"]["title"].lower()
    text = packet_text(packet)
    if any(word in title for word in ("token", "verification code", "otp")) and any(word in text for word in ("log", "authorization", "cookie", "jwt", "session")):
        return _verdict(
            packet,
            "likely_true",
            "high",
            "P0",
            True,
            "fix",
            "Auth token, session, or verification-code logging can expose account access material.",
            verification_commands=["Confirm logs omit raw OTPs, reset tokens, JWTs, cookies, authorization headers, and session ids."],
        )
    if "rate limiting" in title or "rate limit" in title:
        return _verdict(
            packet,
            "needs_human_review",
            "medium",
            "P1",
            True,
            "manual_review",
            "OTP or reset flow lacks visible throttling evidence and may permit repeated guessing or abuse.",
            questions=["Is rate limiting enforced in middleware, provider settings, or another service?", "What threshold and user-support behavior has the product owner approved?"],
            verification_commands=["Confirm repeated failed OTP or reset attempts hit a safe rate-limit path."],
        )
    if "reset token" in title and "expiry" in title:
        return _verdict(
            packet,
            "needs_human_review",
            "medium",
            "P1",
            True,
            "manual_review",
            "Password reset-token expiry or single-use evidence is missing and needs confirmation.",
            questions=["Where is reset-token expiry enforced?", "Can a reset token be reused after a successful reset?"],
            verification_commands=["Confirm expired and already-used reset tokens are rejected."],
        )
    if "enumerate accounts" in title:
        return _verdict(
            packet,
            "needs_human_review",
            "medium",
            "P2",
            True,
            "manual_review",
            "Public auth response may reveal whether an account exists.",
            questions=["Is account-existence disclosure an intentional product decision?", "Are reset/signup responses generic for public callers?"],
            verification_commands=["Confirm public reset/signup/login responses do not reveal account existence unless explicitly accepted."],
        )
    if "admin route" in title:
        return _verdict(
            packet,
            "needs_human_review",
            "medium",
            "P1",
            True,
            "manual_review",
            "Admin route lacks visible role or permission enforcement evidence.",
            questions=["Where is admin role or permission enforcement performed?", "Do non-admin users receive a safe denial?"],
            verification_commands=["Confirm non-admin users cannot reach the admin route."],
        )
    if any(
        word in text
        for word in (
            "ownerid",
            "owner_id",
            "userid ==",
            "user_id ==",
            "where user_id",
            "where owner_id",
            "where: { user_id",
            "where: { owner_id",
            "auth.uid()",
        )
    ):
        return _verdict(
            packet,
            "should_downgrade",
            "medium",
            "P2",
            True,
            "downgrade",
            "Ownership or user-scoped access check is present near the reported auth boundary.",
        )
    if any(word in text for word in ("middleware", "auth(", "getserversession", "requireauth", "session")):
        return _verdict(
            packet,
            "needs_human_review",
            "medium",
            "P1",
            True,
            "manual_review",
            "Auth evidence may exist in middleware or local guards and needs confirmation.",
            questions=[
                "Does route-level or global middleware enforce authentication before this handler?",
                "Does the guard also enforce object ownership, RLS, Firebase rules, or equivalent authorization?",
            ],
        )
    if any(word in text for word in ("post(", "put(", "patch(", "delete(", "export async function post", "mutation", "insert", "update")):
        return _verdict(
            packet,
            "likely_true",
            "medium",
            "P1",
            True,
            "fix",
            "Runtime mutating route or data access lacks nearby auth, ownership, RLS, or Firebase rule evidence.",
        )
    return _verdict(
        packet,
        "needs_human_review",
        "low",
        packet["finding"]["severity"],
        True,
        "manual_review",
        "Auth/data finding needs route and middleware context.",
        questions=[
            "Which HTTP route or RPC method reaches this code?",
            "Where is authentication enforced for that route?",
            "Where is ownership, RLS, Firebase rule, or object-level authorization enforced?",
        ],
    )


def _review_desktop(packet: dict[str, Any]) -> dict[str, Any]:
    title = packet["finding"]["title"].lower()
    text = packet_text(packet)
    if "showopendialog" in text and any(word in text for word in ("path.resolve", "startswith", "workspace", "allowlist", "user-selected")):
        return _verdict(
            packet,
            "should_downgrade",
            "high",
            "P2",
            True,
            "downgrade",
            "File path appears user-selected and constrained to a local workspace.",
        )
    if "nodeintegration" in title or "nodeintegration: true" in text:
        return _verdict(packet, "likely_true", "high", "P1", True, "fix", "Electron renderer has nodeIntegration enabled, weakening the renderer boundary.")
    if "contextisolation" in title or "contextisolation: false" in text:
        return _verdict(packet, "likely_true", "high", "P1", True, "fix", "Electron renderer has contextIsolation disabled, weakening the preload boundary.")
    if any(word in title for word in ("broad preload", "preload api")) or ("contextbridge.exposeinmainworld" in text and "writefile" in text):
        return _verdict(
            packet,
            "needs_human_review",
            "medium",
            "P1",
            True,
            "manual_review",
            "Preload exposes broad file or command capability; confirm renderer reachability and path boundaries.",
            questions=["Can untrusted renderer content call the exposed preload method?", "Does the preload enforce a workspace allowlist and operation-specific schema?"],
        )
    if "openexternal" in title:
        return _verdict(packet, "likely_true", "medium", "P1", True, "fix", "External URL opening needs scheme/domain validation evidence.")
    if ("file operation" in title or any(word in text for word in ("writefile", "unlink", "deletefile"))) and any(
        word in text for word in ("tool_call", "call_tool", "llm", "agent")
    ):
        return _verdict(
            packet,
            "likely_true",
            "medium",
            "P1",
            True,
            "fix",
            "File operation appears reachable from an LLM/tool path without a clear boundary.",
        )
    return _verdict(
        packet,
        "needs_human_review",
        "medium",
        packet["finding"]["severity"],
        True,
        "manual_review",
        "Desktop/Electron boundary requires context about main/preload/renderer and caller trust.",
        questions=["Which Electron process owns this code path?", "Can renderer, preload, IPC, or an agent tool invoke it with untrusted input?"],
    )


def _review_mcp(packet: dict[str, Any]) -> dict[str, Any]:
    title = packet["finding"]["title"].lower()
    text = packet_text(packet)
    has_schema = any(word in text for word in ("pydantic", "jsonschema", "zod", "schema", "validate", "safeparse"))
    has_allowlist = any(word in text for word in ("allowed_tools", "allowedtools", "allowlist", "if tool_name in", "match tool_name"))
    has_process_boundary = any(word in text for word in ("localhost", "127.0.0.1", "process owner", "same-user", "local-only"))
    risky_op = any(word in text for word in ("subprocess", "exec(", "writefile", "unlink", "delete", "open("))
    dynamic_dispatch = any(word in text for word in ("tools[tool_name]", "getattr(", "globals()[", "dispatch[tool_name]"))
    if risky_op:
        return _verdict(
            packet,
            "needs_human_review",
            "medium",
            "P1",
            True,
            "manual_review",
            "MCP/IPC command or file operation needs explicit schema, allowlist, and caller boundary confirmation.",
            questions=["Which clients can call this MCP/IPC method?", "Is every risky argument schema-validated and constrained before command/file execution?"],
        )
    if dynamic_dispatch and not has_allowlist:
        return _verdict(
            packet,
            "needs_human_review",
            "medium",
            "P1",
            True,
            "manual_review",
            "Dynamic MCP/IPC tool dispatch lacks an explicit allowlist boundary.",
            questions=["Can clients choose arbitrary tool names?", "Where is the tool allowlist enforced before dispatch?"],
        )
    if has_schema and has_allowlist and has_process_boundary:
        return _verdict(
            packet,
            "should_downgrade",
            "medium",
            "P2",
            True,
            "downgrade",
            "MCP/IPC code shows schema validation, explicit allowlist, and local process/user boundary signals.",
        )
    if has_schema and not has_allowlist:
        return _verdict(
            packet,
            "needs_human_review",
            "medium",
            "P1",
            True,
            "manual_review",
            "MCP/IPC code has schema validation but no explicit tool/client allowlist evidence.",
            questions=["Which tool names or clients are allowed?", "Is dispatch blocked before any command or file capability is reached?"],
        )
    if has_allowlist and not has_schema:
        return _verdict(
            packet,
            "needs_human_review",
            "medium",
            "P1",
            True,
            "manual_review",
            "MCP/IPC code has allowlist evidence but lacks argument schema validation evidence.",
            questions=["Are all inbound arguments schema-validated before dispatch?", "Can malformed payloads reach file, command, or tool operations?"],
        )
    if any(word in title for word in ("schema", "allowed-client", "allowlist", "execution boundary")) or not has_schema:
        return _verdict(
            packet,
            "needs_human_review",
            "medium",
            "P1",
            True,
            "manual_review",
            "MCP/IPC boundary evidence is missing or incomplete and needs protocol-context review.",
            questions=["Is there an input schema at the protocol boundary?", "Is tool/client selection constrained by an explicit allowlist?"],
        )
    return _verdict(
        packet,
        "needs_human_review",
        "low",
        packet["finding"]["severity"],
        True,
        "manual_review",
        "MCP/IPC finding needs client, message, and tool boundary context.",
    )


def _review_llm(packet: dict[str, Any]) -> dict[str, Any]:
    title = packet["finding"]["title"].lower()
    text = packet_text(packet)
    has_tool = any(word in text for word in ("tool_call", "call_tool", "tools:", "function_call", "writefile", "deletefile", "subprocess", "exec("))
    high_risk_tool = any(word in text for word in ("writefile", "deletefile", "subprocess", "exec(", "send_email", "charge", "payment", "database", "db."))
    has_confirmation = any(
        phrase in text
        for phrase in (
            "approval is required",
            "human approval is required",
            "requires approval",
            "requires user approval",
            "await requireapproval",
            "user confirmation",
            "confirm(",
            "await confirm",
            "allowlist",
            "audit",
            "rate limit",
        )
    )
    if "rate limit" in title or "cost" in title:
        return _verdict(packet, "should_downgrade", "medium", "P2", True, "downgrade", "Missing LLM cost/rate limit is usually P2, not P1.")
    if "system prompt" in title:
        return _verdict(packet, "likely_true", "high", "P1", True, "fix", "System prompt exposure in runtime code can expose internal instructions.")
    if not has_tool:
        return _verdict(packet, "should_downgrade", "medium", "P2", True, "downgrade", "Plain LLM chat without tool control should not be treated as excessive agency.")
    if high_risk_tool and not has_confirmation:
        return _verdict(packet, "likely_true", "high", "P1", True, "fix", "Autonomous LLM-controlled high-risk tool lacks explicit user approval.")
    if has_confirmation:
        return _verdict(
            packet,
            "needs_human_review",
            "medium",
            "P1",
            True,
            "manual_review",
            "High-risk LLM tool has boundary signals; confirm they cover the risky action before fixing.",
            questions=["Does user confirmation happen immediately before the tool call?", "Does the approval describe the exact file, command, database, email, or payment action?"],
        )
    return _verdict(packet, "likely_true", "medium", "P1", True, "fix", "LLM-controlled tool lacks nearby boundary evidence.")


def _review_deployment(packet: dict[str, Any]) -> dict[str, Any]:
    return _verdict(packet, "likely_true", "medium", packet["finding"]["severity"], True, "fix", "Deployment finding remains relevant unless platform configuration proves otherwise.")


def _review_dependency(packet: dict[str, Any]) -> dict[str, Any]:
    return _verdict(
        packet,
        "needs_human_review",
        "medium",
        packet["finding"]["severity"],
        True,
        "manual_review",
        "Dependency findings need package and lockfile context before prioritizing.",
        questions=["Which package and lockfile version are installed?", "Is the vulnerable API reachable in production code?"],
    )


def _review_config(packet: dict[str, Any]) -> dict[str, Any]:
    if "debug" in packet["finding"]["title"].lower():
        return _verdict(packet, "should_downgrade", "medium", "P2", True, "downgrade", "Debug/config findings usually need launch-environment confirmation.")
    return _verdict(
        packet,
        "needs_human_review",
        "low",
        packet["finding"]["severity"],
        True,
        "manual_review",
        "Config finding needs environment context.",
        questions=["Which environment loads this configuration?", "Is the setting active in production or only local development?"],
    )


def _verdict(
    packet: dict[str, Any],
    verdict: str,
    confidence: str,
    severity: str,
    gate_relevant: bool,
    action: str,
    reason: str,
    questions: list[str] | None = None,
    verification_commands: list[str] | None = None,
) -> dict[str, Any]:
    missing: list[str] = []
    human_questions: list[str] = questions or []
    if verdict == "needs_human_review":
        missing = ["caller trust boundary", "complete control evidence"]
        if not human_questions:
            human_questions = [
                "Can untrusted input or an LLM/MCP client reach this code?",
                "Is there validation, allowlist, middleware, or confirmation outside the snippet?",
            ]
    elif verdict in {"should_downgrade", "false_positive"}:
        human_questions = human_questions or ["Confirm local evidence before suppressing or downgrading this finding."]

    inspect_files = _inspect_files(packet)
    return {
        "finding_id": packet["finding"]["id"],
        "fingerprint": packet["finding"]["fingerprint"],
        "verdict": verdict,
        "confidence": confidence,
        "recommended_final_severity": severity,
        "gate_relevant": gate_relevant,
        "reason": reason,
        "missing_evidence": missing,
        "human_review_questions": human_questions,
        "recommended_action": action,
        "agent_next_step": _agent_next_step(verdict, action),
        "inspect_files": inspect_files,
        "prohibited_changes": _prohibited_changes(action),
        "verification_commands": verification_commands or _verification_commands(packet, action),
        "rubric": packet["rubric"],
        "reviewer": "rule-based",
        "safe_to_auto_suppress": False,
    }


def _agent_next_step(verdict: str, action: str) -> str:
    if action == "fix":
        return FIX_NEXT_STEPS.get(verdict, "confirm_and_prepare_fix")
    if verdict == "needs_human_review" or action == "manual_review":
        return "verify_before_fix"
    if verdict in {"false_positive", "should_downgrade"} or action in {"suppress", "downgrade"}:
        return "confirm_before_suppress_or_downgrade"
    return "verify_before_fix"


def _inspect_files(packet: dict[str, Any]) -> list[str]:
    finding = packet["finding"]
    context_file = packet["evidence_context"].get("primary_file", "")
    files = [context_file, *finding.get("affected_files", [])]
    return [item for index, item in enumerate(files) if item and item not in files[:index]]


def _prohibited_changes(action: str) -> list[str]:
    values = [
        "Do not blindly edit a real project without confirming the local evidence first.",
        "Do not auto-suppress findings; safe_to_auto_suppress is false.",
        "Do not call external LLMs or upload project code.",
    ]
    if action == "fix":
        values.append("Do not broaden permissions, remove validation, or add bypasses while fixing.")
    return values


def _verification_commands(packet: dict[str, Any], action: str) -> list[str]:
    if action == "fix":
        return [
            "Run the smallest local test that covers the inspected file.",
            "Rerun vibesec review for the same findings after preparing the fix.",
        ]
    if action in {"downgrade", "suppress"}:
        return ["Re-run review-validate on the output directory after any manual downgrade or suppression record is created."]
    return ["Inspect the listed files and collect the missing evidence before preparing a fix."]


def _downgraded_severity(finding: dict[str, Any]) -> str:
    return "P2" if finding.get("severity") in {"P0", "P1"} else finding.get("severity", "Info")
