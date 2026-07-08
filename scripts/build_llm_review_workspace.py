from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from vibesec.core.llm_review_workspace import build_llm_review_workspace  # noqa: E402
from vibesec.core.review_schema import SchemaValidationError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: py -3 scripts\\build_llm_review_workspace.py <review_output_dir>", file=sys.stderr)
        return 2
    try:
        result = build_llm_review_workspace(args[0])
    except SchemaValidationError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

