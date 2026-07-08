from __future__ import annotations

from collections import Counter
from typing import Any

from .risk_model import Finding, ProjectProfile


REQUESTED_OUTPUTS = [
    "nontechnical_user_summary.md",
    "launch_risk_report.md",
    "security_review_findings.json",
    "agent_fix_plan.md",
    "retest_checklist.md",
]


def build_llm_review_packet(
    profile: ProjectProfile,
    findings: list[Finding],
    review_packets: list[dict[str, Any]],
    verdicts: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "project_profile": profile.to_dict(),
        "product_context": _product_context(profile, findings),
        "sensitive_assets": _sensitive_assets(profile, findings, review_packets),
        "attack_surfaces": _attack_surfaces(profile, findings, review_packets),
        "auth_and_data_flow": _auth_and_data_flow(findings, review_packets),
        "agent_tool_surfaces": _agent_tool_surfaces(profile, findings, review_packets),
        "evidence_files": _evidence_files(review_packets),
        "rule_findings": _rule_findings(review_packets, verdicts),
        "review_questions": _review_questions(profile, findings, review_packets),
        "requested_outputs": REQUESTED_OUTPUTS,
        "safety_boundaries": [
            "Use rule findings as evidence hints and baseline signals, not final truth.",
            "Do not provide exploit payloads, bypass steps, credential theft guidance, or destructive test plans.",
            "Do not auto-write suppression files or blindly edit real projects.",
            "Mask complete secrets in user-facing outputs.",
        ],
    }


def _product_context(profile: ProjectProfile, findings: list[Finding]) -> dict[str, Any]:
    categories = Counter(f.category for f in findings)
    severities = Counter(f.severity for f in findings)
    return {
        "project_type": profile.project_type,
        "technologies": profile.technologies,
        "launch_stage": profile.launch_stage,
        "risk_level": profile.risk_level,
        "data_risk": profile.data_risk,
        "finding_category_counts": dict(categories),
        "finding_severity_counts": dict(severities),
        "review_positioning": "LLM-native launch-risk review using deterministic findings as evidence hints.",
    }


def _sensitive_assets(
    profile: ProjectProfile, findings: list[Finding], review_packets: list[dict[str, Any]]
) -> list[dict[str, str]]:
    assets: list[dict[str, str]] = []
    for item in profile.data_risk:
        assets.append({"asset": item, "source": "project_profile", "reason": "Project intake identified sensitive data."})
    for finding in findings:
        combined = f"{finding.category} {finding.title} {finding.technical_reason}".lower()
        if "secret" in combined or "token" in combined or "api key" in combined or "database" in combined:
            assets.append({"asset": finding.title, "source": finding.id, "reason": finding.technical_reason})
    for packet in review_packets:
        text = f"{packet['finding']['title']} {packet['finding']['technical_reason']}".lower()
        if "service role" in text or "private" in text:
            assets.append(
                {
                    "asset": packet["finding"]["title"],
                    "source": packet["finding"]["id"],
                    "reason": "Review packet indicates high-impact credential or private data exposure.",
                }
            )
    return _dedupe_dicts(assets, "asset")


def _attack_surfaces(
    profile: ProjectProfile, findings: list[Finding], review_packets: list[dict[str, Any]]
) -> list[dict[str, str]]:
    surfaces: list[dict[str, str]] = []
    surface_terms = {
        "api": "API route or server handler",
        "auth": "Authentication or authorization boundary",
        "rls": "Database row-level security",
        "firebase": "Firebase rules",
        "cors": "Cross-origin boundary",
        "electron": "Electron desktop boundary",
        "mcp": "MCP/IPC protocol boundary",
        "ipc": "MCP/IPC protocol boundary",
        "llm": "LLM or Agent tool surface",
        "agent": "LLM or Agent tool surface",
        "upload": "File upload or storage surface",
        "secret": "Secret/config exposure surface",
    }
    for finding in findings:
        combined = f"{finding.category} {finding.title} {finding.technical_reason}".lower()
        for term, label in surface_terms.items():
            if term in combined:
                surfaces.append({"surface": label, "source": finding.id, "reason": finding.title})
    for packet in review_packets:
        context = packet.get("evidence_context", {})
        signals = " ".join(context.get("nearby_risk_signals", []) + context.get("nearby_security_signals", [])).lower()
        if signals:
            surfaces.append(
                {
                    "surface": "Code evidence surface",
                    "source": packet["finding"]["id"],
                    "reason": f"Nearby signals: {signals}",
                }
            )
    return _dedupe_dicts(surfaces, "surface", "source")


def _auth_and_data_flow(findings: list[Finding], review_packets: list[dict[str, Any]]) -> dict[str, Any]:
    relevant = []
    for finding in findings:
        combined = f"{finding.category} {finding.title} {finding.technical_reason}".lower()
        if any(word in combined for word in ("auth", "owner", "rls", "firebase", "data", "database", "api route")):
            relevant.append(
                {
                    "finding_id": finding.id,
                    "title": finding.title,
                    "affected_files": finding.affected_files,
                    "evidence_role": "baseline_hint_not_final_judgment",
                }
            )
    security_signals = sorted(
        {
            signal
            for packet in review_packets
            for signal in packet.get("evidence_context", {}).get("nearby_security_signals", [])
            if signal in {"auth", "session", "middleware", "allowlist", "validate", "schema", "safeparse"}
        }
    )
    return {
        "baseline_findings": relevant,
        "nearby_security_signals": security_signals,
        "missing_context_questions": [
            "Where is authentication enforced for mutating routes or user-data reads?",
            "Where are object ownership, RLS, Firebase rules, or tenant boundaries enforced?",
            "Which data stores contain user or business-sensitive records?",
        ],
    }


def _agent_tool_surfaces(
    profile: ProjectProfile, findings: list[Finding], review_packets: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    surfaces: list[dict[str, Any]] = []
    for packet in review_packets:
        finding = packet["finding"]
        combined = f"{finding['category']} {finding['title']} {finding['technical_reason']}".lower()
        snippet = packet.get("evidence_context", {}).get("snippet", "").lower()
        if any(word in combined + " " + snippet for word in ("llm", "agent", "tool_call", "call_tool", "mcp", "ipc", "electron", "writefile", "exec(")):
            surfaces.append(
                {
                    "finding_id": finding["id"],
                    "title": finding["title"],
                    "surface_type": _tool_surface_type(combined, snippet),
                    "affected_files": finding["affected_files"],
                    "evidence_role": "baseline_hint_not_final_judgment",
                }
            )
    return surfaces


def _evidence_files(review_packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    files = []
    for packet in review_packets:
        context = packet["evidence_context"]
        primary = context.get("primary_file") or ""
        if not primary:
            continue
        files.append(
            {
                "path": primary,
                "finding_id": packet["finding"]["id"],
                "snippet_start_line": context.get("snippet_start_line", 0),
                "snippet_end_line": context.get("snippet_end_line", 0),
                "redacted": True,
            }
        )
    return files


def _rule_findings(review_packets: list[dict[str, Any]], verdicts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings = []
    verdict_by_id = {verdict["finding_id"]: verdict for verdict in verdicts}
    for packet in review_packets:
        finding = packet["finding"]
        verdict = verdict_by_id.get(finding["id"], {})
        findings.append(
            {
                "finding_id": finding["id"],
                "fingerprint": finding["fingerprint"],
                "title": finding["title"],
                "severity": finding["severity"],
                "category": finding["category"],
                "source_type": finding["source_type"],
                "rubric": packet["rubric"],
                "baseline_verdict": verdict.get("verdict", ""),
                "baseline_action": verdict.get("recommended_action", ""),
                "evidence_role": "baseline_hint_not_final_judgment",
                "reason": verdict.get("reason", finding["technical_reason"]),
            }
        )
    return findings


def _review_questions(
    profile: ProjectProfile, findings: list[Finding], review_packets: list[dict[str, Any]]
) -> list[str]:
    questions = [
        "What launch-blocking risks are supported by the evidence?",
        "Which findings are likely false positives or downgrade candidates?",
        "Which files should an Agent inspect before preparing fixes?",
        "What should be retested after fixes?",
    ]
    categories = {finding.category.lower() for finding in findings}
    if any("secret" in category for category in categories):
        questions.append("Are any credentials real runtime secrets that require rotation?")
    if any("auth" in category or "data" in category for category in categories):
        questions.append("Can unauthenticated or wrong-user access reach user or business data?")
    if profile.project_type in {"AI Agent", "MCP / IPC Tool", "Desktop/Electron App"}:
        questions.append("Can LLM, MCP/IPC, Electron, or local tool surfaces perform file, shell, database, email, or payment actions without confirmation?")
    if review_packets:
        questions.append("What missing evidence would change the launch decision?")
    return questions


def _tool_surface_type(combined: str, snippet: str) -> str:
    text = combined + " " + snippet
    if "electron" in text:
        return "desktop_electron"
    if "mcp" in text or "ipc" in text:
        return "mcp_ipc"
    if "exec(" in text or "subprocess" in text or "shell" in text:
        return "shell_command"
    if "writefile" in text or "unlink" in text or "deletefile" in text:
        return "file_system"
    if "database" in text or "db." in text:
        return "database"
    return "llm_agent_tool"


def _dedupe_dicts(items: list[dict[str, str]], *keys: str) -> list[dict[str, str]]:
    seen = set()
    result = []
    for item in items:
        identity = tuple(item.get(key, "") for key in keys) if keys else tuple(sorted(item.items()))
        if identity in seen:
            continue
        seen.add(identity)
        result.append(item)
    return result
