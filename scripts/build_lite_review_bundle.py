from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from vibespec_gate.core.lite_review_bundle import build_lite_review_bundle  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) not in {1, 2}:
        print("usage: py -3 scripts\\build_lite_review_bundle.py <review_output_dir> [bundle_dir]", file=sys.stderr)
        return 2
    review_output = Path(args[0])
    bundle_dir = Path(args[1]) if len(args) == 2 else review_output / "lite_review"
    try:
        result = build_lite_review_bundle(review_output, bundle_dir)
    except Exception as exc:  # noqa: BLE001 - CLI should report validation/shape failures directly.
        print(f"FAIL build lite review bundle: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
