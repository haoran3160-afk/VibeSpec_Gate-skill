from __future__ import annotations

from pathlib import Path

from vibespec_gate.core.fix_prompt_builder import build_fix_prompt
from vibespec_gate.core.risk_model import Finding, ProjectProfile

from .base import BaseScanner, has_any, iter_text_files, next_id, read_lines, rel


TOOL_RISK_MARKERS = ["shell", "exec(", "subprocess", "writefile", "deletefile", "filesystem", "database", "sendemail", "http.request"]
APPROVAL_MARKERS = ["human", "approval", "confirm", "allowlist", "rate limit", "ratelimit", "budget"]
LLM_CONTEXT_MARKERS = ["openai", "anthropic", "chat.completions", "responses.create", "agent", "tool_call", "system prompt"]
CODE_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".py", ".mjs", ".cjs"}


class LlmAgentScanner(BaseScanner):
    name = "llm_agent_scanner"

    def scan(self, root: Path, profile: ProjectProfile) -> list[Finding]:
        findings: list[Finding] = []
        index = 1
        for path in iter_text_files(root):
            if path.suffix not in CODE_SUFFIXES:
                continue
            text = "\n".join(read_lines(path))
            lowered = text.lower()
            has_llm_context = has_any(lowered, LLM_CONTEXT_MARKERS) or "agent" in path.as_posix().lower()
            if not has_llm_context:
                continue
            if has_any(lowered, ["system prompt", "system_message", "developer_message"]) and has_any(lowered, ["export", "client", "public"]):
                findings.append(self._system_prompt_exposure(root, path, index))
                index += 1
            if has_any(lowered, TOOL_RISK_MARKERS) and not has_any(lowered, APPROVAL_MARKERS):
                findings.append(self._excessive_agency(root, path, index, profile, lowered))
                index += 1
            if has_any(lowered, ["messages", "conversation", "prompt"]) and has_any(lowered, ["console.log", "logger.info", "logger.debug"]):
                findings.append(self._sensitive_prompt_logging(root, path, index))
                index += 1
            if has_any(lowered, ["openai", "anthropic", "chat.completions", "responses.create"]) and not has_any(lowered, ["rate limit", "ratelimit", "quota", "budget", "max_tokens"]):
                findings.append(self._missing_resource_limits(root, path, index))
                index += 1
        return findings

    def _system_prompt_exposure(self, root: Path, path: Path, index: int) -> Finding:
        location = rel(path, root)
        title = "Possible system prompt exposure"
        beginner = "系统提示词可能包含内部规则或工具说明，直接暴露会让用户更容易绕过约束。"
        fix = "把系统提示词留在服务端，前端只传必要的用户输入和展示数据。"
        return Finding(
            id=next_id("LLM", index),
            title=title,
            severity="P1",
            category="LLM",
            affected_files=[location],
            evidence=f"{location} contains system-prompt markers in potentially exposed code.",
            why_it_matters_for_beginner=beginner,
            technical_reason="LLM system instructions and tool policy should not be exposed to untrusted clients.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["确认前端 bundle 不包含 system prompt"]),
            verification_steps=["重新扫描前端目录。", "审查构建产物中是否包含内部提示词。"],
            false_positive_notes="文档示例可能误报；生产代码需要移到服务端。",
            references=["https://genai.owasp.org/llm-top-10/"],
            confidence="suspected",
        )

    def _excessive_agency(self, root: Path, path: Path, index: int, profile: ProjectProfile, text: str) -> Finding:
        location = rel(path, root)
        title = "Agent tools may have excessive authority without approval"
        beginner = "Agent 如果能写文件、调用外部 API 或改数据库，却没有确认步骤，可能被提示词诱导做危险操作。"
        fix = "为高风险工具增加 allowlist、权限隔离、人工确认、审计日志和调用次数限制。"
        explicit_tool_control = has_any(text, ["tool_call", "function_call", "tools:", "responses.create", "chat.completions"])
        local_context = profile.project_type in {"Desktop/Electron App", "MCP / IPC Tool", "CLI / Local Tool"}
        severity = "P1"
        confidence = "suspected"
        if local_context and not explicit_tool_control:
            if location.startswith("scripts/") or "/scripts/" in location:
                severity = "P2"
            else:
                severity = "P1"
            confidence = "manual_review"
        return Finding(
            id=next_id("LLM", index),
            title=title,
            severity=severity,
            category="LLM",
            affected_files=[location],
            evidence=f"{location} contains risky tool markers without obvious approval or limits.",
            why_it_matters_for_beginner=beginner,
            technical_reason="OWASP LLM excessive agency risks require least privilege and tool-call governance.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["添加高风险工具必须确认的测试"]),
            verification_steps=["确认所有写操作或外部调用都有权限边界和审计。"],
            false_positive_notes="如果权限控制在框架层完成，请补充文档和测试证据。",
            references=["https://genai.owasp.org/llm-top-10/"],
            confidence=confidence,
        )

    def _sensitive_prompt_logging(self, root: Path, path: Path, index: int) -> Finding:
        location = rel(path, root)
        title = "LLM prompts or conversations may be logged"
        beginner = "聊天内容可能包含隐私、密钥或内部数据，直接写日志会扩大泄露面。"
        fix = "默认不要记录完整对话；只记录脱敏摘要、请求 ID 和错误类别。"
        return Finding(
            id=next_id("LLM", index),
            title=title,
            severity="P2",
            category="Privacy",
            affected_files=[location],
            evidence=f"{location} appears to log prompts or conversation data.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Sensitive information disclosure is a core LLM application risk.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["添加日志脱敏测试"]),
            verification_steps=["重新扫描确认不再记录完整 prompt/messages。"],
            false_positive_notes="如果日志已脱敏，应在代码中明确脱敏函数并添加测试。",
            references=["https://genai.owasp.org/llm-top-10/"],
            confidence="suspected",
        )

    def _missing_resource_limits(self, root: Path, path: Path, index: int) -> Finding:
        location = rel(path, root)
        title = "LLM calls may lack cost or rate limits"
        beginner = "没有频率、token 或预算限制时，别人可能让你的模型账单暴涨。"
        fix = "增加 rate limit、max_tokens、每日预算或用户级额度，并记录异常调用。"
        return Finding(
            id=next_id("LLM", index),
            title=title,
            severity="P2",
            category="LLM",
            affected_files=[location],
            evidence=f"{location} uses LLM APIs without obvious resource limit markers.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Unbounded consumption is an OWASP LLM risk and a common production cost issue.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["添加超过额度时被拒绝的测试"]),
            verification_steps=["确认每个用户或 IP 有请求限制和 token 限制。"],
            false_positive_notes="限制可能在网关或平台层配置；请补充证据。",
            references=["https://genai.owasp.org/llm-top-10/"],
            confidence="suspected",
        )
