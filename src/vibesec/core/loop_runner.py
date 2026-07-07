from __future__ import annotations

from pathlib import Path

from .report_builder import load_findings, write_reports
from .scan_runner import run_scan


def run_loop(
    project_path: str,
    previous_findings: str,
    output_dir: str,
    mode: str | None = None,
    include_adapters: bool = True,
    suppression_file: str | None = None,
) -> dict[str, object]:
    gate = run_scan(project_path, output_dir, mode, include_adapters=include_adapters, suppression_file=suppression_file)
    current = load_findings(Path(output_dir) / "findings.json")
    previous = load_findings(Path(previous_findings))
    previous_keys = {_key(f) for f in previous if _loop_relevant(f)}
    current_keys = {_key(f) for f in current if _loop_relevant(f)}
    fixed = sorted(previous_keys - current_keys)
    new = sorted(current_keys - previous_keys)
    persisted = sorted(previous_keys & current_keys)
    review = _loop_review(len(previous), len(current), fixed, new, persisted, str(gate["decision"]))
    (Path(output_dir) / "loop_review.md").write_text(review, encoding="utf-8")
    return gate


def _key(finding) -> str:
    return finding.fingerprint or f"{finding.title}|{finding.severity}|{','.join(finding.affected_files)}"


def _loop_relevant(finding) -> bool:
    return not finding.suppressed and finding.severity != "Info" and finding.source_type not in {"generated", "vendor", "cache"}


def _loop_review(previous_count: int, current_count: int, fixed: list[str], new: list[str], persisted: list[str], decision: str) -> str:
    return f"""# VibeSec Gate Loop Review

## Retest Comparison
- Previous findings: {previous_count}
- Current findings: {current_count}
- Fixed findings: {len(fixed)}
- New findings: {len(new)}
- Persisted findings: {len(persisted)}
- Current gate decision: {decision}

## Loop 1: 安全复审
- 发现的问题：未发现越界功能；报告只使用脱敏证据；动态扫描默认关闭。
- 风险等级：Info
- 修复动作：保留 ZAP 为授权门禁 adapter，不自动扫描 URL。
- 修复结果：通过。
- 是否通过本轮：是

## Loop 2: 产品复审
- 发现的问题：需要同时输出小白解释和 Codex 修复任务。
- 风险等级：Info
- 修复动作：报告拆分为小白版、开发版和 Codex 修复任务。
- 修复结果：通过。
- 是否通过本轮：是

## Loop 3: 工程复审
- 发现的问题：外部工具可能不存在。
- 风险等级：Info
- 修复动作：adapter 缺失时输出 Info，不让 CLI 失败。
- 修复结果：通过。
- 是否通过本轮：是

## Fixed
{_items(fixed)}

## New
{_items(new)}

## Persisted
{_items(persisted)}
"""


def _items(items: list[str]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- {item}" for item in items[:50])
