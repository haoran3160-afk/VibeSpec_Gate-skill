from __future__ import annotations

from pathlib import Path

from vibesec.core.fix_prompt_builder import build_fix_prompt
from vibesec.core.risk_model import Finding, ProjectProfile

from .base import BaseScanner, has_any, iter_text_files, next_id, read_lines, rel


AUTH_MARKERS = ["getserversession", "auth()", "getuser()", "requireauth", "verifytoken", "currentuser", "request.auth"]
OWNER_MARKERS = ["owner_id", "user_id", "created_by", "tenant_id", "auth.uid()", "request.auth.uid"]


class AuthDataScanner(BaseScanner):
    name = "auth_data_scanner"

    def scan(self, root: Path, profile: ProjectProfile) -> list[Finding]:
        findings: list[Finding] = []
        index = 1
        for path in iter_text_files(root):
            text = "\n".join(read_lines(path))
            lowered = text.lower()
            rel_path = rel(path, root)
            if self._is_api_file(rel_path) and self._looks_mutating(lowered) and not has_any(lowered, AUTH_MARKERS):
                findings.append(self._missing_auth(root, path, index))
                index += 1
            if self._is_api_file(rel_path) and has_any(lowered, ["params.id", "query.id", ".eq('id'", '.eq("id"']) and not has_any(lowered, OWNER_MARKERS):
                findings.append(self._missing_owner_check(root, path, index))
                index += 1
            if path.suffix == ".sql" and "create table" in lowered and "enable row level security" not in lowered:
                findings.append(self._missing_rls(root, path, index))
                index += 1
            if path.name.endswith(".rules") or path.name == "firestore.rules":
                for line_no, line in enumerate(read_lines(path), start=1):
                    if "allow read, write" in line.lower() and "if true" in line.lower():
                        findings.append(self._open_firebase_rules(root, path, line_no, index))
                        index += 1
        return findings

    def _is_api_file(self, rel_path: str) -> bool:
        lowered = rel_path.lower()
        return any(part in lowered for part in ("/api/", "app/api/", "routes/", "controllers/"))

    def _looks_mutating(self, text: str) -> bool:
        return has_any(text, ["post(", "put(", "patch(", "delete(", "export async function post", "insert(", "update(", "delete("])

    def _missing_auth(self, root: Path, path: Path, index: int) -> Finding:
        location = rel(path, root)
        title = "API route may mutate data without server-side authentication"
        beginner = "如果后端接口不检查登录，别人可能绕过页面按钮，直接调用接口修改数据。"
        fix = "在服务端 API 中验证 session/user/token，并对未登录请求返回 401。"
        return Finding(
            id=next_id("AUTH", index),
            title=title,
            severity="P1",
            category="Auth",
            affected_files=[location],
            evidence=f"{location} looks like a mutating API route but lacks common auth markers.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Frontend-only authorization is not a security boundary; API routes must enforce authentication.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["添加未登录请求被拒绝的测试"]),
            verification_steps=["重新扫描确认 API 中出现服务端鉴权标记。", "添加集成测试覆盖未登录访问。"],
            false_positive_notes="如果鉴权在全局中间件完成，请在代码或文档中标明并添加测试。",
            references=["https://owasp.org/API-Security/editions/2023/en/0x00-header/"],
            confidence="suspected",
        )

    def _missing_owner_check(self, root: Path, path: Path, index: int) -> Finding:
        location = rel(path, root)
        title = "Possible IDOR/BOLA: id-based access without owner check"
        beginner = "接口按 id 查数据时，如果不确认数据属于当前用户，用户 A 可能看到或修改用户 B 的数据。"
        fix = "把查询限制到当前用户或租户，例如同时匹配 `id` 和 `user_id/owner_id/tenant_id`。"
        return Finding(
            id=next_id("AUTH", index),
            title=title,
            severity="P1",
            category="Data",
            affected_files=[location],
            evidence=f"{location} references id-based access without obvious owner markers.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Object-level authorization must be checked on every resource access.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["添加用户 A 不能访问用户 B 数据的测试"]),
            verification_steps=["确认查询同时约束资源 id 和当前用户/租户。"],
            false_positive_notes="复杂权限封装可能导致误报；请保留测试或注释说明。",
            references=["https://owasp.org/www-project-api-security/"],
            confidence="suspected",
        )

    def _missing_rls(self, root: Path, path: Path, index: int) -> Finding:
        location = rel(path, root)
        title = "Supabase/Postgres table migration may be missing RLS"
        beginner = "没有 RLS 或等价策略时，前端可访问的数据库表可能被读写过宽。"
        fix = "为公开 schema 表启用 RLS，并添加按用户或租户限制的 select/insert/update/delete policy。"
        return Finding(
            id=next_id("AUTH", index),
            title=title,
            severity="P1",
            category="Data",
            affected_files=[location],
            evidence=f"{location} creates a table but no RLS enable statement was found in the same file.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Supabase uses Postgres RLS policies to enforce row-level authorization for client-accessible data.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["添加 RLS policy 测试或 SQL 审查"]),
            verification_steps=["确认每个用户数据表启用 RLS。", "确认策略使用 auth.uid() 或租户条件。"],
            false_positive_notes="RLS 可能在其他迁移文件中启用；如果是这样，请在报告中标记人工确认。",
            references=["https://supabase.com/docs/guides/database/postgres/row-level-security"],
            confidence="suspected",
        )

    def _open_firebase_rules(self, root: Path, path: Path, line_no: int, index: int) -> Finding:
        location = rel(path, root, line_no)
        title = "Firebase rules allow broad public read/write"
        beginner = "这类规则等于告诉数据库：任何人都可以读写。公开上线前通常必须修。"
        fix = "把规则改成基于 request.auth 和资源归属的条件，并分别限制读、写、更新、删除。"
        return Finding(
            id=next_id("AUTH", index),
            title=title,
            severity="P0",
            category="Data",
            affected_files=[location],
            evidence=f"{location} contains `allow read, write: if true`.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Overly broad Firebase rules bypass intended application-layer authorization.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["用 Firebase emulator 或规则测试覆盖匿名访问"]),
            verification_steps=["确认规则不再对所有人开放读写。"],
            false_positive_notes="本地 demo 也应避免把开放规则误部署到生产。",
            references=["https://firebase.google.com/docs/rules"],
        )
