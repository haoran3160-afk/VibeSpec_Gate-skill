from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from .core.gate_decision import decide_gate
from .core.llm_output_schema import validate_llm_review_outputs
from .core.lite_review_bundle import build_lite_review_bundle
from .core.loop_runner import run_loop
from .core.path_safety import require_disjoint_paths
from .core.project_intake import detect_profile
from .core.report_builder import load_findings, write_reports
from .core.review_runner import run_review
from .core.review_schema import SchemaValidationError, validate_review_output_dir
from .core.scan_runner import run_scan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vibespec-gate", description="VibeSpec Gate defensive launch security scanner.")
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
    scan.add_argument("--suppressions", default=None, help="Path to vibespec_gate.suppressions.json.")

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
    loop.add_argument("--suppressions", default=None, help="Path to vibespec_gate.suppressions.json.")

    review = sub.add_parser("review", help="Build offline AI-assisted review packets and a human review queue.")
    review.add_argument("findings")
    review.add_argument("--project", required=True)
    review.add_argument("--output", required=True)
    review.add_argument("--max-snippet-lines", type=int, default=80)
    review.add_argument("--include-p2", action="store_true", help="Include P2 findings in addition to P0/P1.")
    review.add_argument("--offline", action="store_true", default=True, help="Offline mode; external APIs are never called.")
    review.add_argument("--reviewer-rule-based", action="store_true", default=True, help="Use the local deterministic reviewer.")
    review.add_argument("--model-provider", choices=["none"], default="none", help="Reserved; Phase 4 supports only none.")

    review_validate = sub.add_parser("review-validate", help="Validate VibeSpec review output JSON files.")
    review_validate.add_argument("review_output_dir")

    llm_output_validate = sub.add_parser("llm-output-validate", help="Validate LLM-native review output files.")
    llm_output_validate.add_argument("workspace_or_output_dir")

    lite_review = sub.add_parser("lite-review", help="Build a Lite launch-review bundle from a project or existing review output.")
    lite_review.add_argument("target", help="Project directory, or an existing review output directory.")
    lite_review.add_argument("--output", default=None, help="Bundle directory. Required for project targets; must not overlap the input.")
    lite_review.add_argument("--mode", choices=mode_choices, default=None)
    lite_review.add_argument("--no-adapters", action="store_true", help="Skip external tool adapter status checks during project scans.")
    lite_review.add_argument("--suppressions", default=None, help="Path to vibespec_gate.suppressions.json for project scans.")
    lite_review.add_argument("--max-snippet-lines", type=int, default=80)
    lite_review.add_argument("--p1-only", action="store_true", help="Only include P0/P1 findings in the internal review step.")
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
    if args.command == "llm-output-validate":
        try:
            result = validate_llm_review_outputs(args.workspace_or_output_dir)
        except SchemaValidationError as exc:
            print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False, indent=2))
            return 1
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "lite-review":
        try:
            target = Path(args.target).resolve()
            if not target.is_dir():
                raise ValueError("lite-review target must be an existing directory")
            if (target / "agent_review_decisions.json").exists():
                result = build_lite_review_bundle(
                    target,
                    Path(args.output) if args.output else None,
                )
            else:
                if not args.output:
                    raise ValueError("--output is required when lite-review targets a project directory")
                target, bundle_dir = require_disjoint_paths(
                    target,
                    args.output,
                    first_label="project",
                    second_label="output",
                )
                if bundle_dir.exists():
                    raise ValueError(f"output already exists: {bundle_dir}")
                bundle_dir.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(prefix="vibespec-gate-lite-", dir=bundle_dir.parent) as temporary:
                    staging = Path(temporary)
                    scan_output = staging / "scan"
                    review_output = staging / "review_output"
                    scan_summary = run_scan(
                        str(target),
                        str(scan_output),
                        args.mode,
                        include_adapters=not args.no_adapters,
                        suppression_file=args.suppressions,
                    )
                    review_summary = run_review(
                        str(scan_output / "findings.json"),
                        str(target),
                        str(review_output),
                        max_snippet_lines=args.max_snippet_lines,
                        include_p2=not args.p1_only,
                        offline=True,
                        reviewer_rule_based=True,
                    )
                    staging_bundle = staging / "bundle"
                    lite_result = build_lite_review_bundle(review_output, staging_bundle)
                    evidence_dir = staging_bundle / "evidence"
                    shutil.copytree(scan_output, evidence_dir / "scan")
                    shutil.copytree(review_output, evidence_dir / "review_output")
                    bundle_dir.parent.mkdir(parents=True, exist_ok=True)
                    staging_bundle.rename(bundle_dir)
                    lite_result["bundle_dir"] = str(bundle_dir)
                    lite_result["primary_outputs"] = [
                        str(bundle_dir / Path(path).name) for path in lite_result["primary_outputs"]
                    ]
                    lite_result["evidence_files"] = [
                        str(bundle_dir / "evidence" / Path(path).name) for path in lite_result["evidence_files"]
                    ]
                    lite_result["review_output"] = str(bundle_dir / "evidence" / "review_output")
                result = {
                    "scan": scan_summary,
                    "review": review_summary,
                    "lite": lite_result,
                }
        except Exception as exc:  # noqa: BLE001 - CLI should report validation/shape failures directly.
            print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
            return 1
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
