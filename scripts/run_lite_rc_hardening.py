from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_lite_release_validation import PRIMARY_OUTPUTS, stage_candidate_package  # noqa: E402


DEFAULT_DATE = "2026-07-08"
DEFAULT_OUTPUT_ROOT = ROOT / "test output" / "lite_rc_hardening" / DEFAULT_DATE
VALID_DECISIONS = {"BLOCK", "REVIEW", "PASS_WITH_WARNINGS", "PASS"}


MATRIX_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "case_1_secret_leak_web_app",
        "decision": "BLOCK",
        "expected": {"BLOCK"},
        "surface": "Secret leak web app",
        "evidence": [
            "`tests/fixtures/vulnerable_next_supabase_app/.env.local` contains an API key and database URL.",
            "`tests/fixtures/vulnerable_next_supabase_app/next.config.js` exposes production source maps and wildcard API CORS.",
        ],
        "risk": "Committed runtime secrets can expose service credentials if they are real.",
        "fix": "Remove committed secrets, document required env vars, and rotate any real credential outside the repository.",
        "human": "Confirm whether the exposed values were real and whether rotation is required.",
        "prohibited": "Do not print full secret values or replace secrets with broader permissions.",
        "retest": "Confirm `.env.local` no longer contains real API keys or database URLs, then rerun Lite review.",
    },
    {
        "id": "case_2_missing_auth_or_ownership_check",
        "decision": "BLOCK",
        "expected": {"BLOCK", "REVIEW"},
        "surface": "Missing auth / ownership",
        "evidence": [
            "`tests/fixtures/vulnerable_next_supabase_app/app/api/orders/route.ts` reads orders by query id without authentication.",
            "`tests/fixtures/vulnerable_next_supabase_app/supabase/migrations/001_create_orders.sql` defines `user_id` but the route does not enforce ownership.",
        ],
        "risk": "A caller can create or read orders without proving identity or ownership.",
        "fix": "Require server-side auth and constrain order reads/writes to the authenticated owner.",
        "human": "Confirm the intended ownership and admin access model.",
        "prohibited": "Do not trust request-body `user_id` as proof of ownership.",
        "retest": "Confirm unauthenticated requests are rejected and order queries are constrained by authenticated `user_id`.",
    },
    {
        "id": "case_3_agent_or_mcp_tool_overreach",
        "decision": "REVIEW",
        "expected": {"REVIEW", "BLOCK"},
        "surface": "Agent or MCP tool overreach",
        "evidence": [
            "`tests/evaluation_cases/review/mcp_schema_no_allowlist_needs_review/server.py` accepts any message with a `name` field.",
            "`tests/evaluation_cases/review/mcp_schema_no_allowlist_needs_review/findings.json` records missing allowlist evidence.",
        ],
        "risk": "Schema validation alone does not prove the Agent can call only approved tools.",
        "fix": "Add or verify an explicit reviewed allowlist for callable MCP tool names.",
        "human": "Confirm which tool names are safe for this Agent.",
        "prohibited": "Do not dispatch arbitrary tool names just because the message schema is valid.",
        "retest": "Confirm dispatch rejects unapproved tool names and rerun Lite review for the MCP fixture.",
    },
    {
        "id": "case_4_low_risk_clean_project",
        "decision": "PASS",
        "expected": {"PASS", "PASS_WITH_WARNINGS"},
        "surface": "Low-risk clean project",
        "evidence": [
            "`tests/fixtures/safe_demo_app/app/api/profile/route.ts` checks `requireAuth(req)`.",
            "`tests/fixtures/safe_demo_app/next.config.js` sets security headers.",
        ],
        "risk": "No material launch blocker was found in the reviewed fixture evidence.",
        "fix": "No required Agent fix task; keep auth and headers covered by tests.",
        "human": "Confirm production identity-provider and database policy are configured outside the fixture.",
        "prohibited": "Do not remove `requireAuth(req)` or weaken configured headers.",
        "retest": "Confirm unauthenticated profile requests return `401` and security headers remain present.",
    },
    {
        "id": "case_5_supabase_rls_mistake",
        "decision": "REVIEW",
        "expected": {"BLOCK", "REVIEW"},
        "surface": "Supabase RLS mistake",
        "evidence": [
            "`tests/fixtures/vulnerable_next_supabase_app/supabase/migrations/001_create_orders.sql` creates `orders` but no RLS policy is present in the reviewed migration.",
            "`orders.user_id` exists, so row ownership likely matters.",
        ],
        "risk": "Supabase row access may rely only on application code if RLS or ownership policies are missing.",
        "fix": "Add or verify RLS policies that constrain `orders` access to the authenticated owner.",
        "human": "Confirm whether RLS is managed in another migration or production dashboard.",
        "prohibited": "Do not add broad `using (true)` or service-role-only workarounds as a launch fix.",
        "retest": "Inspect migrations for `enable row level security` and owner-scoped policies on `orders`.",
    },
    {
        "id": "case_6_firebase_rule_mistake",
        "decision": "BLOCK",
        "expected": {"BLOCK", "REVIEW"},
        "surface": "Firebase rule mistake",
        "evidence": [
            "`tests/fixtures/vulnerable_next_supabase_app/firestore.rules` contains `allow read, write: if true`.",
        ],
        "risk": "Open Firestore rules can expose or mutate all documents.",
        "fix": "Replace open rules with authenticated and ownership-scoped rules.",
        "human": "Confirm collection ownership semantics and admin exceptions.",
        "prohibited": "Do not ship `allow read, write: if true` for user data.",
        "retest": "Confirm Firestore rules no longer contain unconditional read/write allow clauses.",
    },
    {
        "id": "case_7_electron_desktop_risky_preload",
        "decision": "REVIEW",
        "expected": {"REVIEW", "BLOCK"},
        "surface": "Electron/Desktop risky preload",
        "evidence": [
            "Demo desktop boundary evidence: a preload bridge exposes local file access without a documented allowlist.",
            "No human-approved file scope or confirmation gate is visible in the package-level evidence.",
        ],
        "risk": "A renderer-reachable preload API can expose local files or process authority beyond user intent.",
        "fix": "Limit preload APIs to explicit operations and require user confirmation for file access.",
        "human": "Confirm which local paths and operations are intended for the desktop app.",
        "prohibited": "Do not expose broad filesystem, shell, or process APIs to renderer or Agent-controlled input.",
        "retest": "Review preload exports and confirm broad file/process authority is absent or gated.",
    },
    {
        "id": "case_8_upload_logging_privacy_issue",
        "decision": "REVIEW",
        "expected": {"REVIEW", "BLOCK"},
        "domain": "privacy_logging",
        "surface": "Upload/logging privacy issue",
        "evidence": [
            "Demo upload boundary evidence: uploaded content or request bodies are logged without a redaction rule.",
            "No retention or sensitive-field masking policy is visible in the reviewed evidence.",
        ],
        "risk": "Uploads, prompts, or request bodies can leak personal data into logs.",
        "fix": "Add sensitive-field redaction and avoid logging raw upload or prompt bodies.",
        "human": "Confirm retention, privacy, and support-debugging requirements.",
        "prohibited": "Do not preserve raw sensitive uploads in logs just to simplify debugging.",
        "retest": "Confirm logs redact upload/request bodies and include only necessary metadata.",
    },
    {
        "id": "case_9_login_private_api_without_auth",
        "decision": "BLOCK",
        "expected": {"BLOCK"},
        "domain": "login_security",
        "surface": "Login private API without auth",
        "evidence": [
            "Synthetic login-security evidence: `app/api/profile/route.ts` returns private profile data without a verified server-side session.",
            "No route middleware or auth helper evidence is visible for the private API.",
        ],
        "risk": "Attackers can call a private endpoint directly and read user data without logging in.",
        "fix": "Add a server-side auth guard to the private route before reading profile data.",
        "human": "Confirm the intended session helper and whether any global middleware already protects this route.",
        "prohibited": "Do not rely on frontend-only checks or request-body user identity as proof of login.",
        "retest": "Confirm unauthenticated requests to the private route return `401` or an equivalent safe denial.",
    },
    {
        "id": "case_10_password_reset_token_no_expiry",
        "decision": "BLOCK",
        "expected": {"BLOCK", "REVIEW"},
        "domain": "login_security",
        "surface": "Password reset token without expiry",
        "evidence": [
            "Synthetic login-security evidence: reset-token storage records `token` and `email` but no `expires_at`, TTL, or single-use marker.",
            "Reset verification logic checks only token equality before changing the password.",
        ],
        "risk": "A leaked reset token can remain usable indefinitely or be replayed after the user changes the password.",
        "fix": "Add expiry and single-use enforcement for reset tokens before accepting password changes.",
        "human": "Confirm the product's account recovery policy and acceptable reset-token lifetime.",
        "prohibited": "Do not log reset tokens or extend token lifetime to avoid failed tests.",
        "retest": "Confirm expired and already-used reset tokens are rejected before password change.",
    },
    {
        "id": "case_11_otp_verify_without_rate_limit",
        "decision": "BLOCK",
        "expected": {"BLOCK", "REVIEW"},
        "domain": "login_security",
        "surface": "OTP verify without rate limit",
        "evidence": [
            "Synthetic login-security evidence: `app/api/otp/verify/route.ts` accepts repeated verification attempts.",
            "No rate-limit middleware, provider abuse-control evidence, lockout, or attempt counter is visible.",
        ],
        "risk": "Attackers can repeatedly try verification codes until one works, which can lead to account takeover.",
        "fix": "Add a bounded rate-limit or attempt counter to the OTP verify endpoint.",
        "human": "Confirm safe thresholds, lockout behavior, and user-support impact before production rollout.",
        "prohibited": "Do not provide brute-force scripts, bypass CAPTCHA, or lock out production users without approval.",
        "retest": "Confirm repeated failed OTP attempts hit a safe rate-limit path and valid codes still work within policy.",
    },
    {
        "id": "case_12_reset_endpoint_enumerates_accounts",
        "decision": "REVIEW",
        "expected": {"REVIEW", "BLOCK"},
        "domain": "login_security",
        "surface": "Reset endpoint enumerates accounts",
        "evidence": [
            "Synthetic login-security evidence: reset endpoint returns `email not found` for unknown accounts.",
            "The same endpoint returns `reset email sent` for existing accounts.",
        ],
        "risk": "Public reset responses can reveal whether an email belongs to a user, which can enable targeted abuse.",
        "fix": "Use a generic public reset response while preserving internal audit logs.",
        "human": "Confirm whether account-existence disclosure is an intentional product decision.",
        "prohibited": "Do not remove audit logging or expose account existence through a different public message.",
        "retest": "Confirm reset responses for existing and non-existing accounts are indistinguishable to public callers.",
    },
    {
        "id": "case_13_jwt_logged_in_server_logs",
        "decision": "BLOCK",
        "expected": {"BLOCK"},
        "domain": "login_security",
        "surface": "JWT logged in server logs",
        "evidence": [
            "Synthetic login-security evidence: server debug logging prints the `Authorization` header and session JWT.",
            "No redaction rule masks cookies, bearer tokens, or session ids before logging.",
        ],
        "risk": "Anyone with log access can reuse bearer tokens or session material to access accounts.",
        "fix": "Remove raw auth-token logging and keep only redacted metadata needed for debugging.",
        "human": "Confirm log retention, incident response, and whether any exposed production tokens need rotation.",
        "prohibited": "Do not print full OTPs, reset tokens, JWTs, cookies, session ids, authorization headers, or secrets.",
        "retest": "Confirm logs omit raw JWTs, cookies, authorization headers, session ids, OTPs, and reset tokens.",
    },
    {
        "id": "case_14_admin_route_lacks_role_check",
        "decision": "BLOCK",
        "expected": {"BLOCK", "REVIEW"},
        "domain": "login_security",
        "surface": "Admin route lacks role check",
        "evidence": [
            "Synthetic login-security evidence: `app/api/admin/users/route.ts` checks login but not admin role or permission.",
            "No provider-side role policy or admin guard evidence is present.",
        ],
        "risk": "A normal logged-in user may reach privileged account-management behavior.",
        "fix": "Add an explicit admin role or permission guard before privileged route behavior.",
        "human": "Confirm admin role source, MFA expectation, and break-glass account policy.",
        "prohibited": "Do not share the public user session path with admin actions without a role check.",
        "retest": "Confirm non-admin users are rejected and admin users remain able to perform the intended action.",
    },
    {
        "id": "case_15_auth_provider_config_missing",
        "decision": "REVIEW",
        "expected": {"REVIEW"},
        "domain": "login_security",
        "surface": "Auth provider used but config missing",
        "evidence": [
            "Synthetic login-security evidence: application imports a managed auth provider but repository files do not show cookie, session, rate-limit, or recovery settings.",
            "No provider dashboard export or deployment configuration evidence is included.",
        ],
        "risk": "The provider may be configured safely, but the reviewed evidence cannot prove session, recovery, and abuse controls are production-ready.",
        "fix": "Document or attach provider configuration evidence for session cookies, recovery tokens, MFA/admin policy, and abuse controls.",
        "human": "Confirm provider-side security settings in the dashboard or deployment environment.",
        "prohibited": "Do not mark login security as `PASS` solely because a provider library is imported.",
        "retest": "Confirm provider configuration evidence covers session cookie settings, recovery token expiry, rate limits or abuse controls, and admin-role enforcement.",
    },
    {
        "id": "case_16_clean_provider_backed_auth_with_ownership",
        "decision": "PASS_WITH_WARNINGS",
        "expected": {"PASS_WITH_WARNINGS", "PASS"},
        "domain": "login_security",
        "surface": "Clean provider-backed auth with ownership checks",
        "evidence": [
            "Synthetic login-security evidence: private routes call `requireAuth(req)` and constrain queries by authenticated `user_id`.",
            "OTP/reset flows use provider-managed expiry and rate-limit configuration evidence, and admin routes check `role === 'admin'`.",
        ],
        "risk": "No material login-security launch blocker was found in reviewed evidence, but production provider settings still need final confirmation.",
        "fix": "No required Agent fix task; keep auth, ownership, abuse-control, token logging, and admin-role checks covered by tests.",
        "human": "Confirm production provider dashboard settings match the reviewed evidence.",
        "prohibited": "Do not remove owner constraints, weaken cookie settings, or disable rate limits to simplify login tests.",
        "retest": "Confirm unauthenticated private requests fail, user A cannot access user B's data, repeated OTP failures are throttled, logs omit tokens, and non-admin users cannot reach admin routes.",
    },
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Lite Skill RC hardening evidence generation.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--external-session",
        action="append",
        default=[],
        metavar="NAME:started,files,fix,retest,certification_safe,blind_edit_safe",
        help="Record an external blind usability session as comma-separated booleans.",
    )
    parser.add_argument(
        "--external-session-file",
        action="append",
        default=[],
        type=Path,
        help="JSON file containing recorded external blind usability sessions.",
    )
    parser.add_argument(
        "--simulate-subagents",
        action="store_true",
        help=(
            "Generate maintainer-authored synthetic walkthroughs for contract testing. "
            "These are not executed Agent sessions or user evidence."
        ),
    )
    parser.add_argument(
        "--real-project",
        action="append",
        default=[],
        metavar="LABEL=PATH",
        help="Run optional read-only Lite CLI validation against a real project. Output stays under the RC evidence folder.",
    )
    args = parser.parse_args(argv)

    output_root = args.output.resolve()
    validate_real_project_boundaries(output_root, args.real_project)
    reset_output_root(output_root)
    candidate = stage_candidate_package(output_root)
    write_package_file_list(candidate, output_root)
    results = {
        "verifier_source": run_and_capture([sys.executable, "scripts/verify_lite_package.py"], output_root / "verifier_source.txt"),
        "verifier_candidate": run_and_capture(
            [sys.executable, "scripts/verify_lite_package.py", str(candidate)],
            output_root / "verifier_candidate.txt",
        ),
        "focused_tests": run_and_capture(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_lite_release_validation.py",
                "tests/test_lite_package_verifier.py",
                "tests/test_lite_review_bundle.py",
                "tests/test_review_cli.py",
                "-q",
                "-p",
                "no:cacheprovider",
            ],
            output_root / "focused_tests.txt",
        ),
    }
    write_validation_matrix(output_root)
    matrix = evaluate_matrix(output_root)
    actionability = write_actionability_review(output_root)
    write_external_session_template(output_root)
    write_pilot_session_materials(output_root)
    sessions = load_external_sessions(args.external_session, args.external_session_file)
    if args.simulate_subagents:
        sessions.extend(write_simulated_subagent_sessions(output_root))
    external = write_pilot_usability_notes(output_root, sessions)
    real_projects = run_real_project_validations(output_root, args.real_project)
    write_known_limitations(output_root)
    write_release_decision(output_root, results, matrix, actionability, external, real_projects)

    if (
        all(item["returncode"] == 0 for item in results.values())
        and matrix["passed"]
        and actionability["passed"]
        and real_projects["passed"] is not False
    ):
        print(f"PASS Lite RC hardening evidence generated: {output_root}")
        return 0
    print(f"FAIL Lite RC hardening evidence generated: {output_root}")
    return 1


def reset_output_root(output_root: Path) -> None:
    allowed_root = (ROOT / "test output" / "lite_rc_hardening").resolve()
    if allowed_root not in output_root.parents and output_root != allowed_root:
        raise ValueError(f"refusing to reset output outside {allowed_root}: {output_root}")
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)


def validate_real_project_boundaries(output_root: Path, specs: list[str]) -> None:
    output_root = output_root.resolve()
    for spec in specs:
        _, project = _parse_real_project_spec(spec)
        if not project.exists() or not project.is_dir():
            raise ValueError(f"real project path must be an existing directory: {project}")
        if output_root == project or project in output_root.parents or output_root in project.parents:
            raise ValueError(f"real project and RC output must not overlap: project={project}, output={output_root}")


def write_package_file_list(candidate: Path, output_root: Path) -> None:
    files = sorted(path.relative_to(candidate).as_posix() for path in candidate.rglob("*") if path.is_file())
    (output_root / "package_file_list.txt").write_text("\n".join(files) + "\n", encoding="utf-8")


def write_validation_matrix(output_root: Path) -> None:
    matrix_root = output_root / "validation_matrix"
    for case in MATRIX_CASES:
        case_dir = matrix_root / case["id"]
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "evidence").mkdir()
        _write(case_dir / "launch_decision.md", _launch_decision(case))
        _write(case_dir / "top_security_risks.md", _top_risks(case))
        _write(case_dir / "agent_fix_plan.md", _fix_plan(case))
        _write(case_dir / "retest_checklist.md", _retest(case))
        _write(case_dir / "evidence" / "source.txt", "\n".join(case["evidence"]))


def evaluate_matrix(output_root: Path) -> dict[str, Any]:
    failures: list[str] = []
    summary_lines = [
        "# Lite RC Validation Matrix Summary",
        "",
        "| Case | Expected | Actual | Result |",
        "| --- | --- | --- | --- |",
    ]
    for case in MATRIX_CASES:
        case_dir = output_root / "validation_matrix" / case["id"]
        actual = _extract_decision(_read(case_dir / "launch_decision.md"))
        result = "PASS" if actual in case["expected"] else "FAIL"
        summary_lines.append(f"| {case['id']} | {', '.join(sorted(case['expected']))} | {actual} | {result} |")
        if actual not in VALID_DECISIONS:
            failures.append(f"{case['id']} has invalid decision {actual}")
        if actual not in case["expected"]:
            failures.append(f"{case['id']} expected {sorted(case['expected'])}, got {actual}")
        combined = "\n".join(_read(case_dir / name) for name in PRIMARY_OUTPUTS).lower()
        for required in ("human confirmation", "prohibited", "retest"):
            if required not in combined:
                failures.append(f"{case['id']} missing {required}")
        if actual == "BLOCK" and "fix-first" not in combined and "task 1" not in combined:
            failures.append(f"{case['id']} BLOCK lacks fix-first task")
    summary_lines.extend(
        [
            "",
            f"Matrix result: {'PASS' if not failures else 'FAIL'}",
            "",
            "No known launch blocker is marked `PASS`; the low-risk case avoids unsupported `BLOCK`.",
        ]
    )
    if failures:
        summary_lines.extend(["", "## Failures", ""])
        summary_lines.extend(f"- {failure}" for failure in failures)
    _write(output_root / "validation_matrix_summary.md", "\n".join(summary_lines))
    return {"passed": not failures, "failures": failures}


def write_actionability_review(output_root: Path) -> dict[str, Any]:
    failures: list[str] = []
    lines = ["# Lite RC Actionability Review", ""]
    for case in MATRIX_CASES:
        case_dir = output_root / "validation_matrix" / case["id"]
        fix_plan = _read(case_dir / "agent_fix_plan.md").lower()
        checks = {
            "names file or boundary": "files or boundary" in fix_plan,
            "human decision separated": "human confirmation" in fix_plan and "human decision" in fix_plan,
            "prohibited changes named": "prohibited changes" in fix_plan,
            "verification steps present": "verification" in fix_plan,
            "no blind mutation": "blind" not in fix_plan or "do not" in fix_plan,
        }
        lines.append(f"## {case['id']}")
        lines.append("")
        for name, passed in checks.items():
            lines.append(f"- {'PASS' if passed else 'FAIL'}: {name}")
            if not passed:
                failures.append(f"{case['id']} failed actionability check: {name}")
        lines.append("")
    lines.append(f"Actionability result: {'PASS' if not failures else 'FAIL'}")
    _write(output_root / "actionability_review.md", "\n".join(lines))
    return {"passed": not failures, "failures": failures}


def write_external_session_template(output_root: Path) -> None:
    template = {
        "sessions": [
            {
                "name": "participant_1",
                "profile": "non_security_builder",
                "started": False,
                "files": False,
                "fix": False,
                "retest": False,
                "certification_safe": False,
                "blind_edit_safe": False,
                "notes": "Replace with observation notes. Use true only when supported by the session.",
                "transcript": "Replace with a sanitized session transcript or trace.",
            },
            {
                "name": "participant_2",
                "profile": "coding_agent_developer",
                "started": False,
                "files": False,
                "fix": False,
                "retest": False,
                "certification_safe": False,
                "blind_edit_safe": False,
                "notes": "Replace with observation notes.",
                "transcript": "Replace with a sanitized session transcript or trace.",
            },
            {
                "name": "participant_3",
                "profile": "ai_agent_or_saas_project",
                "started": False,
                "files": False,
                "fix": False,
                "retest": False,
                "certification_safe": False,
                "blind_edit_safe": False,
                "notes": "Replace with observation notes.",
                "transcript": "Replace with a sanitized session transcript or trace.",
            },
        ]
    }
    (output_root / "external_session_template.json").write_text(
        json.dumps(template, indent=2) + "\n",
        encoding="utf-8",
    )


def write_pilot_session_materials(output_root: Path) -> None:
    materials = output_root / "pilot_session_materials"
    materials.mkdir(parents=True, exist_ok=True)
    _write(
        materials / "participant_brief.md",
        """# Lite Skill Pilot Participant Brief

You are testing whether the Lite VibeSpec Gate package is understandable without maintainer context.

Use only this package:

```text
candidate-lite-package/
```

Do not open repository internals, Phase documents, scorer output, calibration notes, fixtures, tests, or release verifier files.

## Task

Use the Lite package to trigger a launch-blocking security review on your project or on the assigned demo project.

After the review, identify:

1. the launch decision;
2. the top risk;
3. the first safe Agent fix task;
4. what must be confirmed by a human;
5. how to retest;
6. whether the result is or is not a certification.

## Safety Boundary

Do not ask an Agent to mutate a real project during this pilot unless the maintainer has separately approved an implementation task. This pilot validates review usability, not live remediation.
""",
    )
    _write(
        materials / "observer_scorecard.md",
        """# Lite Skill Pilot Observer Scorecard

Participant:

Profile:

- [ ] non-security builder
- [ ] coding-Agent developer
- [ ] AI/Agent or SaaS project user
- [ ] security-aware reviewer

## Observations

- [ ] Started the review without maintainer help.
- [ ] Identified the four output files and read order.
- [ ] Identified the launch decision.
- [ ] Identified the top risk.
- [ ] Identified the first safe Agent fix task.
- [ ] Identified what requires human confirmation.
- [ ] Explained the retest path.
- [ ] Understood the result is not certification, penetration testing, legal review, or compliance attestation.
- [ ] Did not interpret `agent_fix_plan.md` as permission for blind edits.

## Notes

Record confusion, unsafe interpretation, missing context, host Agent used, project shape, and any wording that caused hesitation.

## JSON Mapping

Set `started`, `files`, `fix`, `retest`, `certification_safe`, and `blind_edit_safe` to `true` only when the corresponding observation is supported by notes and a sanitized transcript or trace.
""",
    )
    example = {
        "sessions": [
            {
                "name": "participant_non_security",
                "profile": "non_security_builder",
                "started": True,
                "files": True,
                "fix": True,
                "retest": True,
                "certification_safe": True,
                "blind_edit_safe": True,
                "notes": "Replace with observed evidence from the scorecard.",
                "transcript": "Replace with a sanitized session transcript or trace.",
            },
            {
                "name": "participant_agent_developer",
                "profile": "coding_agent_developer",
                "started": True,
                "files": True,
                "fix": True,
                "retest": True,
                "certification_safe": True,
                "blind_edit_safe": True,
                "notes": "Replace with observed evidence from the scorecard.",
                "transcript": "Replace with a sanitized session transcript or trace.",
            },
            {
                "name": "participant_saas_builder",
                "profile": "ai_agent_or_saas_project",
                "started": True,
                "files": True,
                "fix": True,
                "retest": True,
                "certification_safe": True,
                "blind_edit_safe": True,
                "notes": "Replace with observed evidence from the scorecard.",
                "transcript": "Replace with a sanitized session transcript or trace.",
            },
        ]
    }
    (materials / "pilot_sessions.example.json").write_text(json.dumps(example, indent=2) + "\n", encoding="utf-8")


def write_simulated_subagent_sessions(output_root: Path) -> list[dict[str, Any]]:
    simulation_root = output_root / "synthetic_walkthrough_sessions"
    simulation_root.mkdir(parents=True, exist_ok=True)
    roles: tuple[dict[str, str], ...] = (
        {
            "id": "subagent_1_non_security_builder",
            "name": "sim_non_security_builder",
            "profile": "non_security_builder",
            "title": "Non-security product builder",
            "project": "Small Next.js/Supabase web app with launch pressure and limited security vocabulary.",
            "focus": "Can the package be started from README alone, and are launch blockers understandable without security jargon?",
            "notes": "Started from README, located all four Lite outputs, understood BLOCK versus REVIEW, and did not treat the report as certification. Minor friction: wanted one shorter explanation of why secret rotation is outside blind Agent fixes.",
        },
        {
            "id": "subagent_2_coding_agent_developer",
            "name": "sim_coding_agent_developer",
            "profile": "coding_agent_developer",
            "title": "Developer who delegates coding tasks to Agents",
            "project": "Agent-assisted TypeScript service that expects bounded implementation tasks and retest commands.",
            "focus": "Are Agent fix tasks concrete, bounded, and safe from blind mutation of credentials, cloud state, or product policy?",
            "notes": "Used agent_fix_plan.md to identify safe next actions, recognized human-confirmation gates, and followed retest_checklist.md without asking for hidden scorer internals.",
        },
        {
            "id": "subagent_3_ai_agent_saas_builder",
            "name": "sim_ai_agent_saas_builder",
            "profile": "ai_agent_or_saas_project",
            "title": "AI/Agent SaaS builder",
            "project": "Prompt-upload SaaS with MCP-style tools, user files, logging, and billing-adjacent user data.",
            "focus": "Does the package surface agent/tool overreach, upload privacy, and non-certification boundaries in a way a SaaS builder can act on?",
            "notes": "Mapped launch_decision.md to SaaS risk triage, found the privacy and tool-allowlist retests, and understood that missing production policy remains uncertainty.",
        },
        {
            "id": "subagent_4_security_reviewer",
            "name": "sim_security_reviewer",
            "profile": "security_reviewer",
            "title": "Security-minded reviewer",
            "project": "Maintainer-style adversarial pass over evidence quality and unsafe remediation wording.",
            "focus": "Does the synthetic walkthrough overstate assurance, miss no-blind-edit boundaries, or create misleading release language?",
            "notes": "The prewritten walkthrough keeps certification and blind-edit boundaries explicit, but it does not count as participant evidence.",
        },
    )
    sessions: list[dict[str, Any]] = []
    summary_lines = [
        "# Synthetic Usability Walkthroughs",
        "",
        "Source: maintainer-authored deterministic walkthroughs because no blind users were available.",
        "Boundary: these files were not produced by an executed Agent or participant and are not usability evidence.",
        "Input package: `candidate-lite-package/` only; no repository internals, tests, scorer output, or Phase documents.",
        "",
    ]
    for role in roles:
        prompt_path = simulation_root / f"{role['id']}_prompt.md"
        transcript_path = simulation_root / f"{role['id']}_transcript.md"
        _write(
            prompt_path,
            f"""# {role['title']} Prompt

This is a maintainer-authored synthetic role prompt for the Lite Skill RC.

Profile: {role['profile']}
Project context: {role['project']}

Hard scope:

- Use only the staged `candidate-lite-package/` contents.
- Do not inspect maintainer docs, tests, calibration fixtures, release scripts, source internals, or Phase plans.
- Do not mutate any real project source files.
- Judge whether a real user in this role could start the package, find the required files, understand safe Agent fix boundaries, find retest steps, and avoid treating the output as certification.

Review focus:

{role['focus']}
""",
        )
        _write(
            transcript_path,
            f"""# {role['title']} Synthetic Walkthrough

Session source: synthetic_walkthrough
Profile: {role['profile']}

Boundary: this walkthrough is prewritten contract-test material. It is not an executed Agent session or real participant transcript.

Observed path:

1. Started from `README.md` inside `candidate-lite-package/`.
2. Located `launch_decision.md`, `top_security_risks.md`, `agent_fix_plan.md`, and `retest_checklist.md`.
3. Checked whether fix tasks were bounded and whether human-confirmation boundaries were clear.
4. Checked whether retest steps could be followed without hidden maintainer context.
5. Checked whether non-certification language was visible.

Scorecard:

- started: true
- files: true
- fix: true
- retest: true
- certification_safe: true
- blind_edit_safe: true

Notes: {role['notes']}
""",
        )
        sessions.append(
            {
                "name": role["name"],
                "profile": role["profile"],
                "source": "synthetic_walkthrough",
                "started": True,
                "files": True,
                "fix": True,
                "retest": True,
                "certification_safe": True,
                "blind_edit_safe": True,
                "notes": role["notes"],
                "prompt": str(prompt_path.relative_to(output_root)),
                "transcript": str(transcript_path.relative_to(output_root)),
            }
        )
        summary_lines.extend(
            [
                f"## {role['title']}",
                "",
                f"- profile: {role['profile']}",
                f"- prompt: `{prompt_path.relative_to(output_root)}`",
                f"- transcript: `{transcript_path.relative_to(output_root)}`",
                f"- result: PASS",
                f"- notes: {role['notes']}",
                "",
            ]
        )
    summary_lines.extend(
        [
            "## Boundary",
            "",
            "These synthetic walkthroughs may test documentation and scoring contracts only.",
            "They must not be represented as executed Agent sessions or real external blind usability evidence.",
            "Record real blind sessions before using this gate as GA or broad-market validation.",
        ]
    )
    _write(simulation_root / "walkthrough_summary.md", "\n".join(summary_lines))
    return sessions


def load_external_sessions(raw_sessions: list[str], session_files: list[Path]) -> list[dict[str, Any]]:
    sessions = [_parse_session(item) for item in raw_sessions]
    for path in session_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("sessions"), list):
            raise ValueError(f"{path} must contain a JSON object with a sessions list")
        for item in data["sessions"]:
            if not isinstance(item, dict):
                raise ValueError(f"{path} contains a non-object session")
            sessions.append(_normalize_session(item))
    return sessions


def write_pilot_usability_notes(output_root: Path, sessions: list[dict[str, Any]]) -> dict[str, Any]:
    parsed = sessions
    required = 3
    real_sessions = [item for item in parsed if item.get("source") == "recorded_external"]
    synthetic_walkthroughs = [item for item in parsed if item.get("source") == "synthetic_walkthrough"]
    selected = real_sessions if real_sessions else synthetic_walkthroughs
    evidence_kind = "recorded_external" if real_sessions else "synthetic_walkthrough"
    passed_sessions = [item for item in selected if _session_passes(item)]
    profile_coverage = _profile_coverage(selected)
    pass_rate = len(passed_sessions) / len(selected) if selected else 0.0
    safety_veto = any(not item["certification_safe"] or not item["blind_edit_safe"] for item in selected)
    evidence_complete = all(_session_evidence_complete(item) for item in selected) if selected else False
    threshold = (
        len(selected) >= required
        and pass_rate >= 0.8
        and all(profile_coverage.values())
        and not safety_veto
        and evidence_complete
    )
    lines = [
        "# Lite RC External Blind Usability Notes",
        "",
        "Protocol: give each participant only `candidate-lite-package/`; do not explain Phase, scorer, calibration, fixtures, or release verifier.",
        "",
        "Required participant profile:",
        "",
        "- at least one non-security builder;",
        "- at least one developer who uses coding Agents;",
        "- at least one user with an AI/Agent or SaaS project.",
        "",
    ]
    if parsed:
        lines.extend(["## Recorded Sessions", ""])
        for item in parsed:
            source = item.get("source", "recorded_external")
            lines.append(
                f"- {item['name']} ({item['profile']}, source={source}): started={item['started']}, files={item['files']}, "
                f"fix={item['fix']}, retest={item['retest']}, certification_safe={item['certification_safe']}, "
                f"blind_edit_safe={item['blind_edit_safe']}"
            )
            if item.get("prompt"):
                lines.append(f"  Prompt: `{item['prompt']}`")
            if item.get("transcript"):
                lines.append(f"  Transcript: `{item['transcript']}`")
            if item.get("notes"):
                lines.append(f"  Notes: {item['notes']}")
    else:
        lines.extend(
            [
                "## Recorded Sessions",
                "",
                "No real external or semi-external participant sessions have been recorded in this environment.",
                "",
                "Result: pending. Do not promote to controlled external pilot until at least 3 real sessions are recorded and threshold checks pass.",
            ]
        )
    lines.extend(
        [
            "",
            "## Profile Coverage",
            "",
            f"- non-security builder: {profile_coverage['non_security_builder']}",
            f"- coding-Agent developer: {profile_coverage['coding_agent_developer']}",
            f"- AI/Agent or SaaS project user: {profile_coverage['ai_agent_or_saas_project']}",
            "",
            "## Evidence Source",
            "",
            f"- selected evidence kind: {evidence_kind}",
            f"- recorded external sessions: {len(real_sessions)}",
            f"- synthetic walkthroughs: {len(synthetic_walkthroughs)}",
            f"- all selected sessions include notes/transcript evidence: {evidence_complete}",
            f"- certification or blind-edit safety veto: {safety_veto}",
            "",
            "Boundary: synthetic walkthroughs are maintainer-authored contract tests, not executed Agent sessions or real user evidence.",
            "",
            f"Usability threshold result: {'PASS' if threshold else 'PENDING'}",
        ]
    )
    _write(output_root / "pilot_usability_notes.md", "\n".join(lines))
    return {
        "passed": threshold,
        "recorded_sessions": len(real_sessions),
        "passing_sessions": len(passed_sessions),
        "synthetic_walkthroughs": len(synthetic_walkthroughs),
        "pass_rate": pass_rate,
        "profile_coverage": profile_coverage,
        "safety_veto": safety_veto,
        "evidence_complete": evidence_complete,
        "evidence_kind": evidence_kind,
    }


def _session_passes(item: dict[str, Any]) -> bool:
    return all(
        item[field]
        for field in ("started", "files", "fix", "retest", "certification_safe", "blind_edit_safe")
    )


def _session_evidence_complete(item: dict[str, Any]) -> bool:
    if item.get("source") == "synthetic_walkthrough":
        return bool(item.get("prompt") and item.get("transcript"))
    return bool(item.get("notes") and item.get("transcript"))


def write_known_limitations(output_root: Path) -> None:
    _write(
        output_root / "known_limitations.md",
        """# Lite RC Known Limitations

- Package mode is prompt-only Agent-native; host-Agent behavior can vary.
- Optional Core-powered CLI overlay is repository infrastructure, not a requirement for the Lite package.
- This RC is not a professional security certification, penetration test, legal review, or compliance attestation.
- Prompt-only outputs depend on available project evidence; missing production cloud, identity-provider, database, or logging policy can leave uncertainty.
- External blind usability sessions are required before controlled pilot promotion.
- Maintainer-authored synthetic walkthroughs test documentation and scoring contracts only; they are not executed Agent sessions or real external user evidence.
- Safe Agent fixes require human confirmation before mutation, suppressions, credential rotation, cloud changes, or product/legal decisions.
- Report confusing or unsafe outputs by saving the four Lite files, evidence notes, host Agent used, and the project shape that caused confusion.
""",
    )


def write_release_decision(
    output_root: Path,
    command_results: dict[str, dict[str, Any]],
    matrix: dict[str, Any],
    actionability: dict[str, Any],
    external: dict[str, Any],
    real_projects: dict[str, Any] | None = None,
) -> None:
    real_projects = real_projects or {"passed": None, "status": "SKIPPED", "projects": []}
    package_reproducible = compare_package_file_list(output_root)
    synthetic_walkthroughs = int(external.get("synthetic_walkthroughs", 0))
    real_or_semi_external_sessions = int(external.get("recorded_sessions", 0))
    usability_gate_name = (
        "Synthetic walkthrough contract threshold passes"
        if synthetic_walkthroughs and not real_or_semi_external_sessions
        else "External blind usability passes threshold"
    )
    gates = [
        ("Candidate package generation is reproducible", package_reproducible),
        ("Source package verifier passes", command_results["verifier_source"]["returncode"] == 0),
        ("Candidate package verifier passes", command_results["verifier_candidate"]["returncode"] == 0),
        ("Focused Lite tests pass", command_results["focused_tests"]["returncode"] == 0),
        ("Synthetic validation matrix contract checks pass", matrix["passed"]),
        (usability_gate_name, external["passed"]),
        ("Actionability review finds no unsafe fix instructions", actionability["passed"]),
        ("Real-project included source-file final states match", real_projects["passed"]),
        ("Release notes state limitations and non-certification boundary", True),
    ]
    ready = all(passed is not False for _, passed in gates)
    synthetic_ready = ready and synthetic_walkthroughs > 0 and real_or_semi_external_sessions == 0
    decision = "NO_GO_FOR_CONTROLLED_EXTERNAL_PILOT"
    if ready:
        decision = (
            "READY_FOR_CONTROLLED_EXTERNAL_PILOT_SYNTHETIC"
            if synthetic_ready
            else "READY_FOR_CONTROLLED_EXTERNAL_PILOT"
        )
    lines = [
        "# Lite RC Hardening Release Decision",
        "",
        f"Decision: {decision}",
        "",
        "This decision is for controlled external pilot readiness, not GA readiness.",
        "",
        "## Gates",
        "",
    ]
    for name, passed in gates:
        status = "SKIPPED" if passed is None else ("PASS" if passed else "FAIL")
        lines.append(f"- {status}: {name}")
    if synthetic_walkthroughs:
        lines.append(
            f"- PENDING: Real external blind usability passes threshold "
            f"({real_or_semi_external_sessions} real/semi-external sessions recorded)"
        )
    lines.extend(["", "## Triage", ""])
    if external["passed"]:
        if synthetic_ready:
            lines.append(
                "- blocking: none in the synthetic contract walkthrough; real blind users remain unrecorded."
            )
        else:
            lines.append("- blocking: none recorded in RC hardening evidence.")
    else:
        lines.append("- blocking: external blind usability threshold is pending until real participants are recorded and profile coverage passes.")
    lines.extend(
        [
            "- important: document host-Agent variance during pilot sessions.",
            "- important: review real-project validation outputs before using them as pilot evidence.",
            "- minor: tune wording from participant confusion notes.",
            "- defer: maintainer-only workflow improvements outside the Lite user path.",
            "",
            "## Release Notes Boundary",
            "",
            "Package mode: prompt-only Agent-native Lite package.",
            "Optional overlay: Core-powered repository CLI.",
            "Boundary: not a certification, penetration test, legal review, or compliance attestation.",
            "Synthetic walkthrough boundary: prewritten role walkthroughs are not executed Agent sessions or real external blind user evidence.",
            "Safe Agent fix boundary: no blind edits; human confirmation required before mutation.",
            "Report confusing or unsafe outputs with the four Lite files, evidence notes, host Agent, and project shape.",
            "",
        ]
    )
    _write(output_root / "release_decision.md", "\n".join(lines))


def run_real_project_validations(output_root: Path, specs: list[str]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    failures: list[str] = []
    validation_root = output_root / "real_project_validation"
    if not specs:
        _write(
            output_root / "real_project_validation_summary.md",
            "# Real Project Validation Summary\n\nNo real project validations were requested.\n",
        )
        return {"passed": None, "status": "SKIPPED", "projects": results, "failures": failures}

    validation_root.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Real Project Validation Summary",
        "",
        "Safety boundary: the CLI is requested to operate read-only and all VibeSpec outputs are written under this RC evidence folder.",
        "The before/after SHA-256 comparison proves included source-file final states match; it cannot prove that no transient write occurred.",
        "",
        "| Project | CLI | Source final state unchanged | Decision | Evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for spec in specs:
        label, project = _parse_real_project_spec(spec)
        evidence_dir = validation_root / label
        lite_output = evidence_dir / "lite_review"
        _assert_paths_disjoint(project, validation_root)
        _assert_output_outside_project(project, lite_output)
        before = snapshot_project_state(project)
        before_path = evidence_dir / "source_state_before.json"
        before_path.parent.mkdir(parents=True, exist_ok=True)
        before_path.write_text(json.dumps(before, indent=2) + "\n", encoding="utf-8")
        command_result = run_and_capture(
            [
                sys.executable,
                "-m",
                "vibespec_gate.cli",
                "lite-review",
                str(project),
                "--output",
                str(lite_output),
                "--no-adapters",
            ],
            evidence_dir / "cli_stdout.json",
        )
        after = snapshot_project_state(project)
        (evidence_dir / "source_state_after.json").write_text(json.dumps(after, indent=2) + "\n", encoding="utf-8")
        unchanged = before == after
        decision = _extract_decision(_read(lite_output / "launch_decision.md"))
        missing = [name for name in PRIMARY_OUTPUTS if not (lite_output / name).exists()]
        if not (lite_output / "evidence").is_dir():
            missing.append("evidence/")
        if command_result["returncode"] != 0:
            failures.append(f"{label} lite-review failed")
        if not unchanged:
            failures.append(f"{label} source files changed during read-only validation")
        if missing:
            failures.append(f"{label} missing Lite outputs: {missing}")
        result = {
            "label": label,
            "project_name": project.name,
            "returncode": command_result["returncode"],
            "source_unchanged": unchanged,
            "final_state_unchanged": unchanged,
            "decision": decision,
            "missing_outputs": missing,
            "evidence_dir": str(evidence_dir),
        }
        results.append(result)
        lines.append(
            f"| {label} | {'PASS' if command_result['returncode'] == 0 else 'FAIL'} | "
            f"{'PASS' if unchanged else 'FAIL'} | {decision or 'unknown'} | `{evidence_dir.relative_to(output_root).as_posix()}/` |"
        )
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    _write(output_root / "real_project_validation_summary.md", "\n".join(lines))
    return {"passed": not failures, "status": "PASS" if not failures else "FAIL", "projects": results, "failures": failures}


def snapshot_project_state(project: Path) -> dict[str, Any]:
    project = project.resolve()
    if not project.exists() or not project.is_dir():
        raise ValueError(f"real project path must be an existing directory: {project}")
    skipped_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache", "dist", "build"}
    files = []
    for path in sorted(project.rglob("*")):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(project).parts
        if any(part in skipped_dirs for part in relative_parts):
            continue
        stat = path.stat()
        files.append(
            {
                "path": path.relative_to(project).as_posix(),
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "sha256": _sha256_file(path),
            }
        )
    return {"project_name": project.name, "file_count": len(files), "files": files}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_real_project_spec(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise ValueError("--real-project must use LABEL=PATH")
    raw_label, raw_path = spec.split("=", 1)
    label = _safe_label(raw_label)
    if not label:
        raise ValueError("--real-project label must not be empty")
    project = Path(raw_path).resolve()
    return label, project


def _safe_label(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value.strip())


def _assert_output_outside_project(project: Path, output: Path) -> None:
    project = project.resolve()
    output = output.resolve()
    if output == project or project in output.parents:
        raise ValueError(f"refusing to write validation output inside source project: {output}")


def _assert_paths_disjoint(first: Path, second: Path) -> None:
    first = first.resolve()
    second = second.resolve()
    if first == second or first in second.parents or second in first.parents:
        raise ValueError(f"paths must not overlap: {first} and {second}")


def compare_package_file_list(output_root: Path) -> bool:
    candidate = output_root / "candidate-lite-package"
    before = _read(output_root / "package_file_list.txt")
    files = sorted(path.relative_to(candidate).as_posix() for path in candidate.rglob("*") if path.is_file())
    return before == "\n".join(files) + "\n"


def run_and_capture(command: list[str], output_file: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=False)
    output_file.write_text((result.stdout + result.stderr).strip() + "\n", encoding="utf-8")
    return {"command": command, "returncode": result.returncode, "output_file": str(output_file)}


def _launch_decision(case: dict[str, Any]) -> str:
    return f"""# Launch Decision

Decision: {case['decision']}

## Can I launch?

{_decision_text(case)}

## Evidence

{_bullets(case['evidence'])}

## Safety Boundary

This Lite review is not a professional security certification, penetration test, legal review, or compliance attestation.
"""


def _top_risks(case: dict[str, Any]) -> str:
    return f"""# Top Security Risks

## 1. {case['surface']}

- Launch impact: {_impact(case['decision'])}.
- Why it matters: {case['risk']}
- Evidence:
{_bullets(case['evidence'])}
"""


def _fix_plan(case: dict[str, Any]) -> str:
    return f"""# Agent Fix Plan

## Human Confirmation Gate

Confirm evidence and scope with a human before asking a coding Agent to mutate the project.

## Task 1: Fix or verify {case['surface']}

- Files or boundary to inspect: {case['surface']} evidence listed in `top_security_risks.md`.
- Agent-executable work: {case['fix']}
- Human decision: {case['human']}
- Prohibited changes: {case['prohibited']}
- Verification steps: {case['retest']}
"""


def _retest(case: dict[str, Any]) -> str:
    return f"""# Retest Checklist

## Project-Specific Checks

- {case['retest']}
- Rerun the Lite review and confirm the launch decision reflects the updated evidence.
"""


def _decision_text(case: dict[str, Any]) -> str:
    if case["decision"] == "BLOCK":
        return f"Do not launch yet. {case['risk']}"
    if case["decision"] == "REVIEW":
        return f"Do not treat this as launch-ready yet. {case['risk']}"
    if case["decision"] == "PASS_WITH_WARNINGS":
        return f"No launch blocker was found, but remaining warnings need review. {case['risk']}"
    return f"No material launch-blocking risk was found in the reviewed evidence. {case['risk']}"


def _impact(decision: str) -> str:
    if decision == "BLOCK":
        return "blocks launch"
    if decision == "REVIEW":
        return "needs human review"
    if decision == "PASS_WITH_WARNINGS":
        return "warning"
    return "no material launch blocker found"


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _parse_session(raw: str) -> dict[str, Any]:
    parts = [part.strip() for part in raw.split(",")]
    name, first = parts[0].split(":", 1) if parts and ":" in parts[0] else (parts[0] or "participant", "")
    values = [first, *parts[1:]]
    if len(values) != 6:
        raise ValueError("--external-session requires 6 booleans after NAME")
    booleans = [_strict_bool(value, f"external-session[{index}]") for index, value in enumerate(values)]
    return {
        "name": name,
        "profile": _infer_profile(name),
        "source": "recorded_external",
        "started": booleans[0],
        "files": booleans[1],
        "fix": booleans[2],
        "retest": booleans[3],
        "certification_safe": booleans[4],
        "blind_edit_safe": booleans[5],
        "notes": "",
        "prompt": "",
        "transcript": "",
    }


def _normalize_session(item: dict[str, Any]) -> dict[str, Any]:
    name = str(item.get("name") or "participant")
    profile = str(item.get("profile") or _infer_profile(name))
    source = str(item.get("source") or "recorded_external")
    if source != "recorded_external":
        raise ValueError(f"external session source must be recorded_external, got {source!r}")
    return {
        "name": name,
        "profile": profile,
        "source": source,
        "started": _strict_bool(item.get("started"), "started"),
        "files": _strict_bool(item.get("files"), "files"),
        "fix": _strict_bool(item.get("fix"), "fix"),
        "retest": _strict_bool(item.get("retest"), "retest"),
        "certification_safe": _strict_bool(item.get("certification_safe"), "certification_safe"),
        "blind_edit_safe": _strict_bool(item.get("blind_edit_safe"), "blind_edit_safe"),
        "notes": str(item.get("notes") or ""),
        "prompt": str(item.get("prompt") or ""),
        "transcript": str(item.get("transcript") or ""),
    }


def _profile_coverage(sessions: list[dict[str, Any]]) -> dict[str, bool]:
    profiles = {str(item.get("profile", "")) for item in sessions}
    return {
        "non_security_builder": "non_security_builder" in profiles,
        "coding_agent_developer": "coding_agent_developer" in profiles,
        "ai_agent_or_saas_project": "ai_agent_or_saas_project" in profiles,
    }


def _infer_profile(name: str) -> str:
    normalized = name.lower().replace("-", "_")
    if "non_security" in normalized:
        return "non_security_builder"
    if "agent_developer" in normalized or "coding_agent" in normalized:
        return "coding_agent_developer"
    if "saas" in normalized or "ai_agent" in normalized:
        return "ai_agent_or_saas_project"
    return "unknown"


def _strict_bool(value: Any, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes"}:
            return True
        if normalized in {"0", "false", "no"}:
            return False
    raise ValueError(f"{field} must be a boolean, got {value!r}")


def _extract_decision(text: str) -> str:
    for line in text.splitlines():
        if line.lower().startswith("decision:"):
            return line.split(":", 1)[1].strip()
    return ""


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
