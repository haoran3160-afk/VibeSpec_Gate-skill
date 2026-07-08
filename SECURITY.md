# Security Policy

## Supported Scope

VibeSec Gate is a defensive security review Skill and review engine for projects you own or are authorized to assess.

It is not a professional security certification, penetration test, legal review, or compliance attestation.

## Reporting A Vulnerability

Please do not open a public issue containing secrets, exploit details, private project data, or sensitive reproduction steps.

Preferred report contents:

- affected file, command, or Skill behavior;
- expected safe behavior;
- observed unsafe behavior;
- whether the issue affects prompt-only Skill usage, CLI usage, or maintainer tooling;
- sanitized evidence with secrets masked.

If GitHub private vulnerability reporting is enabled for the repository, use it. Otherwise, open a minimal public issue that says a private security report is needed, without including sensitive details.

## Safe Disclosure Boundary

Reports should avoid:

- complete secrets or tokens;
- exploit payloads against live targets;
- login bypass instructions;
- brute force guidance;
- persistence or destructive testing instructions;
- unauthorized third-party scans.

## Maintainer Response

Maintainers should triage security reports by launch impact:

- `BLOCK`: behavior can cause secret exposure, broken auth, unsafe Agent/tool authority, or user-data exposure.
- `REVIEW`: behavior needs human confirmation or additional evidence.
- `PASS_WITH_WARNINGS`: no blocker found, but hardening or documentation is needed.
- `PASS`: no material security issue found in the reviewed evidence.

