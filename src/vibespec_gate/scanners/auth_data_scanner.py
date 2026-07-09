from __future__ import annotations

from pathlib import Path

from vibespec_gate.core.fix_prompt_builder import build_fix_prompt
from vibespec_gate.core.risk_model import Finding, ProjectProfile

from .base import BaseScanner, has_any, iter_text_files, next_id, read_lines, rel


AUTH_MARKERS = ["getserversession", "auth()", "getuser()", "requireauth", "verifytoken", "currentuser", "request.auth"]
OWNER_MARKERS = ["owner_id", "user_id", "created_by", "tenant_id", "auth.uid()", "request.auth.uid"]
RATE_LIMIT_MARKERS = ["ratelimit", "rate limit", "throttle", "limiter", "too many requests", "429"]
ABUSE_CONTROL_MARKERS = [*RATE_LIMIT_MARKERS, "captcha", "turnstile", "recaptcha", "hcaptcha", "invite only", "risk engine"]
TOKEN_WORDS = ["authorization", "cookie", "jwt", "session", "refresh token", "reset token", "otp", "verification code"]
EXPIRY_MARKERS = ["expires", "expires_at", "expiresat", "expiry", "ttl", "maxage", "max_age", "expiration"]
ADMIN_ROLE_MARKERS = ["role", "isadmin", "is_admin", "admin_only", "requireadmin", "require_admin", "permissions"]


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
            if self._is_auth_flow(rel_path, lowered) and self._handles_otp_or_reset(lowered) and not has_any(lowered, RATE_LIMIT_MARKERS):
                findings.append(self._missing_auth_rate_limit(root, path, index))
                index += 1
            if self._handles_reset_token(lowered) and not has_any(lowered, EXPIRY_MARKERS):
                findings.append(self._reset_token_no_expiry(root, path, index))
                index += 1
            if self._logs_sensitive_auth_value(lowered):
                findings.append(self._auth_token_logged(root, path, index))
                index += 1
            if self._is_auth_flow(rel_path, lowered) and self._has_enumerating_response(lowered):
                findings.append(self._account_enumeration(root, path, index))
                index += 1
            if self._is_auth_flow(rel_path, lowered) and self._is_high_abuse_public_flow(lowered) and not has_any(lowered, ABUSE_CONTROL_MARKERS):
                findings.append(self._missing_abuse_control(root, path, index))
                index += 1
            if self._is_admin_route(rel_path, lowered) and not has_any(lowered, ADMIN_ROLE_MARKERS):
                findings.append(self._weak_admin_auth(root, path, index))
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

    def _is_auth_flow(self, rel_path: str, text: str) -> bool:
        lowered = rel_path.lower()
        return self._is_api_file(rel_path) and has_any(
            f"{lowered}\n{text}",
            ["login", "signup", "sign-up", "register", "password", "reset", "otp", "magic", "verify", "verification"],
        )

    def _handles_otp_or_reset(self, text: str) -> bool:
        return has_any(text, ["otp", "one time", "verification code", "magic link", "reset token", "password reset"])

    def _handles_reset_token(self, text: str) -> bool:
        return has_any(text, ["reset token", "password reset", "verification token"]) and has_any(text, ["create", "insert", "find", "select"])

    def _logs_sensitive_auth_value(self, text: str) -> bool:
        return has_any(text, ["console.log", "logger.", "log.info", "log.debug", "print("]) and has_any(text, TOKEN_WORDS)

    def _has_enumerating_response(self, text: str) -> bool:
        return has_any(
            text,
            [
                "user not found",
                "email not found",
                "account not found",
                "no account",
                "email already exists",
                "account exists",
                "unknown email",
            ],
        )

    def _is_high_abuse_public_flow(self, text: str) -> bool:
        return has_any(text, ["signup", "register", "sendotp", "send otp", "password reset", "reset password", "magic link"])

    def _is_admin_route(self, rel_path: str, text: str) -> bool:
        return self._is_api_file(rel_path) and has_any(f"{rel_path}\n{text}", ["admin", "dashboard", "moderator"])

    def _missing_auth(self, root: Path, path: Path, index: int) -> Finding:
        location = rel(path, root)
        title = "API route may mutate data without server-side authentication"
        beginner = "If a backend API changes data without checking login state, someone may bypass the UI and call it directly."
        fix = "Verify the session, user, or token on the server before reading or mutating private data; reject unauthenticated requests."
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
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["Add a test that unauthenticated requests are rejected."]),
            verification_steps=["Confirm the API route has a server-side auth check.", "Add an integration test for unauthenticated access."],
            false_positive_notes="If authentication is enforced by global middleware, keep visible code or tests that prove this route is covered.",
            references=["https://owasp.org/API-Security/editions/2023/en/0x00-header/"],
            confidence="suspected",
        )

    def _missing_owner_check(self, root: Path, path: Path, index: int) -> Finding:
        location = rel(path, root)
        title = "Possible IDOR/BOLA: id-based access without owner check"
        beginner = "If an API reads by id without checking ownership, user A may read or change user B's data."
        fix = "Constrain object reads and writes by both the requested id and the authenticated owner, user, or tenant id."
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
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["Add a test that user A cannot access user B's object."]),
            verification_steps=["Confirm the query constrains resource id and authenticated owner or tenant."],
            false_positive_notes="A shared authorization helper can be valid, but the project should include evidence or tests for this route.",
            references=["https://owasp.org/www-project-api-security/"],
            confidence="suspected",
        )

    def _missing_auth_rate_limit(self, root: Path, path: Path, index: int) -> Finding:
        location = rel(path, root)
        title = "OTP or reset flow may lack rate limiting"
        beginner = "A public code or reset endpoint without throttling may let attackers keep trying until one code works."
        fix = "Add rate-limit or provider abuse-control checks to the named OTP, magic-link, or reset endpoint."
        return Finding(
            id=next_id("AUTH", index),
            title=title,
            severity="P1",
            category="Auth",
            affected_files=[location],
            evidence=f"{location} handles OTP or reset-token behavior without visible rate-limit evidence.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Public verification and recovery endpoints need throttling to reduce guessing and abuse.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["Verify repeated failed attempts return a safe rate-limit error."]),
            verification_steps=["Confirm repeated failed attempts are throttled.", "Confirm the error does not reveal secret code details."],
            false_positive_notes="Provider-side throttling may exist outside the repository; if so, mark this for human confirmation instead of PASS.",
            references=["https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html"],
            confidence="suspected",
        )

    def _reset_token_no_expiry(self, root: Path, path: Path, index: int) -> Finding:
        location = rel(path, root)
        title = "Password reset token may lack expiry enforcement"
        beginner = "A reset link or code that never expires can be reused later if it leaks."
        fix = "Store and enforce an expiry time for reset or verification tokens, and reject expired or already-used tokens."
        return Finding(
            id=next_id("AUTH", index),
            title=title,
            severity="P1",
            category="Auth",
            affected_files=[location],
            evidence=f"{location} references reset-token storage or lookup without visible expiry markers.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Reset and verification tokens should be short-lived and single-use.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["Verify expired and reused reset tokens are rejected."]),
            verification_steps=["Confirm expired reset tokens are rejected.", "Confirm a reset token cannot be reused after success."],
            false_positive_notes="Auth providers may enforce expiry outside the repo; missing local evidence should remain REVIEW unless a bug is confirmed.",
            references=["https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html"],
            confidence="suspected",
        )

    def _auth_token_logged(self, root: Path, path: Path, index: int) -> Finding:
        location = rel(path, root)
        title = "Authentication token or verification code may be logged"
        beginner = "If logs contain login codes, JWTs, cookies, or reset tokens, someone with log access may take over accounts."
        fix = "Remove raw auth token logging and keep only non-sensitive metadata needed for debugging."
        return Finding(
            id=next_id("AUTH", index),
            title=title,
            severity="P0",
            category="Auth",
            affected_files=[location],
            evidence=f"{location} appears to log an OTP, reset token, JWT, cookie, authorization header, or session value.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Authentication artifacts are bearer secrets and should not be written to application logs.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["Verify logs do not contain raw auth tokens or codes."]),
            verification_steps=["Confirm logs omit raw OTPs, reset tokens, JWTs, cookies, authorization headers, and session ids."],
            false_positive_notes="Structured logging can be safe if it logs only redacted metadata; verify the exact fields.",
            references=["https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html"],
        )

    def _account_enumeration(self, root: Path, path: Path, index: int) -> Finding:
        location = rel(path, root)
        title = "Public auth response may enumerate accounts"
        beginner = "Different login or reset messages can tell attackers whether an email or phone number exists."
        fix = "Use a safe generic response for public login, signup, and reset flows where account existence should stay private."
        return Finding(
            id=next_id("AUTH", index),
            title=title,
            severity="P2",
            category="Auth",
            affected_files=[location],
            evidence=f"{location} appears to return account-existence-specific messages from a public auth flow.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Account enumeration can support targeted takeover and privacy attacks.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["Verify reset/signup responses do not reveal account existence."]),
            verification_steps=["Confirm public reset/signup/login responses are generic for existing and non-existing accounts."],
            false_positive_notes="Some products intentionally reveal account status; require human confirmation before changing product behavior.",
            references=["https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html"],
            confidence="manual_review",
        )

    def _missing_abuse_control(self, root: Path, path: Path, index: int) -> Finding:
        location = rel(path, root)
        title = "Public auth flow may lack CAPTCHA or abuse-control evidence"
        beginner = "Open signup or reset endpoints can be abused at scale if there is no throttling, CAPTCHA, invite gate, or provider protection."
        fix = "Add or document an abuse-control layer such as rate limiting, provider-side protection, invite gating, or CAPTCHA after human choice."
        return Finding(
            id=next_id("AUTH", index),
            title=title,
            severity="P2",
            category="Auth",
            affected_files=[location],
            evidence=f"{location} looks like a high-abuse public auth endpoint without visible abuse-control evidence.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Public identity flows need automation controls, especially before production launch.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["Verify repeated public requests hit a safe abuse-control path."]),
            verification_steps=["Confirm a rate limit, invite gate, provider risk control, or CAPTCHA protects the endpoint."],
            false_positive_notes="CAPTCHA is not required when equivalent abuse controls are visible or provider-side controls are documented.",
            references=["https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html"],
            confidence="manual_review",
        )

    def _weak_admin_auth(self, root: Path, path: Path, index: int) -> Finding:
        location = rel(path, root)
        title = "Admin route may lack role enforcement"
        beginner = "Admin routes need more than normal login; otherwise regular users may reach privileged actions."
        fix = "Add an explicit role, permission, or admin guard before privileged data access or mutation."
        return Finding(
            id=next_id("AUTH", index),
            title=title,
            severity="P1",
            category="Auth",
            affected_files=[location],
            evidence=f"{location} looks like an admin API route without visible role or permission markers.",
            why_it_matters_for_beginner=beginner,
            technical_reason="Privileged routes require authorization checks in addition to authentication.",
            recommended_fix=fix,
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["Verify non-admin users are rejected."]),
            verification_steps=["Confirm non-admin users receive a safe denial.", "Confirm admin-only actions require role or permission evidence."],
            false_positive_notes="Provider-side role policies can be valid, but the route needs visible evidence or tests.",
            references=["https://owasp.org/www-project-access-control/"],
            confidence="suspected",
        )

    def _missing_rls(self, root: Path, path: Path, index: int) -> Finding:
        location = rel(path, root)
        title = "Supabase/Postgres table migration may be missing RLS"
        beginner = "If user data tables are reachable from the client without row-level policies, data access may be too broad."
        fix = "Enable RLS for client-accessible tables and add owner- or tenant-scoped select, insert, update, and delete policies."
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
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["Add an RLS policy test or SQL review."]),
            verification_steps=["Confirm each user-data table enables RLS.", "Confirm policies use auth.uid() or tenant-scoped conditions."],
            false_positive_notes="RLS may be enabled in another migration; if so, mark this for human confirmation.",
            references=["https://supabase.com/docs/guides/database/postgres/row-level-security"],
            confidence="suspected",
        )

    def _open_firebase_rules(self, root: Path, path: Path, line_no: int, index: int) -> Finding:
        location = rel(path, root, line_no)
        title = "Firebase rules allow broad public read/write"
        beginner = "This rule tells the database that anyone can read and write. It usually must be fixed before public launch."
        fix = "Replace broad rules with request.auth and resource ownership checks for each operation."
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
            codex_fix_prompt=build_fix_prompt(title, beginner, [location], fix, ["Use emulator or rules tests for anonymous access."]),
            verification_steps=["Confirm rules no longer allow public read/write for all users."],
            false_positive_notes="Even demo rules should not be deployed to production accidentally.",
            references=["https://firebase.google.com/docs/rules"],
        )
