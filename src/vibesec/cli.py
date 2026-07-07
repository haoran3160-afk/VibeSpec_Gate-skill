from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core.gate_decision import decide_gate
from .core.loop_runner import run_loop
from .core.project_intake import detect_profile
from .core.report_builder import load_findings, write_reports
from .core.review_runner import run_review
from .core.review_schema import SchemaValidationError, validate_review_output_dir
from .core.scan_runner import run_scan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vibesec", description="VibeSec Gate defensive launch security scanner.")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Scan a local user-owned project.")
    scan.add_argument("project")
    mode_choices = [
        "demo",
        "web-app",
        "saas",
        "ai-agent",
        "admin",
        "llm-app",
        "desktop",
        "vscode-extension",
        "cli",
        "mcp",
    ]
    scan.add_argument("--mode", choices=mode_choices, default=None)
    scan.add_argument("--output", default="outputs")
    scan.add_argument("--no-adapters", action="store_true", help="Skip external tool adapter status checks.")
    scan.add_argument("--suppressions", default=None, help="Path to vibesec.suppressions.json.")

    report = sub.add_parser("report", help="Rebuild reports from findings.json.")
    report.add_argument("findings")
    report.add_argument("--project", default=".")
    report.add_argument("--output", default="outputs")

    gate = sub.add_parser("gate", help="Print gate decision from findings.json.")
    gate.add_argument("findings")
    gate.add_argument("--project", default=".")

    loop = sub.add_parser("loop", help="Run scan and compare to previous findings.")
    loop.add_argument("project")
    loop.add_argument("--previous", required=True)
    loop.add_argument("--mode", choices=mode_choices, default=None)
    loop.add_argument("--output", default="outputs")
    loop.add_argument("--no-adapters", action="store_true", help="Skip external tool adapter status checks.")
    loop.add_argument("--suppressions", default=None, help="Path to vibesec.suppressions.json.")

    review = sub.add_parser("review", help="Build offline AI-assisted review packets and a human review queue.")
    review.add_argument("findings")
    review.add_argument("--project", required=True)
    review.add_argument("--output", required=True)
    review.add_argument("--max-snippet-lines", type=int, default=80)
    review.add_argument("--include-p2", action="store_true", help="Include P2 findings in addition to P0/P1.")
    review.add_argument("--offline", action="store_true", default=True, help="Offline mode; external APIs are never called.")
    review.add_argument("--reviewer-rule-based", action="store_true", default=True, help="Use the local deterministic reviewer.")
    review.add_argument("--model-provider", choices=["none"], default="none", help="Reserved; Phase 4 supports only none.")

    review_validate = sub.add_parser("review-validate", help="Validate VibeSec review output JSON files.")
    review_validate.add_argument("review_output_dir")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "scan":
        summary = run_scan(
            args.project,
            args.output,
            args.mode,
            include_adapters=not args.no_adapters,
            suppression_file=args.suppressions,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if args.command == "report":
        findings = load_findings(Path(args.findings))
        profile = detect_profile(args.project)
        summary = write_reports(Path(args.output), profile, findings)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if args.command == "gate":
        findings = load_findings(Path(args.findings))
        profile = detect_profile(args.project)
        print(json.dumps(decide_gate(findings, profile), ensure_ascii=False, indent=2))
        return 0
    if args.command == "loop":
        summary = run_loop(
            args.project,
            args.previous,
            args.output,
            args.mode,
            include_adapters=not args.no_adapters,
            suppression_file=args.suppressions,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if args.command == "review":
        try:
            summary = run_review(
                args.findings,
                args.project,
                args.output,
                max_snippet_lines=args.max_snippet_lines,
                include_p2=args.include_p2,
                offline=args.offline,
                reviewer_rule_based=args.reviewer_rule_based,
            )
        except SchemaValidationError as exc:
            print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
            return 1
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if args.command == "review-validate":
        try:
            result = validate_review_output_dir(args.review_output_dir)
        except SchemaValidationError as exc:
            print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False, indent=2))
            return 1
        print(json.dumps({"valid": True, **result}, ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
