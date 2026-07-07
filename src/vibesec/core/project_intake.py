from __future__ import annotations

import json
import re
from pathlib import Path

from .risk_model import ProjectProfile
from .source_classifier import IGNORED_DIRS, should_ignore_path


def iter_project_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if should_ignore_path(path):
            continue
        if path.is_file():
            files.append(path)
    return sorted(files)


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def read_text(path: Path, max_chars: int = 200_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except OSError:
        return ""


def detect_profile(project_path: str, mode: str | None = None) -> ProjectProfile:
    root = Path(project_path).resolve()
    files = iter_project_files(root)
    names = {p.name for p in files}
    rels = [rel(p, root) for p in files]
    tech: set[str] = set()
    signals: list[str] = []
    data_risk: set[str] = set()
    profile_evidence: list[str] = []
    profile_scores: dict[str, int] = {}

    if "package.json" in names:
        node_tech, node_profile = _detect_node(root / "package.json")
        tech.update(node_tech)
        profile_scores.update(node_profile)
    if "requirements.txt" in names or "pyproject.toml" in names:
        tech.add("Python")
    if "next.config.js" in names or "next.config.mjs" in names or any(r.startswith("app/") for r in rels):
        tech.add("Next.js")
    if any(r.endswith(".tsx") or r.endswith(".jsx") for r in rels):
        tech.add("React")
    if any("supabase" in r.lower() for r in rels):
        tech.add("Supabase")
        data_risk.add("database")
    if any("firebase" in r.lower() or r.endswith("firestore.rules") for r in rels):
        tech.add("Firebase")
        data_risk.add("database")
    if "Dockerfile" in names or "docker-compose.yml" in names:
        tech.add("Docker")
    if "vercel.json" in names:
        tech.add("Vercel")

    readme_text = ""
    for candidate in ("README.md", "README.zh-CN.md", "package.json", "pyproject.toml"):
        if (root / candidate).exists():
            readme_text += "\n" + read_text(root / candidate, 50_000).lower()
    combined = "\n".join(read_text(p, 20_000).lower() for p in files[:200])
    keyword_map = {
        "stripe": "payment",
        "payment": "payment",
        "email": "email",
        "phone": "phone",
        "upload": "file_upload",
        "chat": "chat_history",
        "openai": "api_key",
        "anthropic": "api_key",
        "api key": "api_key",
        "customer": "customer_data",
        "admin": "admin",
        "login": "auth",
    }
    for needle, risk in keyword_map.items():
        if needle in combined:
            data_risk.add(risk)
            signals.append(f"keyword:{needle}")
    if re.search(r"\b(auth|authentication|authorization|session|login|logout|signin|signup)\b", combined):
        data_risk.add("auth")
        signals.append("keyword:auth")

    agent_score, agent_evidence = _score_agent(combined, readme_text, rels)
    profile_scores["agent"] = agent_score
    profile_evidence.extend(agent_evidence)

    if mode:
        project_type = _mode_to_project_type(mode)
        profile_evidence.append(f"mode override: {mode}")
    else:
        project_type = _infer_project_type(root, names, rels, combined, readme_text, data_risk, agent_score, profile_scores)
        profile_evidence.extend(_project_type_evidence(project_type, root, names, rels, combined, readme_text, agent_score))

    launch_stage = "public_launch" if data_risk & {"payment", "customer_data", "auth"} else "demo_or_internal"
    risk_level = _risk_level(project_type, data_risk)

    return ProjectProfile(
        path=str(root),
        project_type=project_type,
        technologies=sorted(tech) or ["Unknown"],
        data_risk=sorted(data_risk) or ["unknown_or_low"],
        launch_stage=launch_stage,
        risk_level=risk_level,
        signals=signals,
        profile_score=agent_score,
        profile_evidence=profile_evidence,
        profile_scores=profile_scores,
    )


def _detect_node(package_json: Path) -> tuple[set[str], dict[str, int]]:
    tech: set[str] = {"Node.js"}
    profile_scores: dict[str, int] = {}
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return tech, profile_scores
    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    for pkg, name in {
        "next": "Next.js",
        "react": "React",
        "express": "Express",
        "@supabase/supabase-js": "Supabase",
        "firebase": "Firebase",
        "openai": "OpenAI SDK",
        "@anthropic-ai/sdk": "Anthropic SDK",
    }.items():
        if pkg in deps:
            tech.add(name)
    if "electron" in deps:
        tech.add("Electron")
        profile_scores["desktop"] = profile_scores.get("desktop", 0) + 4
    if "@tauri-apps/api" in deps or "@tauri-apps/cli" in deps:
        tech.add("Tauri")
        profile_scores["desktop"] = profile_scores.get("desktop", 0) + 4
    if "vscode" in data.get("engines", {}) or "activationEvents" in data or "contributes" in data:
        tech.add("VS Code Extension")
        profile_scores["vscode_extension"] = profile_scores.get("vscode_extension", 0) + 5
    description = str(data.get("description", "")).lower()
    if "agent" in description:
        profile_scores["agent"] = profile_scores.get("agent", 0) + 3
    return tech, profile_scores


def _score_agent(combined: str, readme_text: str, rels: list[str]) -> tuple[int, list[str]]:
    score = 0
    evidence: list[str] = []
    runtime = combined
    if any(term in runtime for term in ("tool_call", "function calling", "tools:", "tools =")):
        score += 3
        evidence.append("agent signal +3: tool/function-calling markers")
    if any(term in runtime for term in ("system prompt", "system_message", "developer message", "tool policy")):
        score += 3
        evidence.append("agent signal +3: system prompt or tool policy")
    if any(term in runtime for term in ("subprocess", "exec(", "writefile", "deletefile", "shell", "sendemail")) and any(
        term in runtime for term in ("openai", "anthropic", "chat.completions", "responses.create", "tool_call", "agent")
    ):
        score += 3
        evidence.append("agent signal +3: LLM context with high-risk tool capability")
    if any(
        term in runtime
        for term in (
            'from "openai"',
            "from 'openai'",
            "import openai",
            "new openai",
            "openai(",
            "anthropic(",
            "chat.completions",
            "responses.create",
        )
    ):
        score += 1
        evidence.append("llm signal +1: LLM SDK/API usage")
    if any(term in runtime for term in ("openai_api_key", "anthropic_api_key")):
        score += 1
        evidence.append("llm signal +1: LLM API key variable")
    if "agent" in readme_text:
        score += 3
        evidence.append("agent signal +3: README/package explicitly mentions agent")
    if any("agent" in rel.lower() for rel in rels):
        score += 1
        evidence.append("agent signal +1: file path mentions agent")
    return score, evidence


def _infer_project_type(
    root: Path,
    names: set[str],
    rels: list[str],
    combined: str,
    readme_text: str,
    data_risk: set[str],
    agent_score: int,
    profile_scores: dict[str, int],
) -> str:
    if profile_scores.get("vscode_extension", 0) >= 5:
        return "VS Code Extension"
    if profile_scores.get("desktop", 0) >= 4 or any(rel.startswith("electron/") or rel.startswith("src-tauri/") for rel in rels):
        return "Desktop/Electron App"
    if "mcp" in root.name.lower() or "model context protocol" in readme_text or "mcp" in readme_text:
        return "MCP / IPC Tool"
    if agent_score >= 5:
        return "AI Agent"
    if agent_score >= 2:
        return "LLM App"
    if "pyproject.toml" in names and "package.json" not in names:
        return "CLI / Local Tool"
    if "stripe" in combined or "subscription" in combined or "payment" in data_risk:
        return "SaaS"
    if "auth" in data_risk or "database" in data_risk:
        return "Web App"
    if "package.json" in names or "index.html" in names:
        return "Static Site"
    return "Unknown"


def _mode_to_project_type(mode: str) -> str:
    return {
        "demo": "Static Site",
        "web-app": "Web App",
        "saas": "SaaS",
        "ai-agent": "AI Agent",
        "admin": "Web App",
        "llm-app": "LLM App",
        "desktop": "Desktop/Electron App",
        "vscode-extension": "VS Code Extension",
        "cli": "CLI / Local Tool",
        "mcp": "MCP / IPC Tool",
    }.get(mode.lower(), "Unknown")


def _project_type_evidence(
    project_type: str, root: Path, names: set[str], rels: list[str], combined: str, readme_text: str, agent_score: int
) -> list[str]:
    evidence = [f"selected project_type={project_type}", f"agent_score={agent_score}"]
    if project_type == "Desktop/Electron App":
        evidence.append("desktop evidence: Electron/Tauri dependency or directory")
    if project_type == "VS Code Extension":
        evidence.append("extension evidence: VS Code extension manifest fields")
    if project_type == "MCP / IPC Tool":
        evidence.append("mcp evidence: project name or README mentions MCP/IPC")
    if project_type == "Static Site":
        evidence.append("static evidence: package/index present without backend auth/database signals")
    return evidence


def _risk_level(project_type: str, data_risk: set[str]) -> str:
    if project_type == "AI Agent":
        return "L4"
    if project_type in {"LLM App", "MCP / IPC Tool"}:
        return "L3"
    if "payment" in data_risk or "customer_data" in data_risk:
        return "L3"
    if "auth" in data_risk or "database" in data_risk:
        return "L2"
    if project_type in {"Desktop/Electron App", "VS Code Extension", "CLI / Local Tool"}:
        return "L2"
    return "L1"
