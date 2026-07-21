from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_lite_release_validation import (  # noqa: E402
    HOST_SKILL_READ_COMMAND_PATTERN,
    HOST_WRITE_COMMAND_PATTERN,
    _fixture_sha256,
    _normalized_host_text,
    _skill_tree_sha256,
)


SKILL_SOURCE = ROOT / "skills/vibespec-gate"
TRIGGER_CASES = ROOT / "evals/trigger_cases.yaml"
BEHAVIOR_CASES = ROOT / "evals/behavior_cases.yaml"
TRIGGER_FIXTURE = ROOT / "evals/fixtures/complete-low-risk-static"
EVAL_RUNS_ROOT = ROOT / "evals/runs"
TEST_OUTPUT_ROOT = ROOT / "test output"
EVAL_WORKSPACE_ROOT = TEST_OUTPUT_ROOT / "skill-evals"
INSTALLED_SKILL = Path.home() / ".agents/skills/vibespec-gate"
USER_SKILLS_ROOT = INSTALLED_SKILL.parent
CONFLICTING_USER_SKILLS = (
    "architecture-patterns",
    "using-superpowers",
)
REQUIRED_SKILL_RESOURCES = {
    "references/review-protocol.md",
    "references/evidence-coverage.md",
}
REQUIRED_CHAT_HEADINGS = (
    "Highest-Impact Risks",
    "Missing Evidence",
    "Limitations",
    "Human Confirmation Required",
    "Human-Gated Repair Tasks",
    "Project-Specific Retests",
)
@dataclass(frozen=True)
class EvaluationJob:
    kind: str
    case: dict[str, Any]
    project_root: Path
    source_fixture: Path
    isolated_fixture: Path
    run_root: Path
    artifact_root: Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run fresh Codex-hosted VibeSpec Gate black-box evaluations."
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--model", default="gpt-5.4")
    parser.add_argument("--max-workers", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--codex", default=_find_codex())
    parser.add_argument(
        "--matrix",
        choices=("all", "behavior", "trigger"),
        default="all",
    )
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument(
        "--run-root",
        type=Path,
        help="Trace destination. Defaults to evals/runs/<run-id>.",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        help="Ignored isolated project root. Defaults to test output/skill-evals/<run-id>.",
    )
    args = parser.parse_args()

    if not args.codex:
        parser.error("codex.cmd or codex was not found on PATH")
    if args.max_workers < 1:
        parser.error("--max-workers must be at least 1")
    if args.timeout_seconds < 30:
        parser.error("--timeout-seconds must be at least 30")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", args.run_id):
        parser.error("--run-id must be a filesystem-safe identifier")

    run_root = (args.run_root or EVAL_RUNS_ROOT / args.run_id).resolve()
    workspace_root = (args.workspace_root or EVAL_WORKSPACE_ROOT / args.run_id).resolve()
    _require_new_directory(
        run_root,
        "run root",
        allowed_roots=(EVAL_RUNS_ROOT, TEST_OUTPUT_ROOT),
    )
    _require_new_directory(
        workspace_root,
        "workspace root",
        allowed_roots=(EVAL_WORKSPACE_ROOT,),
    )
    _require_disjoint_directories(run_root, workspace_root)
    _verify_installed_skill()

    trigger_cases = _load_cases(TRIGGER_CASES)
    behavior_cases = _load_cases(BEHAVIOR_CASES)
    selected_ids = set(args.case)
    known_ids = {str(case["id"]) for case in trigger_cases + behavior_cases}
    unknown_ids = selected_ids - known_ids
    if unknown_ids:
        parser.error(f"unknown case id(s): {', '.join(sorted(unknown_ids))}")

    run_root.mkdir(parents=True)
    workspace_root.mkdir(parents=True)
    jobs: list[EvaluationJob] = []
    if args.matrix in {"all", "trigger"}:
        for case in trigger_cases:
            if not selected_ids or case["id"] in selected_ids:
                jobs.append(_prepare_job("trigger", case, run_root, workspace_root))
    if args.matrix in {"all", "behavior"}:
        for case in behavior_cases:
            if not selected_ids or case["id"] in selected_ids:
                jobs.append(_prepare_job("behavior", case, run_root, workspace_root))
    if not jobs:
        parser.error("no cases selected")

    disabled_user_skills = _disabled_user_skills_override()
    host = _codex_version(args.codex)
    started_at = _utc_now()
    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {
            executor.submit(
                _run_job,
                job,
                codex=args.codex,
                model=args.model,
                host=host,
                timeout_seconds=args.timeout_seconds,
                disabled_user_skills=disabled_user_skills,
            ): job
            for job in jobs
        }
        for future in concurrent.futures.as_completed(futures):
            job = futures[future]
            try:
                result = future.result()
            except Exception as exc:  # pragma: no cover - defensive run preservation
                result = _failed_job_record(job, host, exc)
            results.append(result)
            print(f"{result['status']}: {job.case['id']}", flush=True)

    behavior_results = sorted(
        (item for item in results if item["matrix"] == "behavior"),
        key=lambda item: item["id"],
    )
    trigger_results = sorted(
        (item for item in results if item["matrix"] == "trigger"),
        key=lambda item: item["id"],
    )
    behavior_status = _matrix_status(behavior_results, args.matrix in {"all", "behavior"})
    trigger_status = _matrix_status(trigger_results, args.matrix in {"all", "trigger"})
    overall_status = (
        "PASS"
        if behavior_status in {"PASS", "NOT_RUN"}
        and trigger_status in {"PASS", "NOT_RUN"}
        else "FAIL"
    )
    summary = {
        "schema_version": "1.5",
        "run_id": args.run_id,
        "recorded_at_utc": _utc_now(),
        "started_at_utc": started_at,
        "host": host,
        "model": args.model,
        "execution_mode": "fresh codex exec tasks with standard user-level Skill installation",
        "sandbox_mode": "read-only",
        "skill_invocation": "explicit for behavior cases; normal standard-directory routing for trigger cases",
        "user_skill_isolation": "known conflicting user Skills disabled through an ephemeral CLI override; any non-candidate read fails the run",
        "skill_git_commit": _git_head(),
        "skill_tree_sha256": _skill_tree_sha256(SKILL_SOURCE),
        "installed_skill_tree_sha256": _skill_tree_sha256(INSTALLED_SKILL),
        "trace_level": "complete Codex JSONL host events, stderr, unedited final output, and filesystem snapshots",
        "provenance_status": "live host traces captured; release verification still requires an external trusted digest",
        "skill_activation_status": _matrix_status(
            [item for item in results if item.get("activation_status")],
            True,
            field="activation_status",
        ),
        "behavior_semantic_status": _matrix_status(
            behavior_results,
            args.matrix in {"all", "behavior"},
            field="semantic_status",
        ),
        "write_safety_status": _matrix_status(
            results,
            True,
            field="write_safety_status",
        ),
        "user_skill_isolation_status": _matrix_status(
            results,
            True,
            field="user_skill_isolation_status",
        ),
        "behavior_status": behavior_status,
        "trigger_status": trigger_status,
        "overall_status": overall_status,
        "limitations": [
            "The participants are host Agent tasks, not independent human users.",
            "The read-only sandbox and complete command trace establish observed no-write behavior for the isolated case roots; they do not attest to external systems.",
            "Repository records cannot authenticate their own provenance; release approval must bind an external trusted digest to this summary and its evidence files.",
        ],
        "trigger_cases": trigger_results,
        "behavior_cases": behavior_results,
    }
    _write_json(run_root / "summary.json", summary)
    print(f"{overall_status}: {run_root / 'summary.json'}")
    return 0 if overall_status == "PASS" else 1


def _find_codex() -> str:
    return shutil.which("codex.cmd") or shutil.which("codex") or ""


def _require_new_directory(
    path: Path,
    label: str,
    *,
    allowed_roots: tuple[Path, ...],
) -> None:
    if path.exists():
        raise SystemExit(f"{label} already exists; refusing to overwrite: {path}")
    resolved_roots = tuple(root.resolve() for root in allowed_roots)
    if not any(root in path.parents for root in resolved_roots):
        raise SystemExit(f"unsafe {label}: {path}")


def _require_disjoint_directories(first: Path, second: Path) -> None:
    if first == second or first in second.parents or second in first.parents:
        raise SystemExit(
            "run root and workspace root must not overlap: "
            f"run={first}, workspace={second}"
        )


def _load_cases(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases")
    if not isinstance(cases, list) or not all(isinstance(case, dict) for case in cases):
        raise ValueError(f"invalid case matrix: {path}")
    return cases


def _verify_installed_skill() -> None:
    if not INSTALLED_SKILL.is_dir():
        raise SystemExit(f"standard Skill installation is missing: {INSTALLED_SKILL}")
    source_hash = _skill_tree_sha256(SKILL_SOURCE)
    installed_hash = _skill_tree_sha256(INSTALLED_SKILL)
    if source_hash != installed_hash:
        raise SystemExit(
            "installed Skill does not match the candidate: "
            f"source={source_hash}, installed={installed_hash}"
        )


def _disabled_user_skills_override(
    user_skills_root: Path = USER_SKILLS_ROOT,
    candidate: Path = INSTALLED_SKILL,
) -> str:
    candidate_path = candidate.resolve()
    records: list[str] = []
    for skill_name in CONFLICTING_USER_SKILLS:
        skill_md = user_skills_root / skill_name / "SKILL.md"
        if not skill_md.is_file() or skill_md.parent.resolve() == candidate_path:
            continue
        rendered_path = json.dumps(str(skill_md.resolve()))
        records.append(f"{{path={rendered_path},enabled=false}}")
    return f"skills.config=[{','.join(records)}]"


def _prepare_job(
    kind: str,
    case: dict[str, Any],
    run_root: Path,
    workspace_root: Path,
) -> EvaluationJob:
    case_id = str(case["id"])
    project_root = workspace_root / kind / case_id / "project"
    project_root.mkdir(parents=True)
    source_fixture = (
        TRIGGER_FIXTURE if kind == "trigger" else ROOT / str(case["fixture"])
    ).resolve()
    if source_fixture.is_dir():
        shutil.copytree(source_fixture, project_root, dirs_exist_ok=True)
        isolated_fixture = project_root
    elif source_fixture.is_file():
        isolated_fixture = project_root / source_fixture.name
        shutil.copy2(source_fixture, isolated_fixture)
    else:
        raise FileNotFoundError(source_fixture)
    artifact_root = run_root / kind / case_id
    artifact_root.mkdir(parents=True)
    return EvaluationJob(
        kind,
        case,
        project_root,
        source_fixture,
        isolated_fixture,
        run_root,
        artifact_root,
    )


def _run_job(
    job: EvaluationJob,
    *,
    codex: str,
    model: str,
    host: str,
    timeout_seconds: int,
    disabled_user_skills: str,
) -> dict[str, Any]:
    case_id = str(job.case["id"])
    prompt = str(job.case["prompt"])
    before = _snapshot_tree(job.project_root)
    source_hash = _fixture_sha256(job.source_fixture)
    isolated_hash_before = _fixture_sha256(job.isolated_fixture)
    if not source_hash or source_hash != isolated_hash_before:
        raise RuntimeError(f"isolated fixture mismatch before execution: {case_id}")

    final_path = job.artifact_root / "final.md"
    command = [
        codex,
        "exec",
        "--ignore-user-config",
        "-c",
        disabled_user_skills,
        "-m",
        model,
        "--ephemeral",
        "--json",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "-C",
        str(job.project_root),
        "-o",
        str(final_path),
        prompt,
    ]
    executed_at = _utc_now()
    timed_out = False
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
            env=os.environ.copy(),
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = 124
        stdout = _expired_text(exc.stdout)
        stderr = _expired_text(exc.stderr) + f"\nTimed out after {timeout_seconds} seconds.\n"

    host_trace = job.artifact_root / "host-trace.jsonl"
    stderr_path = job.artifact_root / "stderr.log"
    _write_text(host_trace, stdout)
    _write_text(stderr_path, stderr)
    events = _parse_jsonl(stdout)
    task_id = _task_id(events)
    skill_resources = _skill_resources_read(events)
    user_skills_read = _user_skill_names_read(events)
    unexpected_user_skills = sorted(user_skills_read - {"vibespec-gate"})
    activated = REQUIRED_SKILL_RESOURCES.issubset(skill_resources)
    write_events, write_attempts = _write_activity(events)
    after = _snapshot_tree(job.project_root)
    created, modified, deleted = _snapshot_diff(before, after)
    isolated_hash_after = _fixture_sha256(job.isolated_fixture)
    final_output = final_path.read_text(encoding="utf-8") if final_path.is_file() else ""
    trace_path = job.artifact_root / "trace.md"
    _write_text(
        trace_path,
        f"# {case_id}\n\n## Raw Request\n\n{prompt}\n\n"
        f"## Unedited Final Output\n\n{final_output}",
    )

    activation_evidence_path = job.artifact_root / "activation.json"
    activation_evidence = {
        "case_id": case_id,
        "event_type": "host_skill_resource_trace",
        "task_id": task_id,
        "host": host,
        "standard_skill_root": INSTALLED_SKILL.as_posix(),
        "selected_skills": ["vibespec-gate"] if activated else [],
        "skill_resources_read": sorted(skill_resources),
        "user_skills_read": sorted(user_skills_read),
        "unexpected_user_skills_read": unexpected_user_skills,
        "host_trace": _relative_to_run(host_trace, job.run_root),
        "host_trace_sha256": _sha256_file(host_trace),
    }
    _write_json(activation_evidence_path, activation_evidence)

    common = {
        "id": case_id,
        "matrix": job.kind,
        "task_id": task_id,
        "executed_at_utc": executed_at,
        "status": "FAIL",
        "returncode": returncode,
        "timed_out": timed_out,
        "activated": activated,
        "activation_status": "PASS" if activated else "FAIL",
        "activation_source": "host_skill_resource_trace",
        "activation_evidence": _relative_to_run(activation_evidence_path, job.run_root),
        "activation_evidence_sha256": _sha256_file(activation_evidence_path),
        "output": _relative_to_run(trace_path, job.run_root),
        "output_sha256": _sha256_file(trace_path),
        "host_trace": _relative_to_run(host_trace, job.run_root),
        "host_trace_sha256": _sha256_file(host_trace),
        "stderr": _relative_to_run(stderr_path, job.run_root),
        "stderr_sha256": _sha256_file(stderr_path),
        "source_fixture": job.source_fixture.relative_to(ROOT).as_posix(),
        "isolated_fixture": job.isolated_fixture.as_posix(),
        "fixture_sha256_before": source_hash,
        "fixture_sha256_after": isolated_hash_after,
        "files_written": write_events,
        "write_attempts": write_attempts,
        "write_observability": "host_read_only_sandbox_and_event_trace",
        "user_skills_read": sorted(user_skills_read),
        "unexpected_user_skills_read": unexpected_user_skills,
        "user_skill_isolation_status": "PASS" if not unexpected_user_skills else "FAIL",
    }

    write_safe = (
        not write_events
        and not write_attempts
        and not created
        and not modified
        and not deleted
        and source_hash == isolated_hash_after
    )

    if job.kind == "trigger":
        expected = bool(job.case["expected_trigger"])
        passed = (
            returncode == 0
            and not timed_out
            and bool(task_id)
            and activated is expected
            and write_safe
            and not unexpected_user_skills
        )
        common.update(
            {
                "expected_trigger": expected,
                "status": "PASS" if passed else "FAIL",
                "activation_status": "PASS" if activated is expected else "FAIL",
                "write_safety_status": "PASS" if write_safe else "FAIL",
            }
        )
        return common

    integrity_evidence_path = job.artifact_root / "integrity.json"
    integrity_evidence = {
        "case_id": case_id,
        "event_type": "isolated_content_integrity_snapshot",
        "scope": "isolated_case_root",
        "source_fixture": job.source_fixture.relative_to(ROOT).as_posix(),
        "isolated_project_root": job.project_root.as_posix(),
        "fixture_sha256_before": source_hash,
        "fixture_sha256_after": isolated_hash_after,
        "file_sha256_before": before,
        "file_sha256_after": after,
        "net_created_paths": created,
        "net_modified_paths": modified,
        "net_deleted_paths": deleted,
    }
    _write_json(integrity_evidence_path, integrity_evidence)
    write_evidence_path = job.artifact_root / "writes.json"
    write_evidence = {
        "case_id": case_id,
        "event_type": "host_filesystem_write_trace",
        "scope": "isolated_case_root",
        "task_id": task_id,
        "host": host,
        "sandbox_mode": "read-only",
        "host_trace": _relative_to_run(host_trace, job.run_root),
        "host_trace_sha256": _sha256_file(host_trace),
        "writes": write_events,
        "write_attempts": write_attempts,
    }
    _write_json(write_evidence_path, write_evidence)

    decision = _extract_decision(final_output)
    semantic_failures = _semantic_failures(job.case, final_output, decision)
    semantic_status = "PASS" if not semantic_failures else "FAIL"
    status = (
        "PASS"
        if returncode == 0
        and not timed_out
        and bool(task_id)
        and activated
        and semantic_status == "PASS"
        and write_safe
        and not unexpected_user_skills
        else "FAIL"
    )
    common.update(
        {
            "status": status,
            "decision": decision,
            "semantic_status": semantic_status,
            "semantic_failures": semantic_failures,
            "write_safety_status": "PASS" if write_safe else "FAIL",
            "write_evidence": _relative_to_run(write_evidence_path, job.run_root),
            "write_evidence_sha256": _sha256_file(write_evidence_path),
            "integrity_evidence": _relative_to_run(integrity_evidence_path, job.run_root),
            "integrity_evidence_sha256": _sha256_file(integrity_evidence_path),
        }
    )
    return common


def _semantic_failures(case: dict[str, Any], output: str, decision: str) -> list[str]:
    failures: list[str] = []
    if decision not in set(case.get("allowed_decisions", [])):
        failures.append(f"decision {decision or '<missing>'} is not allowed")
    if decision in set(case.get("forbidden_decisions", [])):
        failures.append(f"forbidden decision {decision}")
    for term in case.get("required_terms", []):
        if str(term).lower() not in output.lower():
            failures.append(f"missing required concept: {term}")
    for heading in REQUIRED_CHAT_HEADINGS:
        if not re.search(rf"(?im)^\*{{0,2}}{re.escape(heading)}\*{{0,2}}\s*$", output):
            failures.append(f"missing required heading: {heading}")
    if not re.search(r"(?im)^Coverage:\s*(complete|partial|insufficient|truncated)\b", output):
        failures.append("missing canonical Coverage line")
    if not re.search(r"(?im)^Decision:\s*(BLOCK|REVIEW|PASS_WITH_WARNINGS|PASS)\b", output):
        failures.append("missing canonical Decision line")
    if case.get("id") == "behavior-complete-low-risk":
        for surface in (
            "auth",
            "authorization",
            "secrets",
            "data_rules",
            "deployment",
            "agent_tools",
            "desktop_ipc",
        ):
            if surface not in output.lower():
                failures.append(f"missing coverage surface: {surface}")
    return failures


def _parse_jsonl(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _task_id(events: list[dict[str, Any]]) -> str:
    for event in events:
        if event.get("type") == "thread.started" and isinstance(event.get("thread_id"), str):
            return str(event["thread_id"])
    return ""


def _skill_resources_read(
    events: list[dict[str, Any]],
    *,
    skill_root: Path = INSTALLED_SKILL,
    skill_source: Path = SKILL_SOURCE,
) -> set[str]:
    resources: set[str] = set()
    installed = _normalize_windows_command(str(skill_root)).lower()
    for event in events:
        item = event.get("item")
        if (
            not isinstance(item, dict)
            or item.get("type") != "command_execution"
            or item.get("status") != "completed"
            or item.get("exit_code") != 0
        ):
            continue
        command = _normalize_windows_command(str(item.get("command", ""))).lower()
        if installed not in command or not HOST_SKILL_READ_COMMAND_PATTERN.search(command):
            continue
        for resource in REQUIRED_SKILL_RESOURCES:
            windows_resource = resource.replace("/", "\\").lower()
            source_path = skill_source / resource
            if (
                f"{installed}\\{windows_resource}" in command
                and source_path.is_file()
                and _normalized_host_text(item.get("aggregated_output"))
                == _normalized_host_text(source_path.read_text(encoding="utf-8"))
            ):
                resources.add(resource)
    return resources


def _normalize_windows_command(value: str) -> str:
    normalized = value.replace("/", "\\")
    while "\\\\" in normalized:
        normalized = normalized.replace("\\\\", "\\")
    return normalized


def _user_skill_names_read(
    events: list[dict[str, Any]],
    *,
    user_skills_root: Path = USER_SKILLS_ROOT,
) -> set[str]:
    names: set[str] = set()
    prefix = _normalize_windows_command(str(user_skills_root)).lower().rstrip("\\") + "\\"
    for event in events:
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") != "command_execution":
            continue
        command = _normalize_windows_command(str(item.get("command", ""))).lower()
        offset = 0
        while (index := command.find(prefix, offset)) >= 0:
            remainder = command[index + len(prefix) :]
            name = remainder.split("\\", 1)[0].strip("'\"")
            if name:
                names.add(name)
            offset = index + len(prefix)
    return names


def _write_activity(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    writes: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    for event in events:
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type", ""))
        if item_type in {"file_change", "apply_patch"}:
            record = {"type": item_type, "status": item.get("status")}
            (writes if item.get("status") == "completed" else attempts).append(record)
            continue
        if item_type != "command_execution":
            continue
        command = str(item.get("command", ""))
        if not HOST_WRITE_COMMAND_PATTERN.search(command):
            continue
        record = {
            "type": "command_execution",
            "command": command,
            "status": item.get("status"),
            "exit_code": item.get("exit_code"),
        }
        if item.get("status") == "completed" and item.get("exit_code") == 0:
            writes.append(record)
        else:
            attempts.append(record)
    return writes, attempts


def _snapshot_tree(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise RuntimeError(f"unsafe linked fixture entry: {path}")
        if path.is_dir():
            snapshot[f"{relative}/"] = "directory"
        elif path.is_file():
            snapshot[relative] = _sha256_file(path)
        else:
            raise RuntimeError(f"unsupported fixture entry: {path}")
    return snapshot


def _snapshot_diff(
    before: dict[str, str], after: dict[str, str]
) -> tuple[list[str], list[str], list[str]]:
    created = sorted(set(after) - set(before))
    deleted = sorted(set(before) - set(after))
    modified = sorted(path for path in set(before) & set(after) if before[path] != after[path])
    return created, modified, deleted


def _extract_decision(text: str) -> str:
    match = re.search(
        r"(?im)^Decision:\s*(BLOCK|REVIEW|PASS_WITH_WARNINGS|PASS)\b",
        text,
    )
    return match.group(1).upper() if match else ""


def _matrix_status(
    records: list[dict[str, Any]],
    expected: bool,
    *,
    field: str = "status",
) -> str:
    if not expected:
        return "NOT_RUN"
    return "PASS" if records and all(item.get(field) == "PASS" for item in records) else "FAIL"


def _failed_job_record(job: EvaluationJob, host: str, exc: Exception) -> dict[str, Any]:
    error_path = job.artifact_root / "runner-error.txt"
    _write_text(error_path, f"{type(exc).__name__}: {exc}\n")
    return {
        "id": str(job.case["id"]),
        "matrix": job.kind,
        "status": "FAIL",
        "activation_status": "FAIL",
        "semantic_status": "FAIL" if job.kind == "behavior" else "NOT_RUN",
        "write_safety_status": "FAIL" if job.kind == "behavior" else "NOT_RUN",
        "host": host,
        "runner_error": _relative_to_run(error_path, job.run_root),
        "runner_error_sha256": _sha256_file(error_path),
    }


def _relative_to_run(path: Path, run_root: Path) -> str:
    return path.relative_to(run_root).as_posix()


def _codex_version(codex: str) -> str:
    completed = subprocess.run(
        [codex, "--version"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    version = completed.stdout.strip() or completed.stderr.strip()
    return f"Codex CLI ({version})"


def _git_head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    value = completed.stdout.strip()
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else ""


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = value if value.endswith("\n") else value + "\n"
    path.write_text(rendered, encoding="utf-8", newline="\n")


def _expired_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
