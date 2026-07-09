from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from vibespec_gate.core.llm_output_schema import validate_llm_review_outputs  # noqa: E402
from vibespec_gate.core.review_schema import SchemaValidationError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    allow_stub = True
    if "--final" in args:
        args = [arg for arg in args if arg != "--final"]
        allow_stub = False
    if len(args) != 1:
        print("usage: py -3 scripts\\validate_llm_review_outputs.py <workspace-or-output-dir> [--final]", file=sys.stderr)
        return 2
    try:
        result = validate_llm_review_outputs(args[0], allow_stub=allow_stub)
    except SchemaValidationError as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
