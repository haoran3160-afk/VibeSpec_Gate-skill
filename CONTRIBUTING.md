# Contributing

Thanks for helping improve VibeSpec Gate.

## Project Direction

VibeSpec Gate is a prompt-only, Agent-native Skill by default, backed by a heavier review and validation engine for maintainers.

Contributions should preserve this boundary:

- user path stays lightweight;
- maintainer path may stay rigorous;
- generated outputs stay out of Git;
- safety claims remain conservative.

## Local Setup

```bash
python -m pip install -e .
```

Run the Lite package verifier:

```powershell
py -3 scripts\verify_lite_package.py
```

Run focused tests:

```bash
python -m pytest -q -p no:cacheprovider
```

Build and verify the installable Lite archive:

```bash
python scripts/build_lite_package_zip.py
python scripts/verify_release_metadata.py --archive dist/vibespec-gate-lite.zip
```

Run broader maintainer checks before a release candidate when the required local evidence directories are available:

```bash
python scripts/verify_release.py
```

## Pull Request Standards

Before opening a PR:

1. Keep changes scoped and reviewable.
2. Update docs when user-facing behavior changes.
3. Add tests for new review logic, package boundaries, or output contracts.
4. Do not commit `outputs/`, `test output/`, `.pytest_cache/`, secrets, or local session files.
5. State whether the change affects the prompt-only Lite package, the optional CLI overlay, or maintainer-only workflows.

## Security Review Rules

Do not add exploit payloads, credential theft guidance, persistence, destructive testing, or unauthorized scanning workflows.

Test fixtures may contain fake secret-looking strings only when they are clearly fixtures and covered by tests.

## Documentation Standards

Use clear task-oriented docs:

- tutorials and quickstarts for first-time users;
- how-to guides for operators;
- references for schemas and contracts;
- maintainer docs for release, scoring, and calibration workflows.
