from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PHASE11_ROOT = ROOT / "test output" / "phase11_real_host_agent_calibration"
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from compare_host_agent_samples import compare_samples, write_reports  # noqa: E402
from verify_phase11_calibration import REQUIRED_SAMPLE_FILES  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) not in {1, 2}:
        print("usage: py -3 scripts\\import_phase11_host_agent_sample.py <sample_dir> [phase11_root]", file=sys.stderr)
        return 2
    sample_dir = Path(args[0])
    phase_root = Path(args[1]) if len(args) == 2 else DEFAULT_PHASE11_ROOT
    try:
        result = import_host_agent_sample(sample_dir, phase_root)
    except Exception as exc:  # noqa: BLE001 - CLI reports validation failures directly.
        print(f"FAIL import host-agent sample: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def import_host_agent_sample(sample_dir: Path, phase_root: Path) -> dict[str, object]:
    sample_dir = sample_dir.resolve()
    validate_sample_dir(sample_dir)
    metadata = _load_metadata(sample_dir)
    agent = str(metadata["agent"])
    case_id = str(metadata["case_id"])
    destination = phase_root / "host_agent_samples" / agent / case_id
    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(sample_dir, destination)
    samples_root = phase_root / "host_agent_samples"
    matrix = compare_samples(samples_root)
    write_reports(samples_root, matrix)
    return {
        "imported": True,
        "agent": agent,
        "case_id": case_id,
        "destination": str(destination),
        "sample_count": matrix.get("sample_count", 0),
        "agents": matrix.get("agents", []),
    }


def validate_sample_dir(sample_dir: Path) -> None:
    if not sample_dir.exists() or not sample_dir.is_dir():
        raise FileNotFoundError(sample_dir)
    missing = sorted(relative for relative in REQUIRED_SAMPLE_FILES if not (sample_dir / relative).exists())
    if missing:
        raise ValueError(f"sample missing required files: {missing}")
    metadata = _load_metadata(sample_dir)
    required_metadata = {
        "schema_version",
        "agent",
        "case_id",
        "source_packet",
        "generated_by",
        "generated_at",
        "prompt_contract",
        "repository_script_invoked_provider",
    }
    missing_metadata = sorted(key for key in required_metadata if key not in metadata)
    if missing_metadata:
        raise ValueError(f"sample_metadata.json missing required fields: {missing_metadata}")
    if metadata.get("schema_version") != "1.0":
        raise ValueError("sample_metadata.schema_version must be 1.0")
    if metadata.get("repository_script_invoked_provider") is not False:
        raise ValueError("repository_script_invoked_provider must be false")
    agent = metadata.get("agent")
    case_id = metadata.get("case_id")
    if not isinstance(agent, str) or not agent.strip():
        raise ValueError("sample_metadata.agent must be a non-empty string")
    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError("sample_metadata.case_id must be a non-empty string")
    if sample_dir.name != case_id:
        raise ValueError(f"sample directory name {sample_dir.name!r} must match case_id {case_id!r}")
    if sample_dir.parent.name != agent:
        raise ValueError(f"sample parent directory {sample_dir.parent.name!r} must match agent {agent!r}")


def _load_metadata(sample_dir: Path) -> dict[str, object]:
    path = sample_dir / "sample_metadata.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("sample_metadata.json must contain a JSON object")
    return data


if __name__ == "__main__":
    raise SystemExit(main())
