from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from vibesec.core.review_schema import validate_review_output_dir  # noqa: E402


def main() -> int:
    os.environ["PYTHONPATH"] = str(SRC)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    checks = [
        ("import vibesec.cli", check_import),
        ("vibesec review --help", check_help),
        ("fixture review output", check_fixture_review),
        ("phase4 review outputs", check_existing_phase4_outputs),
    ]
    failed = False
    for name, fn in checks:
        try:
            detail = fn()
        except Exception as exc:  # noqa: BLE001 - smoke script should report all failures uniformly.
            print(f"FAIL {name}: {exc}")
            failed = True
        else:
            print(f"PASS {name}: {detail}")
    return 1 if failed else 0


def check_import() -> str:
    import vibesec.cli  # noqa: F401

    return "module imported"


def check_help() -> str:
    result = subprocess.run(
        [sys.executable, "-m", "vibesec.cli", "review", "--help"],
        cwd=ROOT,
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or "vibesec review" not in result.stdout:
        raise RuntimeError(result.stderr + result.stdout)
    return "help rendered"


def check_fixture_review() -> str:
    case = ROOT / "tests" / "evaluation_cases" / "review" / "secret_provider_runtime_confirmed"
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "review"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "vibesec.cli",
                "review",
                str(case / "findings.json"),
                "--project",
                str(case),
                "--output",
                str(output),
                "--include-p2",
                "--offline",
                "--reviewer-rule-based",
            ],
            cwd=ROOT,
            env=os.environ.copy(),
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr + result.stdout)
        validate_review_output(output)
    return "fixture output validated"


def check_existing_phase4_outputs() -> str:
    root = ROOT / "test output" / "phase4_review"
    if not root.exists():
        return "phase4_review not present; skipped"
    count = 0
    for output in root.iterdir():
        if output.is_dir():
            validate_review_output(output)
            count += 1
    return f"{count} existing output directories validated"


def validate_review_output(output: Path) -> None:
    required = {
        "ai_review.json",
        "ai_review_summary.md",
        "agent_review_decisions.json",
        "agent_review_decisions.md",
        "human_review_queue.md",
        "llm_review_packet.json",
        "suppression_candidates.json",
        "review_packets.json",
    }
    names = {path.name for path in output.iterdir() if path.is_file()}
    missing = required - names
    if missing:
        raise RuntimeError(f"{output} missing {sorted(missing)}")
    validate_review_output_dir(output)


if __name__ == "__main__":
    raise SystemExit(main())
