from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_lite_release_validation import SKILL_EVAL_SUMMARY, _skill_eval_passed  # noqa: E402


def main() -> int:
    if _skill_eval_passed(SKILL_EVAL_SUMMARY):
        print(f"PASS Skill evaluation readiness: {SKILL_EVAL_SUMMARY}")
        return 0
    print(f"FAIL Skill evaluation readiness: {SKILL_EVAL_SUMMARY}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
