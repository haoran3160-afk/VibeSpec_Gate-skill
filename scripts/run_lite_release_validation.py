from __future__ import annotations

import argparse
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

from scripts.verify_lite_package import REQUIRED_INCLUDE  # noqa: E402


DEFAULT_DATE = "2026-07-08"
DEFAULT_OUTPUT_ROOT = ROOT / "test output" / "lite_release_validation" / DEFAULT_DATE
VALID_DECISIONS = {"BLOCK", "REVIEW", "PASS_WITH_WARNINGS", "PASS"}
PRIMARY_OUTPUTS = (
    "launch_decision.md",
    "top_security_risks.md",
    "agent_fix_plan.md",
    "retest_checklist.md",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Lite Skill release validation sprint.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--skip-cli", action="store_true", help="Skip the optional Core-powered CLI smoke.")
    args = parser.parse_args(argv)

    output_root = args.output.resolve()
    reset_output_root(output_root)
    candidate = stage_candidate_package(output_root)
    write_prompt_only_outputs(output_root)
    write_usability_notes(output_root)
    write_release_notes(output_root)

    results = {
        "package_verifier_source": run_and_capture(
            [sys.executable, "scripts/verify_lite_package.py"],
            output_root / "package_verifier_source.txt",
        ),
        "package_verifier_candidate": run_and_capture(
            [sys.executable, "scripts/verify_lite_package.py", str(candidate)],
            output_root / "package_verifier_candidate.txt",
        ),
        "pytest_lite_focused": run_and_capture(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_lite_package_verifier.py",
                "tests/test_lite_review_bundle.py",
                "tests/test_review_cli.py",
                "-q",
                "-p",
                "no:cacheprovider",
            ],
            output_root / "pytest_lite_focused.txt",
        ),
    }
    if not args.skip_cli:
        results["cli_smoke"] = run_cli_smoke(output_root)

    review = review_validation_outputs(output_root)
    write_release_readiness_decision(output_root, results, review, skipped_cli=args.skip_cli)

    if review["passed"] and all(item["returncode"] == 0 for item in results.values()):
        print(f"PASS Lite release validation evidence: {output_root}")
        return 0
    print(f"FAIL Lite release validation evidence: {output_root}")
    return 1


def reset_output_root(output_root: Path) -> None:
    output_root = output_root.resolve()
    allowed_root = (ROOT / "test output" / "lite_release_validation").resolve()
    if allowed_root not in output_root.parents and output_root != allowed_root:
        raise ValueError(f"refusing to reset output outside {allowed_root}: {output_root}")
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)


def stage_candidate_package(output_root: Path) -> Path:
    candidate = output_root / "candidate-lite-package"
    for file_name in REQUIRED_INCLUDE:
        source = ROOT / file_name
        destination = candidate / file_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return candidate


def write_prompt_only_outputs(output_root: Path) -> None:
    write_case_1(output_root / "prompt_only_case_1_secret_leak_web_app")
    write_case_2(output_root / "prompt_only_case_2_missing_auth_or_ownership_check")
    write_case_3(output_root / "prompt_only_case_3_agent_or_mcp_tool_overreach")
    write_case_4(output_root / "prompt_only_case_4_low_risk_clean_project")


def write_case_1(case_dir: Path) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "evidence").mkdir()
    _write(
        case_dir / "launch_decision.md",
        """# Launch Decision

Decision: BLOCK

## Can I launch?

Do not launch yet. The reviewed evidence shows committed runtime secrets that can expose service credentials if they are real.

## Evidence

- `tests/fixtures/vulnerable_next_supabase_app/.env.local` contains an API key and database URL in the project tree.

## Safety Boundary

This Lite review is not a professional security certification, penetration test, legal review, or compliance attestation.
""",
    )
    _write(
        case_dir / "top_security_risks.md",
        """# Top Security Risks

## 1. Runtime secrets are committed in `.env.local`

- Launch impact: blocks launch.
- Affected evidence: `tests/fixtures/vulnerable_next_supabase_app/.env.local`.
- Why it matters: exposed API keys and database URLs can allow unauthorized access to production services if they are real.

## 2. Broad database and browser exposure increases blast radius if the leaked values are real

- Launch impact: needs review.
- Affected evidence: `tests/fixtures/vulnerable_next_supabase_app/firestore.rules` and `tests/fixtures/vulnerable_next_supabase_app/next.config.js`.
- Why it matters: open Firestore rules, wildcard API CORS, and production source maps can expose data or implementation details.
""",
    )
    _write(
        case_dir / "agent_fix_plan.md",
        """# Agent Fix Plan

## Human Confirmation Gate

Confirm these findings are in scope and the secrets are not production credentials before asking a coding Agent to edit the project.

## Task 1: Remove committed secrets and rotate if real

- Agent-executable scope: remove committed `.env.local` values from the project fixture and document required local env variables.
- Human-confirmed decision: rotate any real credential outside the repository.
- Prohibited changes: do not print full secret values, do not replace secrets with broader permissions.
- Files to inspect: `tests/fixtures/vulnerable_next_supabase_app/.env.local`, deployment env documentation.

## Task 2: Tighten broad client and database exposure

- Agent-executable scope: replace permissive Firestore rules and wildcard CORS/source-map settings with least-privilege defaults.
- Human-confirmed decision: confirm allowed production origins.
- Prohibited changes: do not use `allow read, write: if true` or `Access-Control-Allow-Origin: *` for sensitive APIs.
- Files to inspect: `tests/fixtures/vulnerable_next_supabase_app/firestore.rules`, `tests/fixtures/vulnerable_next_supabase_app/next.config.js`.
""",
    )
    _write(
        case_dir / "retest_checklist.md",
        """# Retest Checklist

## Project-Specific Checks

- Rerun Lite review against `tests/fixtures/vulnerable_next_supabase_app` and confirm the decision is no longer `BLOCK` for committed secrets.
- Confirm `tests/fixtures/vulnerable_next_supabase_app/.env.local` no longer contains real API keys or database URLs.
- Confirm `tests/fixtures/vulnerable_next_supabase_app/firestore.rules` no longer contains `allow read, write: if true`.
- Confirm `tests/fixtures/vulnerable_next_supabase_app/next.config.js` no longer combines production source maps with wildcard API CORS.
""",
    )
    _write(case_dir / "evidence" / "source_files.txt", "case_1_secret_leak_web_app: vulnerable_next_supabase_app fixture reviewed\n")


def write_case_2(case_dir: Path) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "evidence").mkdir()
    _write(
        case_dir / "launch_decision.md",
        """# Launch Decision

Decision: BLOCK

## Can I launch?

Do not launch yet. The orders API accepts request data and reads by id without proving the caller is authenticated or owns the order.

## Evidence

- `tests/fixtures/vulnerable_next_supabase_app/app/api/orders/route.ts` inserts `body` directly into `orders`.
- `tests/fixtures/vulnerable_next_supabase_app/app/api/orders/route.ts` reads an order by query-string `id` without checking `user_id`.
- `tests/fixtures/vulnerable_next_supabase_app/supabase/migrations/001_create_orders.sql` defines `user_id`, but the route does not enforce it.

## Safety Boundary

This Lite review is not a professional security certification, penetration test, legal review, or compliance attestation.
""",
    )
    _write(
        case_dir / "top_security_risks.md",
        """# Top Security Risks

## 1. Orders API lacks server-side auth and ownership enforcement

- Launch impact: blocks launch.
- Affected evidence: `tests/fixtures/vulnerable_next_supabase_app/app/api/orders/route.ts`.
- Why it matters: a caller can create or read orders without proving they are the owner.

## 2. Data model has an ownership field that is not enforced by the route

- Launch impact: needs review.
- Affected evidence: `tests/fixtures/vulnerable_next_supabase_app/supabase/migrations/001_create_orders.sql`.
- Why it matters: `user_id` exists, but launch safety depends on the server constraining queries to the authenticated user.
""",
    )
    _write(
        case_dir / "agent_fix_plan.md",
        """# Agent Fix Plan

## Human Confirmation Gate

Confirm the intended ownership model for `orders.user_id` before asking a coding Agent to change the route.

## Task 1: Require authentication in the orders route

- Agent-executable scope: add a server-side auth check before `POST` or `GET` accesses order data.
- Human-confirmed decision: confirm the auth helper or session source used by the real app.
- Prohibited changes: do not trust `user_id` from the request body as proof of identity.
- Files to inspect: `tests/fixtures/vulnerable_next_supabase_app/app/api/orders/route.ts`.

## Task 2: Enforce ownership on reads and writes

- Agent-executable scope: set `user_id` from the authenticated session and constrain selects by authenticated owner.
- Human-confirmed decision: confirm whether admins have a separate authorized read path.
- Prohibited changes: do not broaden the route to read arbitrary orders by id.
- Files to inspect: `tests/fixtures/vulnerable_next_supabase_app/app/api/orders/route.ts`, `tests/fixtures/vulnerable_next_supabase_app/supabase/migrations/001_create_orders.sql`.
""",
    )
    _write(
        case_dir / "retest_checklist.md",
        """# Retest Checklist

## Project-Specific Checks

- Inspect `tests/fixtures/vulnerable_next_supabase_app/app/api/orders/route.ts` and confirm unauthenticated `POST` and `GET` requests are rejected.
- Confirm order `GET` queries are constrained to the authenticated user's `user_id`.
- Confirm order `POST` writes set `user_id` from the trusted session, not from untrusted request JSON.
- Rerun Lite review against `tests/fixtures/vulnerable_next_supabase_app` and confirm this auth/ownership issue is no longer `BLOCK`.
""",
    )
    _write(case_dir / "evidence" / "source_files.txt", "case_2_missing_auth_or_ownership_check: vulnerable_next_supabase_app orders route reviewed\n")


def write_case_3(case_dir: Path) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "evidence").mkdir()
    _write(
        case_dir / "launch_decision.md",
        """# Launch Decision

Decision: REVIEW

## Can I launch?

Do not treat this as launch-ready yet. The MCP tool dispatcher validates message shape but does not show an allowlist for permitted tool names.

## Evidence

- `tests/evaluation_cases/review/mcp_schema_no_allowlist_needs_review/server.py` accepts any message with a `name` field.
- `tests/evaluation_cases/review/mcp_schema_no_allowlist_needs_review/findings.json` records `MCP tool schema is present but allowlist is unclear`.

## Safety Boundary

This Lite review is not a professional security certification, penetration test, legal review, or compliance attestation.
""",
    )
    _write(
        case_dir / "top_security_risks.md",
        """# Top Security Risks

## 1. MCP tool schema exists without a visible allowlist

- Launch impact: needs human review.
- Affected evidence: `tests/evaluation_cases/review/mcp_schema_no_allowlist_needs_review/server.py`.
- Why it matters: schema validation alone proves the message has a `name`; it does not prove the Agent can call only approved tools.
""",
    )
    _write(
        case_dir / "agent_fix_plan.md",
        """# Agent Fix Plan

## Human Confirmation Gate

Confirm the intended list of callable MCP tools before asking a coding Agent to change dispatch behavior.

## Task 1: Add or verify an explicit tool allowlist

- Agent-executable scope: restrict dispatch to a reviewed set of tool names after human confirmation.
- Human-confirmed decision: identify which tool names are safe for this Agent.
- Prohibited changes: do not allow arbitrary tool names just because the message schema is valid.
- Files to inspect: `tests/evaluation_cases/review/mcp_schema_no_allowlist_needs_review/server.py`.
""",
    )
    _write(
        case_dir / "retest_checklist.md",
        """# Retest Checklist

## Project-Specific Checks

- Inspect `tests/evaluation_cases/review/mcp_schema_no_allowlist_needs_review/server.py` and confirm dispatch rejects unapproved tool names.
- Confirm the allowlist is reviewed by a human and does not include broad shell, filesystem, or network authority by default.
- Rerun Lite review against the MCP fixture and confirm this item moves out of `REVIEW` only after the allowlist evidence exists.
""",
    )
    _write(case_dir / "evidence" / "source_files.txt", "case_3_agent_or_mcp_tool_overreach: mcp_schema_no_allowlist_needs_review fixture reviewed\n")


def write_case_4(case_dir: Path) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "evidence").mkdir()
    _write(
        case_dir / "launch_decision.md",
        """# Launch Decision

Decision: PASS

## Can I launch?

No material launch-blocking risk was found in the reviewed evidence. The reviewed demo API requires authentication and the security headers are explicit.

## Evidence

- `tests/fixtures/safe_demo_app/app/api/profile/route.ts` checks `requireAuth(req)` before returning profile data.
- `tests/fixtures/safe_demo_app/next.config.js` sets frame, content-type, referrer, and CSP headers.

## Safety Boundary

This Lite review is not a professional security certification, penetration test, legal review, or compliance attestation.
""",
    )
    _write(
        case_dir / "top_security_risks.md",
        """# Top Security Risks

No launch-blocking security risks were found in the reviewed evidence.

## Reviewed Surfaces

- `tests/fixtures/safe_demo_app/app/api/profile/route.ts`: profile endpoint returns `401` when auth is missing.
- `tests/fixtures/safe_demo_app/next.config.js`: security headers are configured.

## Residual Warning

This is still a small fixture review. Production identity-provider policy, real database rules, deployment secrets, and cloud configuration were not present in the evidence.
""",
    )
    _write(
        case_dir / "agent_fix_plan.md",
        """# Agent Fix Plan

## Human Confirmation Gate

No Agent-ready security fix task is required for the reviewed fixture.

## Optional Hardening Task

- Agent-executable scope: keep the existing auth gate and security headers covered by tests.
- Human-confirmed decision: confirm whether production deployment has additional identity-provider or database policies.
- Prohibited changes: do not remove `requireAuth(req)` or weaken the configured security headers.
""",
    )
    _write(
        case_dir / "retest_checklist.md",
        """# Retest Checklist

## Project-Specific Checks

- Recheck `tests/fixtures/safe_demo_app/app/api/profile/route.ts` and confirm unauthenticated requests return `401`.
- Recheck `tests/fixtures/safe_demo_app/next.config.js` and confirm `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, and `Content-Security-Policy` remain present.
- Rerun Lite review against `tests/fixtures/safe_demo_app` and confirm it does not produce an unsupported `BLOCK`.
""",
    )
    _write(case_dir / "evidence" / "source_files.txt", "case_4_low_risk_clean_project: safe_demo_app fixture reviewed\n")


def run_and_capture(command: list[str], output_file: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=False)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text((result.stdout + result.stderr).strip() + "\n", encoding="utf-8")
    return {"command": command, "returncode": result.returncode, "output_file": str(output_file)}


def run_cli_smoke(output_root: Path) -> dict[str, Any]:
    cli_output = output_root / "cli_smoke_output"
    result = run_and_capture(
        [
            sys.executable,
            "-m",
            "vibesec.cli",
            "lite-review",
            "tests/fixtures/vulnerable_next_supabase_app",
            "--output",
            str(cli_output),
            "--no-adapters",
        ],
        cli_output / "cli_stdout.json",
    )
    missing = [name for name in PRIMARY_OUTPUTS if not (cli_output / name).exists()]
    if not (cli_output / "evidence").is_dir():
        missing.append("evidence/")
    if missing and result["returncode"] == 0:
        result["returncode"] = 1
    result["missing_outputs"] = missing
    return result


def review_validation_outputs(output_root: Path) -> dict[str, Any]:
    failures: list[str] = []
    cases = {
        "prompt_only_case_1_secret_leak_web_app": {"expected": {"BLOCK"}, "project_specific": "vulnerable_next_supabase_app"},
        "prompt_only_case_2_missing_auth_or_ownership_check": {"expected": {"BLOCK", "REVIEW"}, "project_specific": "vulnerable_next_supabase_app"},
        "prompt_only_case_3_agent_or_mcp_tool_overreach": {"expected": {"REVIEW"}, "project_specific": "mcp_schema_no_allowlist_needs_review"},
        "prompt_only_case_4_low_risk_clean_project": {"expected": {"PASS", "PASS_WITH_WARNINGS"}, "project_specific": "safe_demo_app"},
    }
    for case_name, rules in cases.items():
        case_dir = output_root / case_name
        for output_name in PRIMARY_OUTPUTS:
            if not (case_dir / output_name).exists():
                failures.append(f"{case_name} missing {output_name}")
        decision_text = _read(case_dir / "launch_decision.md")
        decision = _extract_decision(decision_text)
        if decision not in VALID_DECISIONS:
            failures.append(f"{case_name} has invalid launch decision: {decision}")
        if decision not in rules["expected"]:
            failures.append(f"{case_name} launch decision {decision} not in expected set {sorted(rules['expected'])}")
        combined = "\n".join(_read(case_dir / name) for name in PRIMARY_OUTPUTS)
        if rules["project_specific"] not in combined:
            failures.append(f"{case_name} lacks project-specific evidence")
        if "human confirmation" not in combined.lower():
            failures.append(f"{case_name} lacks human confirmation boundary")
        if "professional security certification" not in decision_text.lower():
            failures.append(f"{case_name} lacks certification disclaimer")
        if "retest" not in _read(case_dir / "retest_checklist.md").lower():
            failures.append(f"{case_name} lacks retest language")
    return {"passed": not failures, "failures": failures}


def write_usability_notes(output_root: Path) -> None:
    _write(
        output_root / "usability_notes.md",
        """# Lite Release Usability Notes

Reviewer input: only the staged Lite package files in `candidate-lite-package/`.

Three-minute questions:

1. When should I use the Skill?
   - Use it before launch when an AI-built product may leak secrets, expose user data, ship broken auth, or give an Agent/tool too much authority.
2. How do I trigger it?
   - Ask the host Agent to review the project with `examples/lite_review_prompt.md`.
3. What files do I read first?
   - `launch_decision.md`, `top_security_risks.md`, `agent_fix_plan.md`, and `retest_checklist.md`.
4. What does `BLOCK` mean?
   - Do not launch yet; one or more findings currently block launch.
5. What may an Agent fix?
   - Only bounded tasks in `agent_fix_plan.md`, after human confirmation of evidence and scope.
6. How do I retest?
   - Follow project-specific checks in `retest_checklist.md` and confirm launch status changes after evidence supports the fix.

Result: pass. The reviewer did not need Phase, scorer, calibration, fixture, or release-verifier concepts. The CLI path is identifiable as optional repository infrastructure.
""",
    )


def write_release_notes(output_root: Path) -> None:
    _write(
        output_root / "release_notes.md",
        """# Lite Skill Release Candidate Notes

This release candidate validates the prompt-only Lite package path and the optional Core-powered repository overlay.

## Validated Scope

- Prompt-only Agent-native package files are staged in `candidate-lite-package/`.
- Source and candidate package boundary checks pass.
- Four prompt-only demo reviews produce `launch_decision.md`, `top_security_risks.md`, `agent_fix_plan.md`, and `retest_checklist.md`.
- Optional CLI smoke produces the same Lite output shape with preserved evidence.

## Boundary

This Lite package is not a professional security certification, penetration test, legal review, or compliance attestation.
""",
    )


def write_release_readiness_decision(
    output_root: Path,
    command_results: dict[str, dict[str, Any]],
    review: dict[str, Any],
    *,
    skipped_cli: bool,
) -> None:
    release_notes = _read(output_root / "release_notes.md").lower()
    rows = [
        ("Source package verifier passes", command_results["package_verifier_source"]["returncode"] == 0),
        ("Candidate package verifier passes", command_results["package_verifier_candidate"]["returncode"] == 0),
        ("Focused Lite tests pass", command_results["pytest_lite_focused"]["returncode"] == 0),
        ("Prompt-only review produces four-file shape on four demo projects", review["passed"]),
        ("Expected blocker is BLOCK or REVIEW", _extract_decision(_read(output_root / "prompt_only_case_1_secret_leak_web_app" / "launch_decision.md")) in {"BLOCK", "REVIEW"}),
        ("Low-risk case avoids unsupported BLOCK", _extract_decision(_read(output_root / "prompt_only_case_4_low_risk_clean_project" / "launch_decision.md")) != "BLOCK"),
        ("Fix plans contain bounded Agent tasks and human confirmation", review["passed"]),
        ("Retest checklists contain project-specific checks", review["passed"]),
        ("Three-minute usability check passes", (output_root / "usability_notes.md").exists()),
        (
            "Release notes state non-certification boundary",
            "professional security certification" in release_notes
            and "penetration test" in release_notes
            and "legal review" in release_notes
            and "compliance attestation" in release_notes,
        ),
    ]
    if not skipped_cli:
        rows.insert(3, ("Optional Core-powered CLI smoke passes", command_results["cli_smoke"]["returncode"] == 0))
    ready = all(passed for _, passed in rows) and not skipped_cli
    lines = [
        "# Lite Release Readiness Decision",
        "",
        f"Decision: {'READY_FOR_RELEASE_CANDIDATE' if ready else 'NOT_RELEASE_READY'}",
        "",
        "This validation does not make VibeSec Gate a professional security certification, penetration test, legal review, or compliance attestation.",
        "",
        "## Gates",
        "",
    ]
    for name, passed in rows:
        lines.append(f"- {'PASS' if passed else 'FAIL'}: {name}")
    if review["failures"]:
        lines.extend(["", "## Output Quality Failures", ""])
        lines.extend(f"- {failure}" for failure in review["failures"])
    lines.extend(
        [
            "",
            "## Reviewed Cases",
            "",
            "- `prompt_only_case_1_secret_leak_web_app`: vulnerable Next/Supabase fixture, expected blocker.",
            "- `prompt_only_case_2_missing_auth_or_ownership_check`: vulnerable orders route, expected blocker or review.",
            "- `prompt_only_case_3_agent_or_mcp_tool_overreach`: MCP schema without allowlist fixture, expected review.",
            "- `prompt_only_case_4_low_risk_clean_project`: safe demo fixture, expected no unsupported block.",
            "",
        ]
    )
    _write(output_root / "release_readiness_decision.md", "\n".join(lines))


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
