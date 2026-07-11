from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from build_evaluation_matrix import DOMAINS, build_matrix  # noqa: E402
from build_llm_quality_matrix import build_matrix as build_llm_quality_matrix  # noqa: E402


PHASE4_OUTPUTS = [
    ROOT / "test output" / "phase4_review" / "personal-voice-light-agent",
    ROOT / "test output" / "phase4_review" / "personal-claude-ipc-mcp",
    ROOT / "test output" / "phase4_review" / "agent-programs-file-manager",
]
MATRIX_PATH = ROOT / "test output" / "phase7_release_hardening" / "evaluation_matrix.json"
LLM_QUALITY_MATRIX_PATH = ROOT / "test output" / "phase9_real_llm_review_evaluation" / "llm_quality_matrix.json"


def main() -> int:
    os.environ["PYTHONPATH"] = str(SRC)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    checks: list[tuple[str, Callable[[], str]]] = [
        ("phase4/5 smoke", lambda: run_command([sys.executable, "scripts/verify_phase4_5_smoke.py"])),
        ("pytest", lambda: run_command([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"])),
        ("compileall", lambda: run_command([sys.executable, "-m", "compileall", "-q", "src", "tests", "scripts"])),
        ("Lite package manifest", lambda: run_command([sys.executable, "scripts/verify_lite_package.py"])),
        ("release metadata", lambda: run_command([sys.executable, "scripts/verify_release_metadata.py"])),
        ("Lite archive build", lambda: run_command([sys.executable, "scripts/build_lite_package_zip.py"])),
        (
            "Lite archive metadata",
            lambda: run_command(
                [sys.executable, "scripts/verify_release_metadata.py", "--archive", "dist/vibespec-gate-lite.zip"]
            ),
        ),
        ("Lite release validation", lambda: run_command([sys.executable, "scripts/run_lite_release_validation.py"])),
        ("Lite RC hardening evidence", lambda: run_command([sys.executable, "scripts/run_lite_rc_hardening.py"])),
        ("review-validate personal-voice-light-agent", lambda: review_validate(PHASE4_OUTPUTS[0])),
        ("review-validate personal-claude-ipc-mcp", lambda: review_validate(PHASE4_OUTPUTS[1])),
        ("review-validate agent-programs-file-manager", lambda: review_validate(PHASE4_OUTPUTS[2])),
        ("evaluation matrix coverage", check_evaluation_matrix),
        ("LLM quality matrix coverage", check_llm_quality_matrix),
        ("git hygiene", check_git_hygiene),
    ]
    failed = False
    for name, fn in checks:
        try:
            detail = fn()
        except Exception as exc:  # noqa: BLE001 - release verifier should report every check uniformly.
            print(f"FAIL {name}: {exc}")
            failed = True
        else:
            print(f"PASS {name}: {detail}")
    return 1 if failed else 0


def run_command(command: list[str]) -> str:
    result = subprocess.run(command, cwd=ROOT, env=os.environ.copy(), text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError((result.stderr + result.stdout).strip())
    last_line = [line for line in (result.stdout + result.stderr).splitlines() if line.strip()]
    return last_line[-1] if last_line else "ok"


def review_validate(output: Path) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "vibespec_gate.cli", "review-validate", str(output)],
        cwd=ROOT,
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr + result.stdout).strip())
    data = json.loads(result.stdout)
    if not data.get("valid"):
        raise RuntimeError(result.stdout)
    return f"{data['packets']} packets, {data['agent_decisions']} decisions"


def check_evaluation_matrix() -> str:
    if not MATRIX_PATH.exists():
        raise RuntimeError(f"missing {MATRIX_PATH}")
    expected = build_matrix()
    actual = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    expected_cases = {case["case_id"]: case for case in expected["cases"]}
    actual_cases = {case["case_id"]: case for case in actual.get("cases", [])}
    if actual.get("schema_version") != "1.0":
        raise RuntimeError("evaluation_matrix.schema_version must be 1.0")
    if set(actual_cases) != set(expected_cases):
        raise RuntimeError("evaluation_matrix cases do not match review fixtures")
    missing_domains = [
        item["domain"]
        for item in actual.get("domains", [])
        if item["domain"] in DOMAINS and int(item.get("case_count", 0)) <= 0
    ]
    if missing_domains:
        raise RuntimeError(f"domains without coverage: {missing_domains}")
    for case_id, expected_case in expected_cases.items():
        actual_case = actual_cases[case_id]
        for key in (
            "expected_verdict",
            "expected_action",
            "expected_agent_next_step",
            "expected_decision_type",
            "expected_must_review",
        ):
            if actual_case.get(key) != expected_case[key]:
                raise RuntimeError(f"{case_id}.{key} mismatch")
    return f"{actual['total_cases']} cases across {len(DOMAINS)} domains"


def check_llm_quality_matrix() -> str:
    if not LLM_QUALITY_MATRIX_PATH.exists():
        raise RuntimeError(f"missing {LLM_QUALITY_MATRIX_PATH}")
    expected = build_llm_quality_matrix()
    actual = json.loads(LLM_QUALITY_MATRIX_PATH.read_text(encoding="utf-8"))
    expected_cases = {case["case_id"]: case for case in expected["cases"]}
    actual_cases = {case["case_id"]: case for case in actual.get("cases", [])}
    if actual.get("schema_version") != "1.1":
        raise RuntimeError("llm_quality_matrix.schema_version must be 1.1")
    if actual.get("total_cases") != 12:
        raise RuntimeError("llm_quality_matrix.total_cases must be 12")
    if actual.get("expectations_failed") != 0:
        raise RuntimeError("llm_quality_matrix has unmet expectations")
    if set(actual_cases) != set(expected_cases):
        raise RuntimeError("llm_quality_matrix cases do not match LLM output fixtures")
    for case_id, expected_case in expected_cases.items():
        actual_case = actual_cases[case_id]
        for key in ("expected_launch_decision", "actual_launch_decision", "score", "actual_pass", "expected_pass", "expectation_met"):
            if actual_case.get(key) != expected_case[key]:
                raise RuntimeError(f"{case_id}.{key} mismatch")
    return f"{actual['expectations_met']}/{actual['total_cases']} LLM output fixture expectations met"


def check_git_hygiene() -> str:
    ignored_paths = [
        ".pytest_cache",
        "outputs",
        "test output/phase4_review",
        "test output/phase3_regression",
        "tests/fixtures/vulnerable_next_supabase_app/.env.local",
    ]
    for path in ignored_paths:
        result = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"{path} is not ignored")
    curated_fixture = "tests/evaluation_cases/llm_outputs/secret_runtime_block/outputs/nontechnical_user_summary.md"
    if not (ROOT / curated_fixture).exists():
        raise RuntimeError(f"missing curated quality fixture: {curated_fixture}")
    ignored_fixture = subprocess.run(
        ["git", "check-ignore", "-q", curated_fixture], cwd=ROOT, text=True, capture_output=True, check=False
    )
    if ignored_fixture.returncode == 0:
        raise RuntimeError(f"curated quality fixture must not be ignored: {curated_fixture}")
    cached = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True, capture_output=True, check=False)
    if cached.returncode != 0:
        raise RuntimeError(cached.stderr.strip())
    return "cache/env/generated outputs ignored; staged file list inspected"


if __name__ == "__main__":
    raise SystemExit(main())
