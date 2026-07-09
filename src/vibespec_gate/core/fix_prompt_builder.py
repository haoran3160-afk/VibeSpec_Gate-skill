from __future__ import annotations


def build_fix_prompt(
    title: str,
    risk: str,
    files: list[str],
    fix: str,
    tests: list[str],
    confidence: str = "confirmed",
    source_type: str = "runtime",
    category: str = "",
) -> str:
    file_list = "\n".join(f"- {item}" for item in files) or "- Inspect the files listed in the VibeSpec report."
    likely_change_list = file_list if source_type == "runtime" else "- Runtime source or config only after verification."
    test_list = "\n".join(f"- {item}" for item in tests) or "- Add or update a minimal regression test for this risk."
    verify_note = (
        "- This finding is suspected. Confirm the evidence before changing business logic."
        if confidence == "suspected"
        else "- This finding requires manual review before changing business logic."
        if confidence == "manual_review"
        else "- This finding is treated as confirmed by the current scan evidence."
    )
    specialized = _specialized_verify_section(category, title)
    return f"""## Fix Task: {title}

### First verify
- Inspect the file(s) below.
- Confirm whether this is runtime source, docs/example, test, generated, vendor, or cache code.
- Confirm whether the risk is real or already handled by middleware, platform policy, or another file.
{verify_note}
{specialized}

### Risk
{risk}

### If confirmed
- Implement the required fix: {fix}

### If not confirmed
- Add or update a suppression with a clear reason and expiry.
- Do not modify unrelated business logic.

### Files to inspect
{file_list}

### Files likely to change
{likely_change_list}

### Do not change
- Do not modify unrelated business logic.
- Do not edit generated/vendor/build artifacts.
- Do not hardcode secrets.
- Do not rely only on frontend checks.
- Do not add offensive, bypass, or destructive behavior.

### Tests
{test_list}

### Acceptance command
- vibespec-gate scan <project> --output <output> --no-adapters
"""


def _specialized_verify_section(category: str, title: str) -> str:
    combined = f"{category} {title}".lower()
    if "desktop" in combined or "electron" in combined:
        return """
### First verify for Desktop/Electron
- Confirm whether the code runs in main, preload, renderer, test, or generated context.
- Confirm whether input is user-selected, remote/untrusted, or LLM/tool-controlled.
- Confirm whether contextIsolation, nodeIntegration, and preload API boundaries are already enforced.
"""
    if "mcp" in combined or "ipc" in combined:
        return """
### First verify for MCP/IPC
- Confirm who can send messages to this endpoint.
- Confirm whether message schema validation exists.
- Confirm whether tool names and arguments are allowlisted.
- Confirm whether command/file operations are reachable from untrusted input.
"""
    return ""
