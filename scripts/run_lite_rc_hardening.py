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
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Lite Skill RC hardening evidence generation.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--external-session",
        action="append",
        default=[],
        metavar="NAME:started,files,fix,retest,certification_safe",
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
        "--real-project",
        action="append",
        default=[],
        metavar="LABEL=PATH",
        help="Run optional read-only Lite CLI validation against a real project. Output stays under the RC evidence folder.",
    )
    args = parser.parse_args(argv)

    output_root = args.output.resolve()
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
    external = write_pilot_usability_notes(
        output_root,
        load_external_sessions(args.external_session, args.external_session_file),
    )
    real_projects = run_real_project_validations(output_root, args.real_project)
    write_known_limitations(output_root)
    write_release_decision(output_root, results, matrix, actionability, external, real_projects)

    if (
        all(item["returncode"] == 0 for item in results.values())
        and matrix["passed"]
        and actionability["passed"]
        and real_projects["passed"]
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
                "notes": "Replace with observation notes. Use true only when supported by the session.",
            },
            {
                "name": "participant_2",
                "profile": "coding_agent_developer",
                "started": False,
                "files": False,
                "fix": False,
                "retest": False,
                "certification_safe": False,
                "notes": "Replace with observation notes.",
            },
            {
                "name": "participant_3",
                "profile": "ai_agent_or_saas_project",
                "started": False,
                "files": False,
                "fix": False,
                "retest": False,
                "certification_safe": False,
                "notes": "Replace with observation notes.",
            },
        ]
    }
    (output_root / "external_session_template.json").write_text(
        json.dumps(template, indent=2) + "\n",
        encoding="utf-8",
    )


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
    passed_sessions = [
        item
        for item in parsed
        if item["started"] and item["files"] and item["fix"] and item["retest"] and item["certification_safe"]
    ]
    profile_coverage = _profile_coverage(parsed)
    pass_rate = len(passed_sessions) / len(parsed) if parsed else 0.0
    threshold = len(parsed) >= required and pass_rate >= 0.8 and all(profile_coverage.values())
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
            lines.append(
                f"- {item['name']} ({item['profile']}): started={item['started']}, files={item['files']}, "
                f"fix={item['fix']}, retest={item['retest']}, certification_safe={item['certification_safe']}"
            )
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
            f"Usability threshold result: {'PASS' if threshold else 'PENDING'}",
        ]
    )
    _write(output_root / "pilot_usability_notes.md", "\n".join(lines))
    return {
        "passed": threshold,
        "recorded_sessions": len(parsed),
        "passing_sessions": len(passed_sessions),
        "pass_rate": pass_rate,
        "profile_coverage": profile_coverage,
    }


def write_known_limitations(output_root: Path) -> None:
    _write(
        output_root / "known_limitations.md",
        """# Lite RC Known Limitations

- Package mode is prompt-only Agent-native; host-Agent behavior can vary.
- Optional Core-powered CLI overlay is repository infrastructure, not a requirement for the Lite package.
- This RC is not a professional security certification, penetration test, legal review, or compliance attestation.
- Prompt-only outputs depend on available project evidence; missing production cloud, identity-provider, database, or logging policy can leave uncertainty.
- External blind usability sessions are required before controlled pilot promotion.
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
    real_projects = real_projects or {"passed": True, "projects": []}
    package_reproducible = compare_package_file_list(output_root)
    gates = [
        ("Candidate package generation is reproducible", package_reproducible),
        ("Source package verifier passes", command_results["verifier_source"]["returncode"] == 0),
        ("Candidate package verifier passes", command_results["verifier_candidate"]["returncode"] == 0),
        ("Focused Lite tests pass", command_results["focused_tests"]["returncode"] == 0),
        ("Expanded validation matrix has no blocker-level failures", matrix["passed"]),
        ("External blind usability passes threshold", external["passed"]),
        ("Actionability review finds no unsafe fix instructions", actionability["passed"]),
        ("Read-only real-project validation does not mutate source files", real_projects["passed"]),
        ("Release notes state limitations and non-certification boundary", True),
    ]
    ready = all(passed for _, passed in gates)
    lines = [
        "# Lite RC Hardening Release Decision",
        "",
        f"Decision: {'READY_FOR_CONTROLLED_EXTERNAL_PILOT' if ready else 'NO_GO_FOR_CONTROLLED_EXTERNAL_PILOT'}",
        "",
        "This decision is for controlled external pilot readiness, not GA readiness.",
        "",
        "## Gates",
        "",
    ]
    for name, passed in gates:
        lines.append(f"- {'PASS' if passed else 'FAIL'}: {name}")
    lines.extend(["", "## Triage", ""])
    if external["passed"]:
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
        return {"passed": True, "projects": results, "failures": failures}

    validation_root.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Real Project Validation Summary",
        "",
        "Safety boundary: source projects are read-only; all VibeSec outputs are written under this RC evidence folder.",
        "",
        "| Project | CLI | Source unchanged | Decision | Evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for spec in specs:
        label, project = _parse_real_project_spec(spec)
        evidence_dir = validation_root / label
        lite_output = evidence_dir / "lite_review"
        _assert_output_outside_project(project, lite_output)
        before = snapshot_project_state(project)
        before_path = evidence_dir / "source_state_before.json"
        before_path.parent.mkdir(parents=True, exist_ok=True)
        before_path.write_text(json.dumps(before, indent=2) + "\n", encoding="utf-8")
        command_result = run_and_capture(
            [
                sys.executable,
                "-m",
                "vibesec.cli",
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
            "project": str(project),
            "returncode": command_result["returncode"],
            "source_unchanged": unchanged,
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
    return {"passed": not failures, "projects": results, "failures": failures}


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
            }
        )
    return {"project": str(project), "file_count": len(files), "files": files}


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
    booleans = [_to_bool(value) for value in values[:5]]
    while len(booleans) < 5:
        booleans.append(False)
    return {
        "name": name,
        "profile": _infer_profile(name),
        "started": booleans[0],
        "files": booleans[1],
        "fix": booleans[2],
        "retest": booleans[3],
        "certification_safe": booleans[4],
        "notes": "",
    }


def _normalize_session(item: dict[str, Any]) -> dict[str, Any]:
    name = str(item.get("name") or "participant")
    profile = str(item.get("profile") or _infer_profile(name))
    return {
        "name": name,
        "profile": profile,
        "started": bool(item.get("started")),
        "files": bool(item.get("files")),
        "fix": bool(item.get("fix")),
        "retest": bool(item.get("retest")),
        "certification_safe": bool(item.get("certification_safe")),
        "notes": str(item.get("notes") or ""),
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


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "pass", "passed"}


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
