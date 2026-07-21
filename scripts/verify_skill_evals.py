from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_lite_release_validation import (  # noqa: E402
    SKILL_EVAL_SUMMARY,
    TRUSTED_EVAL_SHA256_ENV,
    _skill_eval_passed,
)


def main() -> int:
    if _skill_eval_passed(SKILL_EVAL_SUMMARY):
        print(f"PASS Skill evaluation readiness: {SKILL_EVAL_SUMMARY}")
        return 0
    if not os.environ.get(TRUSTED_EVAL_SHA256_ENV):
        print(
            f"FAIL trusted provenance is missing: set {TRUSTED_EVAL_SHA256_ENV} "
            "to the externally observed summary SHA256"
        )
    print(f"FAIL Skill evaluation readiness: {SKILL_EVAL_SUMMARY}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
