# Pull Request

## Summary

Describe the user-facing or maintainer-facing change.

## Scope

- [ ] Prompt-only Lite package
- [ ] Optional Core-powered CLI overlay
- [ ] Review engine
- [ ] Tests or fixtures
- [ ] Documentation
- [ ] Maintainer tooling

## Safety Boundary

- [ ] Does not add offensive exploit guidance.
- [ ] Does not commit generated `outputs/` or `test output/` evidence.
- [ ] Does not expose real secrets.
- [ ] Keeps certification and blind-edit boundaries clear.

## Verification

Paste the relevant commands and results:

```text
py -3 scripts\verify_lite_package.py
py -3 -m pytest ...
```

