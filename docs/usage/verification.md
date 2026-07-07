# Verification

Canonical project root:

```powershell
cd D:\personal\Vibespec_gate_skill
```

Use `py -3` on Windows when available. Avoid the Microsoft Store `python.exe` launcher if it points at `C:\Users\lenovo\AppData\Local\Microsoft\WindowsApps\python.exe`.

Set these variables for local verification commands that import the local source tree directly:

```powershell
$env:PYTHONPATH = "src"
$env:PYTHONDONTWRITEBYTECODE = "1"
```

`PYTHONPATH=src` runs the local source tree without installing the package. `PYTHONDONTWRITEBYTECODE=1` avoids creating new `__pycache__` files during verification.

## Smoke Verification

This check uses only the Python standard library and does not require pytest:

```powershell
py -3 scripts\verify_phase4_5_smoke.py
```

The smoke script inserts the local `src` directory into `sys.path`, so it can run even when `PYTHONPATH` is not already set. It verifies CLI import, `vibesec review --help`, one review evaluation fixture, existing Phase 4 review JSON and markdown outputs, schema shape, snippet limits, agent decision coverage, and provider-secret redaction through the official review schema validator.

If `py -3` is unavailable, use the Codex bundled Python runtime if present:

```powershell
& "C:\Users\lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\verify_phase4_5_smoke.py
```

## Pytest Verification

When pytest is available:

```powershell
py -3 -m pytest -q -p no:cacheprovider
py -3 -m pytest tests\test_evaluation_cases.py -q -p no:cacheprovider
```

Do not install dependencies or run fix commands inside real scanned projects. Real-project review and scan outputs must be written only under this project root, for example `D:\personal\Vibespec_gate_skill\test output`.

## Review Schema Validation

Validate a Phase 4 review output directory:

```powershell
py -3 -m vibesec.cli review-validate "D:\personal\Vibespec_gate_skill\test output\phase4_review\personal-voice-light-agent"
```

The validator checks JSON structure, enum values, packet/verdict matching, snippet length, secret redaction, `reviewer=rule-based`, `safe_to_auto_suppress=false`, and that `agent_review_decisions.md` covers every reviewed finding.
